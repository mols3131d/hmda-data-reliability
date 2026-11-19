"""원본의 모델·도구·시계·저장 결과를 공급해 같은 사고 조사 그래프를 재실행한다."""

from __future__ import annotations

import json
import math
import tempfile
import uuid
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Literal

from hmda_reliability.reliability.contracts.base import ReliabilityContract
from hmda_reliability.reliability_ai.investigation.contracts import (
    InvestigationResult,
    InvestigationTurnRecord,
    ToolCallRecord,
)
from hmda_reliability.reliability_ai.investigation.records import read_record
from hmda_reliability.reliability_ai.investigation.tools import (
    DEFAULT_INVESTIGATION_TOOLS,
)
from hmda_reliability.reliability_ai.settings import ReliabilityAISettings
from hmda_reliability.reliability_ai.store import ReplayEvidenceError
from hmda_reliability.runtime_ai.codex import CodexSettings
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
from hmda_reliability.runtime_ai.settings import RuntimeAISettings


class InvestigationReplay(ReliabilityContract):
    replay_id: str
    source_invocation_id: str
    outcome: Literal["replayed", "unreplayable"]
    status: str | None = None
    failure_code: str | None = None
    reason: str | None = None


class _RecordedProvider:
    def __init__(
        self,
        turns: Sequence[InvestigationTurnRecord],
        requests: list[list[dict[str, Any]]],
        raw_available: set[int],
        *,
        max_bytes: int,
    ) -> None:
        self.turns = [turn for turn in turns if turn.role == "assistant"]
        self.requests = requests
        self.raw_available = raw_available
        self.max_bytes = max_bytes
        self.count = 0

    def invoke(
        self, messages: tuple[ChatMessage, ...], **kwargs: Any
    ) -> ProviderResponse:
        i = self.count
        self.count += 1
        turn = self.turns[i]
        if [message.model_dump(mode="json") for message in messages] != self.requests[
            i
        ]:
            raise ReplayEvidenceError("input_mismatch")
        if (
            i not in self.raw_available
            and turn.failure_code == "provider_response_too_large"
        ):
            raise ProviderResponseTooLargeError(
                attempt_count=turn.attempt_count or 0,
                latency_ms=turn.latency_ms,
                actual_bytes=self.max_bytes + 1,
                max_bytes=self.max_bytes,
                usage=turn.usage,
                trace_id=None,
                response_metadata=turn.response_metadata,
            )
        if (
            i not in self.raw_available
            and turn.failure_code
            and not turn.content
            and turn.raw_tool_calls is None
        ):
            raise ProviderUnavailableError(
                failure_code=turn.failure_code,
                attempt_count=turn.attempt_count or 0,
                latency_ms=turn.latency_ms,
            )
        return ProviderResponse.model_validate(
            {
                "content": turn.content,
                "tool_calls": turn.tool_calls,
                "raw_tool_calls": turn.raw_tool_calls,
                "attempt_count": turn.attempt_count,
                "latency_ms": turn.latency_ms,
                "usage": turn.usage,
                "response_metadata": turn.response_metadata,
            }
        )


class _RecordedRegistry:
    def __init__(
        self,
        definitions: list[dict[str, Any]],
        result: InvestigationResult,
        observations: list[dict[str, str]],
    ) -> None:
        self.definitions = tuple(ToolDefinition.model_validate(d) for d in definitions)
        self.records = result.tool_calls
        self.unserializable = {
            i
            for i, ref in enumerate(observations)
            if ref.get("serialization") == "failed"
        }
        self.outputs = {
            i: turn.content
            for i, turn in enumerate(t for t in result.turns if t.role == "tool")
        }
        self.count = 0

    def execute(self, tool_call: ToolCall) -> tuple[ToolCallRecord, str]:
        call = tool_call
        i = self.count
        self.count += 1
        record = self.records[i]
        matches = record.call_id == call.id and record.tool_name == call.function.name
        redacted_mismatch = (
            record.status == "error"
            and not record.arguments
            and record.result == {"error": "tool_observation_mismatch"}
        )
        if not matches and not redacted_mismatch:
            raise ReplayEvidenceError("tool_mismatch")
        output = self.outputs.get(i)
        if output is None:
            output = json.dumps(record.result, ensure_ascii=False)
        if i in self.unserializable:
            # Reuse the original JSON arguments and tool message at the same boundary.
            record = record.model_copy(
                update={
                    "arguments": json.loads(call.function.arguments),
                    "result": json.loads(output),
                }
            )
        return record, output


def replay_investigation(
    path: Path, *, expected_revision: str | None = None
) -> InvestigationReplay:
    """일반·실패 manifest를 검증한다. 과거 형식은 읽을 수 있고 재현 불가로 분류한다."""
    from hmda_reliability.reliability_ai.investigation.service import (
        ReplayIncidentInput,
        _IncidentRun,
    )

    replay_id = f"replay-{uuid.uuid4().hex}"
    identity = {"source_invocation_id": path.stem, "replay_id": replay_id}
    try:
        document, original, requests = read_record(path)
        if "record_version" not in document or (
            expected_revision is not None
            and document["project_revision"] != expected_revision
        ):
            raise ReplayEvidenceError("incompatible_version")
        ticks: list[float] = document["relative_clock"]
        if not ticks:
            raise ReplayEvidenceError("missing_evidence")
        if (
            ticks[0] != 0
            or any(not math.isfinite(t) or t < 0 for t in ticks)
            or ticks != sorted(ticks)
        ):
            raise ReplayEvidenceError("corrupt_evidence")
        samples = iter(ticks)

        def frozen_clock() -> float:
            try:
                return next(samples)
            except StopIteration:
                raise ReplayEvidenceError("missing_evidence") from None

        configuration = dict(document["runtime_configuration"])
        config: CodexSettings | RuntimeAISettings
        provider_kind = configuration.pop("provider", None)
        if provider_kind == "codex" or (
            provider_kind == "injected" and "base_url" not in configuration
        ):
            config = CodexSettings.model_validate(configuration)
        else:
            config = RuntimeAISettings.model_validate(
                {**configuration, "api_key": "offline-recording"}
            )
        settings = ReliabilityAISettings.model_validate(document["ai_configuration"])
        assistant = [turn for turn in original.turns if turn.role == "assistant"]
        raw_available = {
            turn["turn"]
            for turn in document["result"]["turns"]
            if turn["role"] == "assistant" and "response" in turn
        }
        provider = _RecordedProvider(
            assistant, requests, raw_available, max_bytes=config.max_output_bytes
        )
        if "tool_definitions_json" in document:
            definitions = json.loads(document["tool_definitions_json"])
        else:
            # Earlier v2 files retain schema values but not nested key order.
            # A matching built-in schema is accepted only if the wire digest matches.
            builtins = [t.model_dump(mode="json") for t in DEFAULT_INVESTIGATION_TOOLS]
            definitions = [
                next((t for t in builtins if t == saved), saved)
                for saved in document["tool_definitions"]
            ]
        registry = _RecordedRegistry(definitions, original, document["observations"])
        prompt = document["prompt"] or {}
        failed_write = document.get("failed_write") or {}
        replay = ReplayIncidentInput(
            canonical_input=document["canonical_input"],
            incident_id=original.incident_id,
            project_revision=document["project_revision"],
            evidence_refs=tuple(document["evidence_refs"]),
            codex_wire_input=document["codex_wire_input"],
            prompt_name=prompt.get("name"),
            prompt_version=prompt.get("version"),
            compiled_messages=requests,
            final_write_failure=document["publication"] == "failed",
            preflight_failure=document.get("preflight_failure"),
            final_write_expired=document["publication"] == "expired",
            publication_clock_reads=document["publication_clock_reads"],
            failed_tool_id=failed_write.get("tool_id"),
            write_failure=failed_write.get("kind"),
            failed_turn=failed_write.get("turn"),
        )
        with tempfile.TemporaryDirectory(prefix="hmda-replay-") as directory:
            result = _IncidentRun(
                None,
                settings=config,
                ai_settings=settings,
                provider=provider,
                tool_registry=registry,
                allowed_tools=tuple(document["allowed_tools"]),
                artifact_root=Path(directory),
                clock=frozen_clock,
                replay=replay,
            ).run()
            replay_path = result.manifest_path or (
                Path(directory)
                / "reliability-ai"
                / "failures"
                / f"{result.invocation_id}.json"
            )
            reproduced, _, _ = read_record(replay_path)
            if any(
                reproduced[field] != document[field]
                for field in ("input_digests", "input_bytes")
            ):
                raise ReplayEvidenceError("input_mismatch")
        if next(samples, None) is not None:
            raise ReplayEvidenceError("execution_mismatch")
        if provider.count != len(assistant) or registry.count != len(
            original.tool_calls
        ):
            raise ReplayEvidenceError("execution_mismatch")
        expected: tuple[str, str | None]
        if document["publication"] == "failed":
            expected = ("error", "manifest_persistence_failed")
        else:
            expected = (original.status, original.failure_code)
        if (result.status, result.failure_code) != expected:
            raise ReplayEvidenceError("execution_mismatch")
        if result.status == "completed" and (
            result.facts,
            result.findings,
            result.hypotheses,
            result.uncertainties,
        ) != (
            original.facts,
            original.findings,
            original.hypotheses,
            original.uncertainties,
        ):
            raise ReplayEvidenceError("execution_mismatch")
        return InvestigationReplay(
            **identity,
            outcome="replayed",
            status=result.status,
            failure_code=result.failure_code,
        )
    except ReplayEvidenceError as exc:
        return InvestigationReplay(
            **identity, outcome="unreplayable", reason=exc.reason
        )
    except (KeyError, ValueError, IndexError, TypeError, RecursionError):
        return InvestigationReplay(
            **identity, outcome="unreplayable", reason="corrupt_evidence"
        )
