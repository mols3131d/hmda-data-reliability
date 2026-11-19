"""적재 재현은 각 저장·기한 경계와 원 조사 identity를 확인한다."""

import json
from pathlib import Path
from typing import Any, Never
from unittest.mock import MagicMock

import pytest

from hmda_reliability.reliability_ai.ingestion import (
    evidence,
    investigate_ingestion,
    replay_ingestion,
)
from hmda_reliability.reliability_ai.ingestion.airflow import AirflowRunReader
from hmda_reliability.reliability_ai.ingestion.evidence import validate_previous
from hmda_reliability.reliability_ai.store import (
    InvocationEvidenceWriteError,
    write_evidence_ref,
    write_review_json,
)
from tests.reliability_ai.test_ingestion_workflow import (
    native_client,
    response,
    setup_review,
    tool,
)

pytestmark = pytest.mark.component


@pytest.mark.parametrize(
    "failure", ["late", "start", "initial", "model_response", "lookup", "publish"]
)
def test_replay_recovers_observed_ingestion_boundary(
    failure: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request = setup_review(tmp_path)
    clock = [20.0]
    provider = MagicMock()

    def invoke(*args: Any, **kwargs: Any) -> Any:
        if failure == "late":
            clock[0] += 61
        return response(tool(source_id="source-1"))

    provider.invoke.side_effect = invoke
    with monkeypatch.context() as broken:

        def fail_event(
            path: Path, filename: str, payload: dict[str, object], **kwargs: Any
        ) -> dict[str, str]:
            if payload.get("kind") == failure:
                raise InvocationEvidenceWriteError("synthetic event failure")
            return write_evidence_ref(path, filename, payload, **kwargs)

        def fail_final(path: Path, payload: dict[str, object], **kwargs: Any) -> Path:
            if failure == "publish" and path.name == "result.json":
                raise InvocationEvidenceWriteError("synthetic final failure")
            return write_review_json(path, payload, **kwargs)

        broken.setattr(evidence, "write_evidence_ref", fail_event)
        broken.setattr(evidence, "write_review_json", fail_final)
        live = investigate_ingestion(
            "prepare",
            request=request,
            client=native_client(),
            provider=provider,
            artifact_root=tmp_path,
            clock=lambda: clock[0],
        )
    assert live["termination"] == (
        "workflow_budget_exhausted" if failure == "late" else "evidence_write_failed"
    )
    source_dir = tmp_path / "ingestion" / live["investigation_id"]
    captured = {p: p.read_bytes() for p in source_dir.glob("*") if p.is_file()}

    def unexpected(*args: Any, **kwargs: Any) -> Never:
        pytest.fail("replay contacted the source, provider or Langfuse")

    from hmda_reliability.reliability_ai.ingestion import service

    monkeypatch.setattr(service, "inspect_inputs", unexpected)
    monkeypatch.setattr(service, "get_client", unexpected)
    monkeypatch.setattr(AirflowRunReader, "read", unexpected)
    provider.invoke.side_effect = unexpected
    if failure == "late":
        _, events = evidence.load_record(tmp_path, live["investigation_id"])
        received = next(
            event["data"]["response"]
            for event in events
            if event["kind"] == "model_response"
        )
        assert received["tool_calls"][0]["id"] == "prop-1"
        assert all(event["kind"] != "lookup" for event in events)
    replay = replay_ingestion(live["investigation_id"], artifact_root=tmp_path)
    assert replay["termination"] == live["termination"], replay
    assert replay["next_action"] == live["next_action"]
    assert replay["investigation_id"] != live["investigation_id"]
    assert replay["replayed_from"] == live["investigation_id"]
    again = replay_ingestion(replay["investigation_id"], artifact_root=tmp_path)
    assert again["termination"] == replay["termination"]
    assert again["replayed_from"] == replay["investigation_id"]
    assert {p: p.read_bytes() for p in source_dir.glob("*") if p.is_file()} == captured


def test_empty_or_substituted_directory_is_not_a_previous_investigation(
    tmp_path: Path,
) -> None:
    prior = "ing-" + "a" * 32
    path = tmp_path / "ingestion" / prior
    path.mkdir(parents=True)
    with pytest.raises(ValueError):
        validate_previous(tmp_path, prior)


@pytest.mark.parametrize(
    "defect", ["missing-event", "changed-result", "substituted-start", "unsupported"]
)
def test_replay_rejects_invalid_journal(defect: str, tmp_path: Path) -> None:
    from hmda_reliability.data_operations.request import DataOperationRequest

    source = tmp_path / "empty"
    source.mkdir()
    live = investigate_ingestion(
        "prepare",
        request=DataOperationRequest(source_root=source),
        artifact_root=tmp_path,
    )
    invocation = live["investigation_id"]
    path = tmp_path / "ingestion" / invocation
    result = path / "result.json"
    expected = "corrupt_evidence"
    if defect == "missing-event":
        (path / "event-0.json").unlink()
        expected = "missing_evidence"
    elif defect == "substituted-start":
        other_id = "ing-" + "c" * 32
        other = tmp_path / "ingestion" / other_id
        other.mkdir()
        (other / "event-0.json").write_bytes((path / "event-0.json").read_bytes())
        with pytest.raises(ValueError, match="corrupt_evidence"):
            validate_previous(tmp_path, other_id)
        return
    else:
        payload = json.loads(result.read_bytes())
        if defect == "changed-result":
            payload["result"].pop("initial")
        else:
            payload["format"] = "future"
            expected = "unsupported_version"
        result.write_text(json.dumps(payload))
    replay = replay_ingestion(invocation, artifact_root=tmp_path)
    assert replay["termination"] == expected


def test_resuming_an_interrupted_investigation_reads_the_current_source(
    tmp_path: Path,
) -> None:
    from hmda_reliability.data_operations.request import DataOperationRequest

    source = tmp_path / "source"
    source.mkdir()
    prior = evidence.IngestionJournal(tmp_path)
    prior.add("start", {"mode": "prepare", "scope": {"source_root": str(source)}})
    prior.add("initial", {"status": "ready", "version": "outdated"})
    source.joinpath("unloadable.csv").write_text("invalid_header\n123\n")
    result = investigate_ingestion(
        "prepare",
        request=DataOperationRequest(source_root=source),
        previous_id=prior.id,
        artifact_root=tmp_path,
        client=native_client(),
        provider=MagicMock(),
    )
    assert result["investigation_id"] != prior.id
    assert result["previous_id"] == prior.id
    assert result["initial"]["version"] != "outdated"
    assert result["status"] == "blocked"
