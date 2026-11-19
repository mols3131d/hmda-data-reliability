"""준비·사후 조사에 같은 그래프, 제공자와 로컬 근거 경계를 사용한다."""

from __future__ import annotations

import time
from collections.abc import Callable
from pathlib import Path
from typing import Any, Literal

from langfuse import get_client
from langfuse.model import ChatPromptClient

from hmda_reliability.data_operations.request import DataOperationRequest
from hmda_reliability.reliability_ai.ingestion.airflow import (
    STAGES,
    AirflowRunReader,
    RunRef,
)
from hmda_reliability.reliability_ai.ingestion.evidence import (
    MAX_BYTES,
    IngestionJournal,
    load_record,
    validate_previous,
)
from hmda_reliability.reliability_ai.ingestion.policy import (
    advisory,
    initial_handoff,
    lookup,
    tool_definitions,
)
from hmda_reliability.reliability_ai.ingestion.source import inspect_inputs
from hmda_reliability.reliability_ai.investigation.graph import (
    GraphStop,
    run_investigation_graph,
)
from hmda_reliability.reliability_ai.investigation.observations import (
    InvestigationTrace,
)
from hmda_reliability.reliability_ai.prompt import canonical_json_bytes
from hmda_reliability.reliability_ai.settings import ReliabilityAISettings
from hmda_reliability.reliability_ai.store import (
    InvocationEvidenceStoreError,
    ReplayEvidenceError,
    evidence_digest,
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

type _Payload = dict[str, Any]


class _Events:
    """재현 중에는 저장된 경계 값만 순서대로 소비한다."""

    def __init__(
        self, journal: IngestionJournal, replay: list[_Payload] | None
    ) -> None:
        self.journal = journal
        self.replay = replay
        self.index = 0

    def boundary(self, kind: str, get: Callable[[], _Payload]) -> _Payload:
        if self.replay is None:
            data = get()
        else:
            if self.index >= len(self.replay):
                raise ReplayEvidenceError("missing_evidence")
            record = self.replay[self.index]
            if record["kind"] != kind or not isinstance(record["data"], dict):
                raise ReplayEvidenceError("corrupt_evidence")
            data = record["data"]
            self.index += 1
        self.journal.add(kind, data)
        return data


def _run(
    journal: IngestionJournal,
    start: _Payload,
    initial: _Payload,
    events: _Events,
    *,
    clock: Callable[[], float],
    origin: float,
    client: Any,
    adapter: InvestigationProvider | None,
    synthetic: bool,
) -> tuple[dict[str, Any], InvestigationTrace]:
    mode = start["mode"]
    limits = ReliabilityAISettings.model_validate(start["limits"])
    budget = limits.workflow_budget_seconds
    trace = InvestigationTrace(journal.id, observe_io=synthetic)
    generation = None
    base: list[ChatMessage] = []
    history: list[ChatMessage] = []
    seen: set[str] = set()
    tool_ids: list[str] = []
    advice: _Payload | None = None
    status, action = initial_handoff(mode, initial)
    tools = tool_definitions(mode, initial)
    prompt_meta: _Payload = {}
    # Model-facing identifiers omit local paths and filenames.
    summary = {
        "mode": mode,
        "evidence_id": "initial",
        "status": status,
        "reason": initial.get("reason"),
        "source_ids": [s["source_id"] for s in initial.get("sources", [])],
        "stages": [
            {"stage": s["stage"], "state": s["state"]}
            for s in initial.get("stages", [])
        ],
    }

    def elapsed(kind: str) -> float:
        return float(
            events.boundary(kind, lambda: {"seconds": clock() - origin})["seconds"]
        )

    def assess(turn: int) -> GraphStop | None:
        if elapsed("assess_time") >= budget:
            return GraphStop("budget_exhausted", "workflow_budget_exhausted")
        if action is not None:
            return GraphStop("completed")
        return None

    def load_prompt() -> _Payload:
        nonlocal client
        try:
            client = client if client is not None else get_client()
            prompt = client.get_prompt(
                limits.prompt_name,
                type="chat",
                version=limits.prompt_version,
                label=limits.prompt_label if limits.prompt_version is None else None,
                max_retries=0,
                fetch_timeout_seconds=max(1, min(5, int(origin + budget - clock()))),
            )
            if (
                not isinstance(prompt, ChatPromptClient)
                or prompt.is_fallback
                or type(prompt.version) is not int
                or prompt.version < 1
            ):
                raise ValueError("native prompt unavailable")
            compiled = prompt.compile(
                canonical_input=canonical_json_bytes(summary).decode(), history=[]
            )
            messages = [
                ChatMessage.model_validate(m).model_dump(mode="json") for m in compiled
            ]
            trace.start(
                client,
                "investigate-ingestion",
                "agent",
                metadata={"mode": mode, "prompt_version": prompt.version},
                **({"inputs": {"mode": mode, "status": status}} if synthetic else {}),
            )
            return {
                "messages": messages,
                "name": prompt.name,
                "version": prompt.version,
            }
        except Exception:
            return {"failure": "prompt_unavailable"}

    def model(turn: int) -> GraphStop | ProviderResponse:
        nonlocal generation
        if not base:
            prompt_meta.update(events.boundary("prompt", load_prompt))
            if "failure" in prompt_meta:
                return GraphStop("error", prompt_meta["failure"])
            base.extend(ChatMessage.model_validate(m) for m in prompt_meta["messages"])
        messages = tuple(base + history)
        available = tools if len(tool_ids) < limits.max_tool_calls else ()
        encoded = canonical_json_bytes(
            {
                "messages": [m.model_dump(mode="json") for m in messages],
                "tools": [t.model_dump(mode="json") for t in available],
            }
        )
        codex = start["codex"]
        if codex:
            encoded = CodexAdapter.input_bytes(messages, available)
        identity = {
            "turn": turn,
            "input_digest": evidence_digest(encoded),
            "input_bytes": len(encoded),
        }
        if events.boundary("input", lambda: identity) != identity:
            raise ReplayEvidenceError("corrupt_evidence")
        if len(encoded) > limits.max_prompt_bytes:
            return GraphStop("error", "prompt_too_large")
        remaining = budget - elapsed("call_time")
        if remaining <= 0:
            return GraphStop("budget_exhausted", "workflow_budget_exhausted")

        def invoke() -> _Payload:
            nonlocal generation
            assert adapter is not None
            generation = trace.start(
                trace.root,
                "ingestion-model",
                "generation",
                metadata={"turn": turn, "prompt_version": prompt_meta["version"]},
                model=start["model"],
            )
            at_dispatch = origin + budget - clock()
            if at_dispatch <= 0:
                return {"failure": "workflow_budget_exhausted", "attempt_count": 0}
            opts: dict[str, Any] = dict(
                output_format="text",
                budget_seconds=min(remaining, at_dispatch),
                tools=available or None,
                tool_choice="auto" if available else "none",
            )
            try:
                if isinstance(adapter, CodexAdapter):
                    response = adapter.invoke_for_turn(
                        journal.id, turn, messages, **opts
                    )
                else:
                    response = adapter.invoke(messages, **opts)
                return {"response": response.model_dump(mode="json")}
            except ProviderUnavailableError as exc:
                return {"failure": exc.failure_code, "attempt_count": exc.attempt_count}
            except ProviderResponseTooLargeError as exc:
                return {
                    "failure": "response_too_large",
                    "attempt_count": exc.attempt_count,
                }

        received = events.boundary("model_response", invoke)
        if "failure" in received:
            trace.end(generation)
            return GraphStop("error", received["failure"])
        return ProviderResponse.model_validate(received["response"])

    def retain(turn: int, response: ProviderResponse) -> GraphStop | ProviderResponse:
        nonlocal advice
        trace.end(generation)
        if elapsed("retained_time") >= budget:
            return GraphStop("budget_exhausted", "workflow_budget_exhausted")
        try:
            if start["codex"]:
                response = decode_codex_response(response)
            metadata = response.response_metadata
            if response.raw_tool_calls is not None or (
                metadata and metadata.content_state == "invalid_tool_calls"
            ):
                return GraphStop("error", "invalid_provider_tool_calls")
            if metadata and metadata.finish_reason in {"length", "content_filter"}:
                return GraphStop("error", "incomplete_provider_response")
            if not response.tool_calls:
                advice = advisory(
                    response.content, mode, status, {"initial", *tool_ids}
                )
                return GraphStop("completed")
            if len(response.tool_calls) != 1:
                raise ValueError
            history.append(
                ChatMessage(
                    role="assistant",
                    content=response.content,
                    tool_calls=response.tool_calls,
                )
            )
            return response
        except (ValueError, TypeError, RecursionError):
            return GraphStop("error", "invalid_model_proposal")

    def read(turn: int, call: ToolCall) -> GraphStop | None:
        if elapsed("lookup_time") >= budget:
            return GraphStop("budget_exhausted", "workflow_budget_exhausted")
        try:
            key, value = lookup(call, tools, initial)
        except (ValueError, TypeError, RecursionError):
            return GraphStop("error", "invalid_tool_request")
        if key in seen or call.id in {"initial", *tool_ids}:
            return GraphStop("error", "repeated_tool_request")
        span = trace.start(
            trace.root,
            "ingestion-read",
            "tool",
            metadata={"turn": turn, "call_id": call.id, "tool": call.function.name},
        )
        observed = events.boundary(
            "lookup", lambda: {"proposal_id": call.id, "value": value}
        )
        trace.end(span)
        if observed.get("proposal_id") != call.id or observed.get("value") != value:
            return GraphStop("error", "observation_mismatch")
        if elapsed("observed_time") >= budget:
            return GraphStop("budget_exhausted", "workflow_budget_exhausted")
        seen.add(key)
        tool_ids.append(call.id)
        history.append(
            ChatMessage(
                role="tool",
                tool_call_id=call.id,
                name=call.function.name,
                content=canonical_json_bytes(observed).decode(),
            )
        )
        return None

    def finish(stop: GraphStop) -> _Payload:
        reason = stop.failure_code or stop.status
        accepted = advice if reason == "completed" else None
        result = {
            "investigation_id": journal.id,
            "previous_id": start["previous_id"],
            "mode": mode,
            "scope": start["scope"],
            "initial": initial,
            "status": status,
            "next_action": (accepted["next_action"] if accepted else action)
            if reason == "completed"
            else "request_confirmation",
            "advisory": accepted,
            "termination": reason,
            "observation_ids": tool_ids,
            "prompt_version": prompt_meta.get("version"),
            "model": start["model"] if prompt_meta else None,
        }
        return result

    try:
        result = run_investigation_graph(
            assess=assess,
            model=model,
            retain=retain,
            read=read,
            finish=finish,
            max_turns=limits.max_tool_calls + 2,
            max_tool_calls=limits.max_tool_calls,
        )
    finally:
        trace.end(trace.root)
    # 원격 전송 상태는 로컬 결과 게시 뒤 별도로 기록한다.
    return result, trace


def investigate_ingestion(
    mode: Literal["prepare", "review_run"],
    *,
    request: DataOperationRequest | None = None,
    run: RunRef | None = None,
    reader: AirflowRunReader | None = None,
    previous_id: str | None = None,
    artifact_root: Path = Path(".local/artifacts"),
    ai_settings: ReliabilityAISettings | None = None,
    settings: RuntimeAISettings | CodexSettings | None = None,
    provider: InvestigationProvider | None = None,
    client: Any = None,
    synthetic: bool = False,
    clock: Callable[[], float] = time.monotonic,
) -> dict[str, Any]:
    origin = clock()
    limits = ai_settings or ReliabilityAISettings(
        prompt_name="hmda-reliability-ai/ingestion"
    )
    deadline = origin + limits.workflow_budget_seconds
    if mode == "prepare" and (request is None or run is not None or reader is not None):
        raise ValueError("prepare requires a data operation request")
    if mode == "review_run" and (run is None or reader is None or request is not None):
        raise ValueError("review_run requires a scoped reader and run")
    if mode not in ("prepare", "review_run"):
        raise ValueError("unknown ingestion mode")
    prepared = None
    if previous_id is not None:
        obj, entries = validate_previous(artifact_root, previous_id)
        if (
            mode == "review_run"
            and obj is not None
            and obj["result"]["termination"] == "completed"
            and entries[0]["data"]["mode"] == "prepare"
        ):
            prepared = {
                "version": entries[1]["data"].get("version"),
                "scope": entries[0]["data"]["scope"],
            }
    if request is None:
        assert run is not None
        scope = run.model_dump()
    else:
        scope = {
            "source_year": request.source_year,
            "source_file": request.source_file,
            "source_root": str(request.source_root.absolute()),
            "raw_table_name": request.raw_table_name,
        }
    configuration, adapter = resolve_investigation_provider(settings, provider, clock)
    journal = IngestionJournal(artifact_root)
    events = _Events(journal, None)
    start = {
        "mode": mode,
        "limits": limits.model_dump(mode="json"),
        "model": configuration.model,
        "codex": isinstance(adapter, CodexAdapter),
        "scope": scope,
        "previous_id": previous_id,
    }
    initial: dict[str, Any] = {}
    try:
        journal.add("start", start)
        if request is not None:
            initial = inspect_inputs(request, clock=clock, deadline=deadline)
        else:
            assert run is not None and reader is not None
            stages = [
                reader.read(run, stage, prepared, deadline=deadline, clock=clock)
                for stage in STAGES
            ]
            initial = {"stages": stages}
        journal.add("initial", initial)
        result, trace = _run(
            journal,
            start,
            initial,
            events,
            clock=clock,
            origin=origin,
            client=client,
            adapter=adapter,
            synthetic=synthetic,
        )
        result = journal.publish(result, clock, deadline)
        if trace.root is not None or trace.errors:
            try:
                client = client if client is not None else get_client()
                client.flush()
            except Exception:
                trace.errors.append("observation_flush_failed")
            projection: dict[str, Any] = {
                "trace_id": trace.trace_id,
                "observations": trace.observations,
                "status": "submission_failed"
                if trace.errors
                else "submitted_unverified",
                "errors": trace.errors,
            }
            try:
                write_review_json(
                    journal.path / "observations.json",
                    projection,
                    max_record_bytes=MAX_BYTES,
                )
            except InvocationEvidenceStoreError:
                projection["status"] = "observation_write_failed"
            result = {**result, "observation": projection}
        return result
    except (InvocationEvidenceStoreError, OSError):
        status = initial_handoff(mode, initial)[0] if initial else "needs_human"
        handoff: dict[str, Any] = {
            "investigation_id": journal.id,
            "previous_id": previous_id,
            "mode": mode,
            "scope": scope,
            "initial": initial,
            "status": status,
            "next_action": "request_confirmation",
            "termination": "evidence_write_failed",
            "advisory": None,
            "observation_ids": [],
        }
        return journal.retain_failure(handoff)
    finally:
        if provider is None and isinstance(adapter, CodexAdapter):
            adapter.close()


class _RecordedWriteFailure(Exception):
    """재현에서 원래의 create-only 쓰기가 실패한 동일 경계에 도달했다."""


class _ReplayEvents(_Events):
    def __init__(
        self,
        journal: IngestionJournal,
        records: list[dict[str, Any]],
        failure: dict[str, Any] | None,
    ):
        super().__init__(journal, records)
        self.failure = failure

    def boundary(self, kind: str, get: Callable[[], dict[str, Any]]) -> dict[str, Any]:
        if self.failure == {"kind": kind, "index": self.index}:
            self.journal.failed_event = dict(self.failure)
            raise _RecordedWriteFailure
        return super().boundary(kind, get)


def replay_ingestion(
    investigation_id: str, *, artifact_root: Path = Path(".local/artifacts")
) -> dict[str, Any]:
    journal = IngestionJournal(artifact_root)
    identity = {"investigation_id": journal.id, "replayed_from": investigation_id}
    try:
        manifest, records = load_record(artifact_root, investigation_id)
        original = manifest["result"]
        events = _ReplayEvents(journal, records, manifest.get("failed_event"))

        def offline() -> dict[str, Any]:
            raise ReplayEvidenceError("missing_evidence")

        start: dict[str, Any] = {}
        initial: dict[str, Any] = {}
        try:
            start = events.boundary("start", offline)
            initial = events.boundary("initial", offline)
            result, _ = _run(
                journal,
                start,
                initial,
                events,
                clock=lambda: 0,
                origin=0,
                client=None,
                adapter=None,
                synthetic=False,
            )
        except _RecordedWriteFailure:
            # A failed first/second write can still preserve its scope or measured input
            # in the independent failure record. No source or provider is re-read.
            if events.index < 2:
                initial = original["initial"]
            mode = start.get("mode", original["mode"])
            result = {
                **identity,
                "mode": mode,
                "scope": start.get("scope", original["scope"]),
                "previous_id": start.get("previous_id", original["previous_id"]),
                "initial": initial,
                "status": initial_handoff(mode, initial)[0]
                if initial
                else "needs_human",
                "next_action": "request_confirmation",
                "termination": "evidence_write_failed",
                "advisory": None,
                "observation_ids": [],
            }
        if events.index != len(records) or events.failure != journal.failed_event:
            raise ReplayEvidenceError("corrupt_evidence")
        publication = manifest.get("publication")
        if publication is not None:
            if (
                publication
                not in {"workflow_budget_exhausted", "evidence_write_failed"}
                or events.failure
            ):
                raise ReplayEvidenceError("corrupt_evidence")
            result.update(
                termination=publication,
                next_action="request_confirmation",
                advisory=None,
            )
        result.update(identity)
        identity_fields = {"investigation_id", "replayed_from"}
        if {k: v for k, v in result.items() if k not in identity_fields} != {
            k: v for k, v in original.items() if k not in identity_fields
        }:
            raise ReplayEvidenceError("corrupt_evidence")
        if events.failure:
            return journal.retain_failure(result)
        return journal.publish(
            result, lambda: 0, float("inf"), recorded_publication=publication
        )
    except ReplayEvidenceError as exc:
        return {**identity, "termination": exc.reason}
    except (ValueError, TypeError, KeyError, IndexError, RecursionError):
        return {**identity, "termination": "corrupt_evidence"}
    except (InvocationEvidenceStoreError, OSError):
        return {**identity, "termination": "replay_write_failed"}
