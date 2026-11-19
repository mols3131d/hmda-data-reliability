"""도구 기반 단일 에이전트 인시던트 조사 서비스 모듈."""

from __future__ import annotations

import hashlib
import json
import logging
import time
import uuid
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from langchain_core.messages import (
    HumanMessage,
    ToolMessage,
    convert_to_openai_messages,
)
from langfuse import get_client
from langfuse.model import ChatPromptClient
from pydantic import JsonValue, TypeAdapter, ValidationError

from hmda_reliability.reliability_ai.context import (
    ReviewContextTooLargeError,
    json_message_body,
)
from hmda_reliability.reliability_ai.contracts import AgenticReviewInput
from hmda_reliability.reliability_ai.investigation.contracts import (
    InvestigationResult,
    InvestigationTurnRecord,
    ToolCallRecord,
)
from hmda_reliability.reliability_ai.investigation.graph import (
    GraphStop,
    run_investigation_graph,
)
from hmda_reliability.reliability_ai.investigation.observations import (
    InvestigationTrace,
)
from hmda_reliability.reliability_ai.investigation.records import InvestigationJournal
from hmda_reliability.reliability_ai.investigation.tools import ToolRegistry
from hmda_reliability.reliability_ai.prompt import (
    build_canonical_input,
    canonical_json_bytes,
)
from hmda_reliability.reliability_ai.settings import ReliabilityAISettings
from hmda_reliability.reliability_ai.store import (
    InvocationEvidenceDeadlineError,
    InvocationEvidenceStoreError,
    InvocationResponseStore,
    write_review_json,
)
from hmda_reliability.runtime_ai.codex import (
    CodexAdapter,
    CodexSettings,
    decode_codex_response,
)
from hmda_reliability.runtime_ai.contracts import (
    ChatMessage,
    ProviderResponse,
    ToolCall,
    ToolDefinition,
)
from hmda_reliability.runtime_ai.provider import (
    ProviderResponseTooLargeError,
    ProviderUnavailableError,
)
from hmda_reliability.runtime_ai.selection import (
    InvestigationProvider,
    resolve_investigation_provider,
)
from hmda_reliability.runtime_ai.settings import RuntimeAISettings


class InvestigationTools(Protocol):
    @property
    def definitions(self) -> tuple[ToolDefinition, ...]: ...

    def execute(self, tool_call: ToolCall) -> tuple[ToolCallRecord, str]: ...


@dataclass(frozen=True)
class ReplayIncidentInput:
    canonical_input: dict[str, Any]
    incident_id: str
    project_revision: str
    evidence_refs: tuple[str, ...]
    prompt_name: str | None
    prompt_version: int | None
    compiled_messages: Sequence[Sequence[dict[str, Any]]]
    final_write_failure: bool = False
    preflight_failure: str | None = None
    write_failure: str | None = None
    failed_turn: int | None = None
    failed_tool_id: str | None = None
    final_write_expired: bool = False
    publication_clock_reads: int = 0
    codex_wire_input: bool = False


def investigate_incident(
    review_input: AgenticReviewInput,
    *,
    settings: RuntimeAISettings | CodexSettings | None = None,
    ai_settings: ReliabilityAISettings | None = None,
    provider: InvestigationProvider | None = None,
    tool_registry: InvestigationTools | None = None,
    allowed_tools: tuple[str, ...] | None = None,
    dbt_artifact_paths: tuple[Path, Path] | None = None,
    observe_io: bool = False,
    artifact_root: Path = Path(".local/artifacts"),
    clock: Callable[[], float] = time.monotonic,
) -> InvestigationResult:
    """도구 호출을 동적으로 수행하며 인시던트의 원인, 증거, 불확실성을 조사한다."""
    return _IncidentRun(
        review_input,
        settings=settings,
        ai_settings=ai_settings,
        provider=provider,
        tool_registry=tool_registry,
        allowed_tools=allowed_tools,
        dbt_artifact_paths=dbt_artifact_paths,
        observe_io=observe_io,
        artifact_root=artifact_root,
        clock=clock,
    ).run()


class _IncidentRun:
    """사고 조사 노드의 입력과 근거 참조를 관리한다."""

    def __init__(
        self,
        review_input: AgenticReviewInput | None,
        *,
        settings: RuntimeAISettings | CodexSettings | None = None,
        ai_settings: ReliabilityAISettings | None = None,
        provider: InvestigationProvider | None = None,
        tool_registry: InvestigationTools | None = None,
        allowed_tools: tuple[str, ...] | None = None,
        dbt_artifact_paths: tuple[Path, Path] | None = None,
        observe_io: bool = False,
        artifact_root: Path = Path(".local/artifacts"),
        clock: Callable[[], float] = time.monotonic,
        replay: ReplayIncidentInput | None = None,
    ) -> None:
        self.review_input = review_input
        self.dbt_artifact_paths = dbt_artifact_paths
        self.observe_io = observe_io
        self.artifact_root = artifact_root
        self.clock = clock
        self.replay = replay
        self.limits = ai_settings or ReliabilityAISettings()
        self.settings, self.adapter = resolve_investigation_provider(
            settings, provider, clock=self.clock
        )
        self.invocation_id = f"inv-{uuid.uuid4().hex}"
        self.journal = InvestigationJournal(self.artifact_root, self.invocation_id)
        self.clock = self.journal.clock(self.clock)
        self.deadline = self.clock() + self.limits.workflow_budget_seconds
        if self.replay is None:
            assert self.review_input is not None
            self.incident_id = self.review_input.incident.incident_id
            self.project_revision = self.review_input.project_revision
            self.evidence_refs = tuple(self.review_input.incident.evidence_refs)
        else:
            self.incident_id, self.project_revision, self.evidence_refs = (
                self.replay.incident_id,
                self.replay.project_revision,
                self.replay.evidence_refs,
            )
        if tool_registry is None:
            assert self.review_input is not None
            tool_registry = ToolRegistry.from_review_input(
                self.review_input,
                allowed_tools=allowed_tools,
                dbt_artifact_paths=self.dbt_artifact_paths,
            )
        self.registry = tool_registry
        self.tools = tuple(
            definition
            for definition in self.registry.definitions
            if allowed_tools is None or definition.function.name in allowed_tools
        )
        self.tool_names = {definition.function.name for definition in self.tools}

        self.canonical_input: dict[str, object] = {}

        self.history: list[dict[str, Any]] = []
        self.compiled_message_digests: list[str] = []
        self.compiled_messages: list[list[dict[str, Any]]] = []
        self.native_prompt: ChatPromptClient | None = None
        self.trace = InvestigationTrace(self.invocation_id, observe_io=self.observe_io)
        self.generation: Any = None

        self.all_tool_records: list[ToolCallRecord] = []
        self.executed_call_fingerprints: set[str] = set()
        self.turns: list[InvestigationTurnRecord] = []

        self.store = InvocationResponseStore(self.artifact_root)
        self.response_paths: list[Path] = []
        self.max_turns = self.limits.max_tool_calls + 2

        self.input_digests: list[str] = []
        self.input_sizes: list[int] = []
        self.preflight_failure: str | None = None
        self.initial_user_message = ""
        self.turn_start = 0.0

    def publish(self, path: Path, data: dict[str, Any], **kwargs: Any) -> Path:
        if self.replay and self.replay.final_write_failure:
            raise InvocationEvidenceStoreError("recorded publication failure")
        if (
            self.replay
            and self.replay.final_write_expired
            and kwargs["deadline"] is not None
        ):
            for _ in range(self.replay.publication_clock_reads):
                kwargs["clock"]()
            raise InvocationEvidenceDeadlineError("recorded publication deadline")
        if self.replay:
            kwargs["deadline"] = None
        return write_review_json(path, data, **kwargs)

    def finish(
        self,
        status: str,
        failure_code: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> InvestigationResult:
        if status == "completed" and self.clock() >= self.deadline:
            return self.finish("budget_exhausted", "workflow_budget_exhausted")
        common = {
            "incident_id": self.incident_id,
            "invocation_id": self.invocation_id,
            "tool_calls": tuple(self.all_tool_records),
            "response_paths": tuple(self.response_paths),
            "turns": tuple(self.turns),
        }
        try:
            result = InvestigationResult.model_validate(
                {
                    **common,
                    "status": status,
                    "failure_code": failure_code,
                    **(payload or {}),
                }
            )
        except ValidationError:
            result = InvestigationResult.model_validate(
                {
                    **common,
                    "status": "error",
                    "failure_code": "invalid_investigation_output",
                }
            )
        try:
            result.model_dump(mode="json")
        except (ValueError, RecursionError):
            safe_records: list[ToolCallRecord] = []
            for record in self.all_tool_records:
                try:
                    record.model_dump(mode="json")
                except (ValueError, RecursionError):
                    record = record.model_copy(
                        update={
                            "arguments": {},
                            "result": {
                                "error": "unserializable_tool_record",
                                "raw_evidence": "investigation turns",
                            },
                            "status": "error",
                        }
                    )
                safe_records.append(record)
            result = InvestigationResult.model_validate(
                {
                    **common,
                    "tool_calls": tuple(safe_records),
                    "status": "error",
                    "failure_code": "invalid_investigation_output",
                }
            )
            result.model_dump(mode="json")
        if result.status == "completed" and self.clock() >= self.deadline:
            return self.finish("budget_exhausted", "workflow_budget_exhausted")
        manifest_path = (
            self.artifact_root
            / "reliability-ai"
            / "investigations"
            / f"{self.invocation_id}.json"
        )
        result = result.model_copy(update={"manifest_path": manifest_path})
        observation_record_path = manifest_path.with_name(
            f"{self.invocation_id}-observations.json"
        )
        max_record_bytes = (
            self.limits.max_prompt_bytes * (self.max_turns + 1)
            + self.settings.max_output_bytes * (self.max_turns + 1) * 4
            + 65_536
        )
        self.trace.end(self.generation)
        try:
            result_payload = result.model_dump(mode="json")
            result = self.journal.publish(
                manifest_path,
                {
                    "project_revision": self.project_revision,
                    "input_digest": "sha256:"
                    + hashlib.sha256(
                        canonical_json_bytes(self.canonical_input)
                    ).hexdigest(),
                    "canonical_input": self.canonical_input,
                    "evidence_refs": list(self.evidence_refs),
                    "runtime_configuration": self.settings.sanitized_configuration(),
                    "ai_configuration": self.limits.sanitized_configuration(),
                    "allowed_tools": sorted(self.tool_names),
                    "dbt_artifact_paths": (
                        [str(path.resolve()) for path in self.dbt_artifact_paths]
                        if self.dbt_artifact_paths is not None
                        else None
                    ),
                    "preflight_failure": self.preflight_failure,
                    "tool_definitions": [
                        definition.model_dump(mode="json") for definition in self.tools
                    ],
                    "codex_wire_input": isinstance(self.adapter, CodexAdapter)
                    or bool(self.replay and self.replay.codex_wire_input),
                    "input_digests": self.input_digests,
                    "input_bytes": self.input_sizes,
                    "prompt": (
                        {
                            "name": self.native_prompt.name,
                            "version": self.native_prompt.version,
                        }
                        if self.native_prompt is not None
                        else (
                            {
                                "name": self.replay.prompt_name,
                                "version": self.replay.prompt_version,
                            }
                            if self.replay and self.replay.prompt_name is not None
                            else None
                        )
                    ),
                    "compiled_message_digests": self.compiled_message_digests,
                    "compiled_messages": self.compiled_messages,
                    "observation_errors": self.trace.errors,
                    "observation_record_path": str(observation_record_path),
                    "trace_id": self.trace.trace_id,
                    "observation_ids": self.trace.observations,
                    "result": result_payload,
                },
                max_record_bytes=max_record_bytes,
                deadline=self.deadline if result.status == "completed" else None,
                clock=self.clock,
                writer=self.publish,
            )
        except InvocationEvidenceDeadlineError:
            return self.finish("budget_exhausted", "workflow_budget_exhausted")
        except (
            InvocationEvidenceStoreError,
            OSError,
            ValueError,
            TypeError,
            RecursionError,
        ):
            result = result.model_copy(
                update={
                    "status": "error",
                    "failure_code": "manifest_persistence_failed",
                    "manifest_path": None,
                    "facts": {},
                    "findings": (),
                    "hypotheses": (),
                    "uncertainties": (),
                }
            )
        else:
            if self.replay is None:
                try:
                    write_review_json(
                        self.journal.root / "results" / manifest_path.name,
                        {
                            field: result_payload[field]
                            for field in (
                                "incident_id",
                                "invocation_id",
                                "status",
                                "failure_code",
                                "facts",
                                "findings",
                                "hypotheses",
                                "uncertainties",
                            )
                        },
                        max_record_bytes=max_record_bytes,
                        indent=2,
                    )
                except InvocationEvidenceStoreError:
                    logging.getLogger(__name__).warning(
                        "investigation result JSON unavailable",
                        extra={"invocation_id": self.invocation_id},
                    )
        remote_result: dict[str, Any] = {}
        if self.observe_io:
            remote_result = result.model_dump(mode="json")
            retained_tools = {t.tool_call_id for t in self.turns if t.role == "tool"}
            remote_result["tool_calls"] = [
                r for r in remote_result["tool_calls"] if r["call_id"] in retained_tools
            ]
            remote_result["turns"] = [
                turn
                for turn in remote_result["turns"]
                if (
                    (turn["role"] == "tool" and turn["tool_call_id"] in retained_tools)
                    or (
                        turn["role"] == "assistant"
                        and turn["turn"] < len(self.response_paths)
                        and (
                            turn["tool_calls_path"] is not None
                            or (
                                not turn["tool_calls"]
                                and turn["raw_tool_calls"] is None
                            )
                        )
                    )
                )
            ]
        self.trace.update(
            self.trace.root,
            output=remote_result,
            metadata={"status": result.status, "failure_code": result.failure_code},
        )
        self.trace.end(self.trace.root)
        try:
            write_review_json(
                observation_record_path,
                {
                    "invocation_id": self.invocation_id,
                    "errors": self.trace.errors,
                },
                max_record_bytes=65_536,
            )
        except InvocationEvidenceStoreError:
            logging.getLogger(__name__).warning(
                "investigation observation record unavailable",
                extra={"invocation_id": self.invocation_id},
            )
        return result

    def assess(self, turn: int) -> GraphStop | None:
        if turn:
            return None
        if self.replay is not None:
            self.canonical_input = self.replay.canonical_input
            if self.replay.preflight_failure and not self.replay.compiled_messages:
                self.preflight_failure = self.replay.preflight_failure
                return GraphStop("error", self.preflight_failure)
            return None
        assert self.review_input is not None
        try:
            self.canonical_input = build_canonical_input(self.review_input)
        except ReviewContextTooLargeError:
            self.preflight_failure = "context_too_large"
            return GraphStop("error", self.preflight_failure)
        except ValidationError:
            self.preflight_failure = "invalid_review_context"
            return GraphStop("error", self.preflight_failure)
        self.initial_user_message = canonical_json_bytes(self.canonical_input).decode(
            "utf-8"
        )

        try:
            client = get_client()
            loaded = client.get_prompt(
                self.limits.prompt_name,
                type="chat",
                version=self.limits.prompt_version,
                label=(
                    self.limits.prompt_label
                    if self.limits.prompt_version is None
                    else None
                ),
                max_retries=0,
                fetch_timeout_seconds=5,
            )
            if not isinstance(loaded, ChatPromptClient) or loaded.is_fallback:
                raise ValueError("native prompt unavailable")
            self.native_prompt = loaded
        except Exception:
            self.preflight_failure = "prompt_unavailable"
            return GraphStop("error", self.preflight_failure)

        self.trace.start(
            client,
            "investigate-incident",
            "agent",
            inputs=self.canonical_input,
            metadata={
                "invocation_id": self.invocation_id,
                "project_revision": self.project_revision,
                "prompt_name": self.native_prompt.name,
                "prompt_version": self.native_prompt.version,
            },
        )
        return None

    def model(self, turn: int) -> ProviderResponse | GraphStop:
        remaining_budget = max(0.0, self.deadline - self.clock())
        if remaining_budget <= 0:
            return GraphStop("budget_exhausted", "workflow_budget_exhausted")

        try:
            rendered: Sequence[object]
            if self.replay is not None:
                if turn >= len(self.replay.compiled_messages):
                    raise ValueError("recorded prompt unavailable")
                rendered = self.replay.compiled_messages[turn]
            else:
                assert self.native_prompt is not None
                rendered = self.native_prompt.compile(
                    canonical_input=self.initial_user_message,
                    history=self.history,
                )
            messages = tuple(
                ChatMessage.model_validate(message) for message in rendered
            )
            message_bytes = canonical_json_bytes(
                [message.model_dump(mode="json") for message in messages]
            )
        except (ValueError, TypeError, RecursionError):
            self.preflight_failure = "prompt_unavailable"
            return GraphStop("error", self.preflight_failure)
        self.compiled_message_digests.append(
            "sha256:" + hashlib.sha256(message_bytes).hexdigest()
        )
        self.compiled_messages.append(
            [message.model_dump(mode="json") for message in messages]
        )
        available_tools = (
            self.tools
            if len(self.all_tool_records) < self.limits.max_tool_calls
            else ()
        )
        if isinstance(self.adapter, CodexAdapter) or (
            self.replay and self.replay.codex_wire_input
        ):
            wire_input = CodexAdapter.input_bytes(messages, available_tools)
        elif available_tools:
            wire_input = canonical_json_bytes(
                {
                    "messages": self.compiled_messages[-1],
                    "tools": [t.model_dump(mode="json") for t in available_tools],
                }
            )
        else:
            wire_input = message_bytes
        self.input_sizes.append(len(wire_input))
        self.input_digests.append("sha256:" + hashlib.sha256(wire_input).hexdigest())
        if len(wire_input) > self.limits.max_prompt_bytes:
            return GraphStop("error", "prompt_too_large")
        self.generation = self.trace.start(
            self.trace.root,
            "investigate-model",
            "generation",
            model=self.settings.model,
            prompt=self.native_prompt,
            inputs={"messages": self.compiled_messages[-1]},
            metadata={
                "turn": turn,
                "message_digest": self.compiled_message_digests[-1],
            },
            model_parameters={
                "temperature": self.settings.temperature,
                "max_tokens": self.settings.max_output_tokens,
            },
        )
        self.turn_start = self.clock()
        remaining_budget = max(0.0, self.deadline - self.turn_start)
        if remaining_budget <= 0:
            return GraphStop("budget_exhausted", "workflow_budget_exhausted")
        try:
            kwargs: dict[str, Any] = dict(
                output_format="text",
                budget_seconds=remaining_budget,
                tools=available_tools or None,
                tool_choice="auto" if available_tools else "none",
            )
            if isinstance(self.adapter, CodexAdapter):
                return self.adapter.invoke_for_turn(
                    self.invocation_id, turn, messages, **kwargs
                )
            return self.adapter.invoke(messages, **kwargs)
        except ProviderUnavailableError as exc:
            self.turns.append(
                InvestigationTurnRecord(
                    turn=turn,
                    role="assistant",
                    attempt_count=exc.attempt_count,
                    latency_ms=exc.latency_ms,
                    failure_code=exc.failure_code,
                    response_metadata=getattr(exc, "response_metadata", None),
                )
            )
            self.trace.update(
                self.generation,
                level="ERROR",
                status_message=exc.failure_code,
                metadata={
                    "attempt_count": exc.attempt_count,
                    "latency_ms": exc.latency_ms,
                },
            )
            return GraphStop("error", exc.failure_code)
        except ProviderResponseTooLargeError as exc:
            self.turns.append(
                InvestigationTurnRecord(
                    turn=turn,
                    role="assistant",
                    attempt_count=exc.attempt_count,
                    latency_ms=exc.latency_ms,
                    usage=exc.usage,
                    response_metadata=exc.response_metadata,
                    failure_code="provider_response_too_large",
                )
            )
            return GraphStop("error", "provider_response_too_large")

    def retain(
        self, turn: int, response: ProviderResponse
    ) -> ProviderResponse | GraphStop:
        response_failure = (
            "invalid_provider_tool_calls"
            if response.raw_tool_calls is not None
            or (
                response.response_metadata is not None
                and response.response_metadata.content_state == "invalid_tool_calls"
            )
            else None
        )
        turn_latency = max(0.0, (self.clock() - self.turn_start) * 1000)
        self.turns.append(
            InvestigationTurnRecord(
                turn=turn,
                role="assistant",
                content=response.content,
                tool_calls=tuple(
                    call.model_dump(mode="json") for call in response.tool_calls
                ),
                raw_tool_calls=response.raw_tool_calls,
                latency_ms=turn_latency,
                attempt_count=response.attempt_count,
                usage=response.usage,
                response_metadata=response.response_metadata,
                failure_code=response_failure,
            )
        )
        try:
            if (
                self.replay
                and self.replay.failed_turn == turn
                and self.replay.write_failure == "response"
            ):
                raise InvocationEvidenceStoreError("recorded response failure")
            self.response_paths.append(
                self.store.write(
                    f"{self.invocation_id}-{turn}",
                    response.content,
                    max_response_bytes=self.settings.max_output_bytes,
                )
            )
            if (
                response.response_metadata
                and response.response_metadata.codex_attempt is not None
            ):
                try:
                    response = decode_codex_response(response)
                except ValueError:
                    response_failure = "invalid_investigation_output"
                self.turns[-1] = self.turns[-1].model_copy(
                    update={
                        "tool_calls": tuple(
                            call.model_dump(mode="json") for call in response.tool_calls
                        ),
                        "raw_tool_calls": response.raw_tool_calls,
                        "failure_code": response_failure,
                    }
                )
            if response.tool_calls or response.raw_tool_calls is not None:
                if (
                    self.replay
                    and self.replay.failed_turn == turn
                    and self.replay.write_failure == "calls"
                ):
                    raise InvocationEvidenceStoreError("recorded call data failure")
                tool_calls_path = write_review_json(
                    self.store.path_for(
                        f"{self.invocation_id}-{turn}-tool-calls"
                    ).with_suffix(".json"),
                    {
                        "tool_calls": list(self.turns[-1].tool_calls),
                        "raw_tool_calls": response.raw_tool_calls,
                    },
                    max_record_bytes=self.settings.max_output_bytes * 6 + 128,
                )
                self.turns[-1] = self.turns[-1].model_copy(
                    update={"tool_calls_path": tool_calls_path}
                )
        except InvocationEvidenceStoreError:
            kind = "calls" if turn < len(self.response_paths) else "response"
            self.journal.failed_write(kind, turn)
            return GraphStop("error", "response_persistence_failed")

        self.trace.retained_model(self.generation, turn, response, response_failure)
        self.generation = None
        if self.clock() >= self.deadline:
            return GraphStop("budget_exhausted", "workflow_budget_exhausted")
        if response_failure is not None:
            return GraphStop("error", response_failure)
        if response.response_metadata is not None and (
            response.response_metadata.finish_reason in {"length", "content_filter"}
        ):
            return GraphStop("error", "incomplete_provider_response")

        if response.tool_calls:
            # Preserve raw argument strings, including invalid JSON and whitespace.
            self.history.append(
                ChatMessage(
                    role="assistant",
                    content=response.content,
                    tool_calls=response.tool_calls,
                ).model_dump(mode="json")
            )
            return response
        try:
            parsed_data = _parse_investigation_payload(response.content)
            TypeAdapter(dict[str, JsonValue]).validate_python(parsed_data)
        except (ValueError, RecursionError):
            return GraphStop("error", "invalid_investigation_output")
        return GraphStop(
            "completed",
            payload={
                "facts": self.canonical_input["deterministic_facts"],
                **{
                    field: parsed_data[field]
                    for field in ("findings", "hypotheses", "uncertainties")
                },
            },
        )

    def read(self, turn: int, call: ToolCall) -> GraphStop | None:
        if self.clock() >= self.deadline:
            return GraphStop("budget_exhausted", "workflow_budget_exhausted")
        if call.function.name not in self.tool_names:
            return GraphStop("error", "tool_not_allowed")
        try:
            arguments = json.loads(call.function.arguments or "{}")
            fingerprint = (
                f"{call.function.name}:"
                f"{canonical_json_bytes(arguments).decode('utf-8')}"
            )
        except RecursionError:
            return GraphStop("error", "invalid_investigation_output")
        except ValueError:
            arguments = call.function.arguments
            fingerprint = f"{call.function.name}:{call.function.arguments.strip()}"
        if fingerprint in self.executed_call_fingerprints:
            return GraphStop("tool_cycle_detected", "duplicate_tool_call_cycle")
        self.executed_call_fingerprints.add(fingerprint)

        tool_observation = self.trace.start(
            self.trace.root,
            call.function.name,
            "tool",
            inputs={"arguments": arguments},
            metadata={"call_id": call.id, "turn": turn},
        )
        if self.clock() >= self.deadline:
            self.trace.end(tool_observation)
            return GraphStop("budget_exhausted", "workflow_budget_exhausted")
        record, tool_output = self.registry.execute(call)
        matched = record.call_id == call.id and record.tool_name == call.function.name
        if not matched:
            # A mismatched observation may belong to a different investigation.
            error = {"error": "tool_observation_mismatch"}
            record = record.model_copy(
                update={"arguments": {}, "result": error, "status": "error"}
            )
            tool_output = json.dumps(error)
        self.all_tool_records.append(record)
        try:
            if (
                self.replay
                and self.replay.failed_turn == turn
                and self.replay.write_failure == "observation"
                and self.replay.failed_tool_id == call.id
            ):
                raise InvocationEvidenceStoreError("recorded observation failure")
            self.journal.observe_tool(turn, record, tool_output)
        except (InvocationEvidenceStoreError, OSError, ValueError, RecursionError):
            self.journal.failed_write("observation", turn, call.id)
            self.trace.end(tool_observation)
            return GraphStop("error", "tool_observation_persistence_failed")
        if not matched:
            self.trace.update(
                tool_observation,
                level="ERROR",
                status_message="tool_observation_mismatch",
            )
            self.trace.end(tool_observation)
            return GraphStop("error", "tool_observation_mismatch")
        self.trace.update(
            tool_observation,
            output=record.result,
            metadata={"status": record.status, "latency_ms": record.latency_ms},
        )
        self.trace.end(tool_observation)
        self.turns.append(
            InvestigationTurnRecord(
                turn=turn,
                role="tool",
                tool_call_id=call.id,
                content=tool_output,
                latency_ms=record.latency_ms,
            )
        )
        self.history.append(
            convert_to_openai_messages(
                ToolMessage(tool_call_id=call.id, content=tool_output)
            )
        )
        if len(self.all_tool_records) == self.limits.max_tool_calls:
            self.history.append(
                convert_to_openai_messages(
                    HumanMessage(
                        content=(
                            "도구 호출 한도에 도달했습니다. "
                            "현재까지 확인된 정보로 최종 JSON 보고서를 작성하세요."
                        )
                    )
                )
            )
        return None

    def run(self) -> InvestigationResult:
        try:
            return run_investigation_graph(
                assess=self.assess,
                model=self.model,
                retain=self.retain,
                read=self.read,
                finish=lambda stop: self.finish(
                    stop.status, stop.failure_code, stop.payload
                ),
                max_turns=self.max_turns,
                max_tool_calls=self.limits.max_tool_calls,
            )
        finally:
            if isinstance(self.adapter, CodexAdapter):
                self.adapter.close()


def _parse_investigation_payload(content: str) -> dict[str, Any]:
    """최종 JSON 객체를 파싱하고 비정형 응답은 거부한다."""
    data = json.loads(json_message_body(content))
    if not isinstance(data, dict):
        raise ValueError("investigation output must be a JSON object")
    if any(
        not isinstance(data.get(field), list)
        for field in ("findings", "hypotheses", "uncertainties")
    ):
        raise ValueError("investigation output requires all three report arrays")
    return data
