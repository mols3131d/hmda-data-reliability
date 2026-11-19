"""버전 있는 조사 기록은 외부 호출 없이 검증하고 복원한다."""

import json
from pathlib import Path
from typing import Any, Never
from unittest.mock import MagicMock

import pytest

from hmda_reliability.reliability_ai.investigation.contracts import (
    InvestigationResult,
    ToolCallRecord,
)
from hmda_reliability.reliability_ai.investigation.records import (
    InvestigationJournal,
    load_investigation,
)

from .conftest import NullSpikeReviewMaterial

pytestmark = pytest.mark.component


def test_existing_unversioned_investigation_remains_readable(tmp_path: Path) -> None:
    path = tmp_path / "inv-historical.json"
    path.write_text(
        '{"result":{"incident_id":"old","invocation_id":"inv-historical",'
        '"status":"error","failure_code":"invalid_investigation_output",'
        '"turns":[{"turn":0,"role":"assistant","content":" {"}]}}'
    )
    restored = load_investigation(path)
    assert restored.incident_id == "old"
    assert restored.turns[0].content == " {"
    assert restored.failure_code == "invalid_investigation_output"


def test_tool_observation_survives_without_a_final_manifest(tmp_path: Path) -> None:
    journal = InvestigationJournal(tmp_path, "inv-sample")
    record = ToolCallRecord(
        call_id="proposal-1",
        tool_name="compare_profiles",
        arguments={},
        result={"observed": 71},
        latency_ms=3,
        status="success",
    )
    journal.observe_tool(0, record, '{"observed": 71}')
    files = list(
        (tmp_path / "reliability-ai" / "observations").glob("inv-sample-*.json")
    )
    assert len(files) == 1
    assert files[0].stat().st_mode & 0o077 == 0
    assert "proposal-1" in files[0].read_text()
    assert "71" in files[0].read_text()


@pytest.mark.parametrize(
    "case",
    [
        "completed",
        "invalid",
        "late",
        "final-write",
        "tool-write",
        "response-write",
        "result-copy-write",
    ],
)
def test_replay_uses_original_boundaries_with_no_external_calls(
    case: str,
    null_spike_review_material: NullSpikeReviewMaterial,
    native_prompt_client: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    from hmda_reliability.reliability_ai import AgenticReviewInput, investigate_incident
    from hmda_reliability.reliability_ai.investigation import service
    from hmda_reliability.reliability_ai.investigation.replay import (
        replay_investigation,
    )
    from hmda_reliability.reliability_ai.investigation.tools import ToolRegistry
    from hmda_reliability.reliability_ai.store import (
        InvocationEvidenceWriteError,
        InvocationResponseStore,
        write_review_json,
    )
    from hmda_reliability.runtime_ai.contracts import ProviderResponse

    material = null_spike_review_material
    review_input = AgenticReviewInput(
        incident=material.detection.incident,
        evidence=(material.detection.evidence,),
        draft=material.draft,
        project_revision="synthetic-replay-test",
    )
    responses = [
        ProviderResponse.model_validate(
            {
                "content": "",
                "tool_calls": [
                    {
                        "id": "original-call",
                        "function": {"name": "compare_profiles", "arguments": "{}"},
                    }
                ],
                "attempt_count": 1,
                "latency_ms": 0,
            }
        ),
        ProviderResponse(
            content="invalid JSON"
            if case == "invalid"
            else (
                '{"findings":[{"topic":"결측률",'
                '"description":"프로파일에서 결측률 증가를 확인했다."}],'
                '"hypotheses":[],"uncertainties":[]}'
            ),
            attempt_count=1,
            latency_ms=0,
        ),
    ]
    now = 100.0

    class Provider:
        def invoke(self, *args: Any, **kwargs: Any) -> ProviderResponse:
            nonlocal now
            if len(responses) == 1 and case == "late":
                now += 61
            return responses.pop(0)

    def run() -> InvestigationResult:
        return investigate_incident(
            review_input,
            provider=Provider(),
            artifact_root=tmp_path,
            clock=lambda: now,
            tool_registry=ToolRegistry(
                profile_comparison_handler=lambda _: {"daily_metric": 42}
            ),
        )

    if case in {"tool-write", "response-write"}:
        with monkeypatch.context() as storage_failure:
            if case == "tool-write":

                def fail_observation(*args: Any, **kwargs: Any) -> Never:
                    raise InvocationEvidenceWriteError("simulated tool write failure")

                storage_failure.setattr(
                    InvestigationJournal, "observe_tool", fail_observation
                )
            else:

                def fail_response(*args: Any, **kwargs: Any) -> Never:
                    raise InvocationEvidenceWriteError(
                        "simulated response write failure"
                    )

                storage_failure.setattr(InvocationResponseStore, "write", fail_response)
            result = run()
    elif case in {"final-write", "result-copy-write"}:

        def fail_publication(
            path: Path, data: dict[str, object], **kwargs: Any
        ) -> Path:
            if (case == "final-write" and "result" in data) or (
                case == "result-copy-write" and path.parent.name == "results"
            ):
                raise InvocationEvidenceWriteError("simulated publication failure")
            return write_review_json(path, data, **kwargs)

        monkeypatch.setattr(service, "write_review_json", fail_publication)
        result = run()
    else:
        result = run()
    expected = {
        "completed": ("completed", None),
        "tool-write": ("error", "tool_observation_persistence_failed"),
        "response-write": ("error", "response_persistence_failed"),
        "invalid": ("error", "invalid_investigation_output"),
        "late": ("budget_exhausted", "workflow_budget_exhausted"),
        "final-write": ("error", "manifest_persistence_failed"),
        "result-copy-write": ("completed", None),
    }
    assert (result.status, result.failure_code) == expected[case]
    path = result.manifest_path or (
        tmp_path / "reliability-ai" / "failures" / f"{result.invocation_id}.json"
    )
    assert load_investigation(path).status == result.status
    result_path = (
        tmp_path / "reliability-ai" / "results" / f"{result.invocation_id}.json"
    )
    if case in {"final-write", "result-copy-write"}:
        assert not result_path.exists()
        if case == "result-copy-write":
            assert "investigation result JSON unavailable" in caplog.text
    else:
        displayed = result_path.read_text(encoding="utf-8")
        assert displayed.startswith('{\n  "')
        assert result_path.stat().st_mode & 0o077 == 0
        assert json.loads(displayed) == {
            "incident_id": result.incident_id,
            "invocation_id": result.invocation_id,
            "status": expected[case][0],
            "failure_code": expected[case][1],
            "facts": result.facts,
            "findings": [
                {
                    "topic": "결측률",
                    "description": "프로파일에서 결측률 증가를 확인했다.",
                    "evidence_refs": [],
                }
            ]
            if case == "completed"
            else [],
            "hypotheses": [],
            "uncertainties": [],
        }
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}

    def forbidden(*args: Any, **kwargs: Any) -> Never:
        pytest.fail("unexpected live model, tool or Langfuse call during replay")

    monkeypatch.setattr(service, "get_client", forbidden)
    monkeypatch.setattr(Provider, "invoke", forbidden)
    monkeypatch.setattr(ToolRegistry, "execute", forbidden)

    replay = replay_investigation(path)
    assert replay.outcome == "replayed", replay
    assert (replay.status, replay.failure_code) == expected[case]
    assert replay.source_invocation_id == result.invocation_id
    assert replay.replay_id != result.invocation_id
    assert {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()} == before

    if case == "completed":
        assert (
            replay_investigation(path, expected_revision="other").reason
            == "incompatible_version"
        )
        raw = result.response_paths[-1]
        raw.write_bytes(b"tampered")
        assert replay_investigation(path).reason == "corrupt_evidence"
        raw.unlink()
        assert replay_investigation(path).reason == "missing_evidence"


def test_codex_replay_recovers_exact_custom_schema_wire_order(
    tmp_path: Path,
    null_spike_review_material: NullSpikeReviewMaterial,
    native_prompt_client: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import json

    from hmda_reliability.reliability_ai import AgenticReviewInput, investigate_incident
    from hmda_reliability.reliability_ai.investigation.replay import (
        replay_investigation,
    )
    from hmda_reliability.reliability_ai.investigation.tools import ToolRegistry
    from hmda_reliability.runtime_ai.codex import CodexAdapter, CodexSettings
    from hmda_reliability.runtime_ai.contracts import ProviderResponse, ToolDefinition

    config = CodexSettings(model="fake")
    provider = CodexAdapter(config)

    class Registry(ToolRegistry):
        @property
        def definitions(self) -> tuple[ToolDefinition, ...]:
            return (
                ToolDefinition.model_validate(
                    {
                        "function": {
                            "name": "lookup",
                            "description": "test",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "z_id": {"type": "integer"},
                                    "a_id": {"type": "string"},
                                },
                            },
                        }
                    }
                ),
            )

    def stub(
        invocation_id: str, turn: int, *args: Any, **kwargs: Any
    ) -> ProviderResponse:
        text = json.dumps(
            {
                "content": '{"findings":[],"hypotheses":[],"uncertainties":[]}',
                "tool_calls": [],
            }
        )
        return ProviderResponse.model_validate(
            {
                "content": text,
                "attempt_count": 1,
                "latency_ms": 1,
                "response_metadata": {
                    "content_state": "text",
                    "content_bytes": len(text),
                    "codex_attempt": {
                        "invocation_id": invocation_id,
                        "logical_turn": turn,
                        "request_id": 1,
                        "thread_id": "thread",
                        "turn_id": "turn",
                        "model": "fake",
                    },
                },
            }
        )

    monkeypatch.setattr(provider, "invoke_for_turn", stub)
    material = null_spike_review_material
    result = investigate_incident(
        AgenticReviewInput(
            incident=material.detection.incident,
            evidence=(material.detection.evidence,),
            draft=material.draft,
            project_revision="schema-order-test",
        ),
        artifact_root=tmp_path,
        provider=provider,
        settings=config,
        tool_registry=Registry(),
    )
    assert result.status == "completed" and result.manifest_path is not None
    replay = replay_investigation(result.manifest_path)
    assert replay.outcome == "replayed" and replay.status == "completed"
