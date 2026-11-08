"""도구 기반 단일 에이전트 인시던트 조사 서비스 모듈."""

from __future__ import annotations

import hashlib
import json
import logging
import time
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any

from langfuse import get_client
from langfuse.model import ChatPromptClient
from pydantic import JsonValue, TypeAdapter, ValidationError

from hmda_reliability.reliability_ai.context import (
    ReviewContextTooLargeError,
    project_remote_output,
)
from hmda_reliability.reliability_ai.contracts import AgenticReviewInput
from hmda_reliability.reliability_ai.investigation.contracts import (
    InvestigationResult,
    InvestigationTurnRecord,
    ToolCallRecord,
)
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
from hmda_reliability.runtime_ai.contracts import ChatMessage, ProviderResponse
from hmda_reliability.runtime_ai.provider import (
    OpenAICompatibleAdapter,
    ProviderResponseTooLargeError,
    ProviderUnavailableError,
)
from hmda_reliability.runtime_ai.settings import RuntimeAISettings


def investigate_incident(
    review_input: AgenticReviewInput,
    *,
    settings: RuntimeAISettings,
    ai_settings: ReliabilityAISettings | None = None,
    provider: OpenAICompatibleAdapter | None = None,
    tool_registry: ToolRegistry | None = None,
    allowed_tools: tuple[str, ...] | None = None,
    dbt_artifact_paths: tuple[Path, Path] | None = None,
    observe_io: bool = False,
    artifact_root: Path = Path(".local/artifacts"),
    clock: Callable[[], float] = time.monotonic,
) -> InvestigationResult:
    """도구 호출을 동적으로 수행하며 인시던트의 원인, 증거, 불확실성을 조사한다."""
    active_ai_settings = ai_settings or ReliabilityAISettings()
    adapter = provider or OpenAICompatibleAdapter(settings, clock=clock)
    registry = tool_registry or ToolRegistry.from_review_input(
        review_input,
        allowed_tools=allowed_tools,
        dbt_artifact_paths=dbt_artifact_paths,
    )
    tools = tuple(
        definition
        for definition in registry.definitions
        if allowed_tools is None or definition.function.name in allowed_tools
    )
    tool_names = {definition.function.name for definition in tools}

    started_at = clock()
    deadline = started_at + active_ai_settings.workflow_budget_seconds
    incident = review_input.incident

    canonical_input: dict[str, object] = {}

    history: list[ChatMessage] = []
    compiled_message_digests: list[str] = []
    compiled_messages: list[list[dict[str, Any]]] = []
    native_prompt: ChatPromptClient | None = None
    observation_errors: list[str] = []
    root_observation: Any = None
    generation: Any = None

    all_tool_records: list[ToolCallRecord] = []
    executed_call_fingerprints: set[str] = set()
    turns: list[InvestigationTurnRecord] = []

    invocation_id = f"inv-{uuid.uuid4().hex}"
    store = InvocationResponseStore(artifact_root)
    response_paths: list[Path] = []
    max_turns = active_ai_settings.max_tool_calls + 2

    def finish(
        status: str,
        failure_code: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> InvestigationResult:
        if status == "completed" and clock() >= deadline:
            return finish("budget_exhausted", "workflow_budget_exhausted")
        common = {
            "incident_id": incident.incident_id,
            "invocation_id": invocation_id,
            "tool_calls": tuple(all_tool_records),
            "response_paths": tuple(response_paths),
            "turns": tuple(turns),
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
            for record in all_tool_records:
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
        if result.status == "completed" and clock() >= deadline:
            return finish("budget_exhausted", "workflow_budget_exhausted")
        manifest_path = (
            artifact_root
            / "reliability-ai"
            / "investigations"
            / f"{invocation_id}.json"
        )
        result = result.model_copy(update={"manifest_path": manifest_path})
        observation_record_path = manifest_path.with_name(
            f"{invocation_id}-observations.json"
        )
        _end_observation(generation, observation_errors)
        try:
            write_review_json(
                manifest_path,
                {
                    "project_revision": review_input.project_revision,
                    "input_digest": "sha256:"
                    + hashlib.sha256(canonical_json_bytes(canonical_input)).hexdigest(),
                    "canonical_input": canonical_input,
                    "evidence_refs": list(incident.evidence_refs),
                    "runtime_configuration": settings.sanitized_configuration(),
                    "ai_configuration": active_ai_settings.sanitized_configuration(),
                    "allowed_tools": sorted(tool_names),
                    "dbt_artifact_paths": (
                        [str(path.resolve()) for path in dbt_artifact_paths]
                        if dbt_artifact_paths is not None
                        else None
                    ),
                    "prompt": (
                        {"name": native_prompt.name, "version": native_prompt.version}
                        if native_prompt is not None
                        else None
                    ),
                    "compiled_message_digests": compiled_message_digests,
                    "compiled_messages": compiled_messages,
                    "observation_errors": observation_errors,
                    "observation_record_path": str(observation_record_path),
                    "trace_id": (
                        root_observation.trace_id
                        if root_observation is not None
                        else None
                    ),
                    "result": result.model_dump(mode="json"),
                },
                max_record_bytes=active_ai_settings.max_prompt_bytes * (max_turns + 1)
                + settings.max_output_bytes * (max_turns + 1) * 4
                + 65_536,
                deadline=deadline if result.status == "completed" else None,
                clock=clock,
            )
        except InvocationEvidenceDeadlineError:
            return finish("budget_exhausted", "workflow_budget_exhausted")
        except (InvocationEvidenceStoreError, ValueError, TypeError, RecursionError):
            result = result.model_copy(
                update={
                    "status": "error",
                    "failure_code": "manifest_persistence_failed",
                    "manifest_path": None,
                }
            )
        _update_observation(
            root_observation,
            observation_errors,
            **(
                {"output": project_remote_output(result.model_dump(mode="json"))}
                if observe_io
                else {}
            ),
            metadata={"status": result.status, "failure_code": result.failure_code},
        )
        _end_observation(root_observation, observation_errors)
        try:
            write_review_json(
                observation_record_path,
                {"invocation_id": invocation_id, "errors": observation_errors},
                max_record_bytes=65_536,
            )
        except InvocationEvidenceStoreError:
            logging.getLogger(__name__).warning(
                "investigation observation record unavailable",
                extra={"invocation_id": invocation_id},
            )
        return result

    try:
        canonical_input = build_canonical_input(review_input)
    except ReviewContextTooLargeError:
        return finish("error", "context_too_large")
    except ValidationError:
        return finish("error", "invalid_review_context")
    initial_user_message = canonical_json_bytes(canonical_input).decode("utf-8")

    try:
        client = get_client()
        loaded = client.get_prompt(
            active_ai_settings.prompt_name,
            type="chat",
            version=active_ai_settings.prompt_version,
            label=(
                active_ai_settings.prompt_label
                if active_ai_settings.prompt_version is None
                else None
            ),
            max_retries=0,
            fetch_timeout_seconds=5,
        )
        if not isinstance(loaded, ChatPromptClient) or loaded.is_fallback:
            return finish("error", "prompt_unavailable")
        native_prompt = loaded
    except Exception:
        return finish("error", "prompt_unavailable")

    root_observation = _start_observation(
        client,
        observation_errors,
        name="investigate-incident",
        as_type="agent",
        **({"input": canonical_input} if observe_io else {}),
        metadata={
            "invocation_id": invocation_id,
            "project_revision": review_input.project_revision,
            "prompt_name": native_prompt.name,
            "prompt_version": native_prompt.version,
        },
    )
    for turn in range(max_turns):
        remaining_budget = max(0.0, deadline - clock())
        if remaining_budget <= 0:
            return finish("budget_exhausted", "workflow_budget_exhausted")

        try:
            messages = tuple(
                ChatMessage.model_validate(message)
                for message in native_prompt.compile(
                    canonical_input=initial_user_message,
                    history=[message.model_dump(mode="json") for message in history],
                )
            )
            message_bytes = canonical_json_bytes(
                [message.model_dump(mode="json") for message in messages]
            )
        except (ValueError, TypeError, RecursionError):
            return finish("error", "prompt_unavailable")
        compiled_message_digests.append(
            "sha256:" + hashlib.sha256(message_bytes).hexdigest()
        )
        compiled_messages.append(
            [message.model_dump(mode="json") for message in messages]
        )
        if len(message_bytes) > active_ai_settings.max_prompt_bytes:
            return finish("error", "prompt_too_large")

        available_tools = (
            tools if len(all_tool_records) < active_ai_settings.max_tool_calls else ()
        )
        turn_start = clock()
        remaining_budget = max(0.0, deadline - turn_start)
        if remaining_budget <= 0:
            return finish("budget_exhausted", "workflow_budget_exhausted")
        generation = _start_observation(
            root_observation,
            observation_errors,
            name="investigate-model",
            as_type="generation",
            model=settings.model,
            prompt=native_prompt,
            **(
                {
                    "input": project_remote_output({"messages": compiled_messages[-1]})[
                        "messages"
                    ]
                }
                if observe_io
                else {}
            ),
            metadata={"turn": turn, "message_digest": compiled_message_digests[-1]},
            model_parameters={
                "temperature": settings.temperature,
                "max_tokens": settings.max_output_tokens,
            },
        )
        try:
            response: ProviderResponse = adapter.invoke(
                tuple(messages),
                output_format="text",
                budget_seconds=remaining_budget,
                tools=available_tools or None,
                tool_choice="auto" if available_tools else "none",
            )
        except ProviderUnavailableError as exc:
            turns.append(
                InvestigationTurnRecord(
                    turn=turn,
                    role="assistant",
                    attempt_count=exc.attempt_count,
                    latency_ms=exc.latency_ms,
                    failure_code=exc.failure_code,
                )
            )
            _update_observation(
                generation,
                observation_errors,
                level="ERROR",
                status_message=exc.failure_code,
                metadata={
                    "attempt_count": exc.attempt_count,
                    "latency_ms": exc.latency_ms,
                },
            )
            return finish("error", exc.failure_code)
        except ProviderResponseTooLargeError as exc:
            turns.append(
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
            return finish("error", "provider_response_too_large")

        response_failure = (
            "invalid_provider_tool_calls"
            if response.raw_tool_calls is not None
            or (
                response.response_metadata is not None
                and response.response_metadata.content_state == "invalid_tool_calls"
            )
            else None
        )
        turn_latency = max(0.0, (clock() - turn_start) * 1000)
        turns.append(
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
            response_paths.append(
                store.write(
                    f"{invocation_id}-{turn}",
                    response.content,
                    max_response_bytes=settings.max_output_bytes,
                )
            )
        except InvocationEvidenceStoreError:
            return finish("error", "response_persistence_failed")

        _update_observation(
            generation,
            observation_errors,
            **(
                {"level": "ERROR", "status_message": response_failure}
                if response_failure is not None
                else {}
            ),
            **(
                {
                    "output": project_remote_output(
                        {
                            "role": "assistant",
                            "content": response.content,
                            "tool_calls": [
                                call.model_dump(mode="json")
                                for call in response.tool_calls
                            ],
                        }
                    )
                }
                if observe_io
                else {}
            ),
            usage_details=(
                {
                    key: value
                    for key, value in {
                        "input": response.usage.prompt_tokens,
                        "output": response.usage.completion_tokens,
                        "total": response.usage.total_tokens,
                    }.items()
                    if value is not None
                }
                if response.usage is not None
                else None
            ),
            metadata={
                "turn": turn,
                "attempt_count": response.attempt_count,
                "latency_ms": response.latency_ms,
            },
        )
        _end_observation(generation, observation_errors)
        generation = None
        if clock() >= deadline:
            return finish("budget_exhausted", "workflow_budget_exhausted")
        if response_failure is not None:
            return finish("error", response_failure)
        if response.response_metadata is not None and (
            response.response_metadata.finish_reason in {"length", "content_filter"}
        ):
            return finish("error", "incomplete_provider_response")

        if response.tool_calls:
            assistant_msg = ChatMessage(
                role="assistant",
                content=response.content,
                tool_calls=response.tool_calls,
            )
            history.append(assistant_msg)
            for call in response.tool_calls:
                if len(all_tool_records) >= active_ai_settings.max_tool_calls:
                    return finish("budget_exhausted", "tool_call_budget_exhausted")
                if clock() >= deadline:
                    return finish("budget_exhausted", "workflow_budget_exhausted")
                if call.function.name not in tool_names:
                    return finish("error", "tool_not_allowed")
                try:
                    arguments = json.loads(call.function.arguments or "{}")
                    fingerprint = (
                        f"{call.function.name}:"
                        f"{canonical_json_bytes(arguments).decode('utf-8')}"
                    )
                except RecursionError:
                    return finish("error", "invalid_investigation_output")
                except ValueError:
                    arguments = call.function.arguments
                    fingerprint = (
                        f"{call.function.name}:{call.function.arguments.strip()}"
                    )
                if fingerprint in executed_call_fingerprints:
                    return finish("tool_cycle_detected", "duplicate_tool_call_cycle")
                executed_call_fingerprints.add(fingerprint)

                if clock() >= deadline:
                    return finish("budget_exhausted", "workflow_budget_exhausted")
                tool_observation = _start_observation(
                    root_observation,
                    observation_errors,
                    name=call.function.name,
                    as_type="tool",
                    **(
                        {"input": project_remote_output({"arguments": arguments})}
                        if observe_io
                        else {}
                    ),
                    metadata={"call_id": call.id, "turn": turn},
                )
                record, tool_output = registry.execute(call)
                _update_observation(
                    tool_observation,
                    observation_errors,
                    **(
                        {"output": project_remote_output(record.result)}
                        if observe_io
                        else {}
                    ),
                    metadata={"status": record.status, "latency_ms": record.latency_ms},
                )
                _end_observation(tool_observation, observation_errors)
                all_tool_records.append(record)
                turns.append(
                    InvestigationTurnRecord(
                        turn=turn,
                        role="tool",
                        tool_call_id=call.id,
                        content=tool_output,
                        latency_ms=record.latency_ms,
                    )
                )
                history.append(
                    ChatMessage(
                        role="tool",
                        tool_call_id=call.id,
                        content=tool_output,
                    )
                )

            if len(all_tool_records) >= active_ai_settings.max_tool_calls:
                history.append(
                    ChatMessage(
                        role="user",
                        content=(
                            "도구 호출 한도에 도달했습니다. "
                            "현재까지 확인된 정보로 최종 JSON 보고서를 작성하세요."
                        ),
                    )
                )

            continue

        try:
            parsed_data = _parse_investigation_payload(response.content)
            TypeAdapter(dict[str, JsonValue]).validate_python(parsed_data)
        except (ValueError, RecursionError):
            return finish("error", "invalid_investigation_output")
        return finish(
            "completed",
            payload={
                "facts": {
                    "target_column": review_input.target_column,
                    **review_input.deterministic_facts.model_dump(mode="json"),
                },
                **{
                    field: parsed_data[field]
                    for field in ("findings", "hypotheses", "uncertainties")
                },
            },
        )

    return finish("budget_exhausted", "max_turns_exceeded")


def _start_observation(owner: Any, errors: list[str], **kwargs: Any) -> Any:
    if owner is None:
        return None
    try:
        return owner.start_observation(**kwargs)
    except Exception:
        errors.append("observation_start_failed")
        return None


def _update_observation(observation: Any, errors: list[str], **kwargs: Any) -> None:
    if observation is None:
        return
    try:
        observation.update(**kwargs)
    except Exception:
        errors.append("observation_update_failed")


def _end_observation(observation: Any, errors: list[str]) -> None:
    if observation is None:
        return
    try:
        observation.end()
    except Exception:
        errors.append("observation_end_failed")


def _parse_investigation_payload(content: str) -> dict[str, Any]:
    """최종 JSON 객체를 파싱하고 비정형 응답은 거부한다."""
    text = content.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("investigation output must be a JSON object")
    if any(
        not isinstance(data.get(field), list)
        for field in ("findings", "hypotheses", "uncertainties")
    ):
        raise ValueError("investigation output requires all three report arrays")
    return data
