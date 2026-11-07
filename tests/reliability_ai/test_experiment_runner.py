"""Offline Dataset task output and completion exit-code contracts."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest

from hmda_reliability.reliability_ai import AgenticReviewInput
from hmda_reliability.reliability_ai.evaluation import experiment
from hmda_reliability.reliability_ai.investigation.contracts import InvestigationResult

from .conftest import NullSpikeReviewMaterial

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(("status", "exit_code"), [("completed", 0), ("error", 1)])
def test_experiment_preserves_investigation_output_and_exit_status(
    null_spike_review_material: NullSpikeReviewMaterial,
    monkeypatch: pytest.MonkeyPatch,
    status: str,
    exit_code: int,
) -> None:
    material = null_spike_review_material
    review_input = AgenticReviewInput(
        incident=material.detection.incident,
        evidence=[material.detection.evidence],
        draft=material.draft,
        project_revision="input-revision",
    )
    result = InvestigationResult.model_validate(
        {
            "incident_id": review_input.incident.incident_id,
            "status": status,
            "failure_code": "provider_timeout" if status == "error" else None,
            "findings": [
                {
                    "topic": "null_spike",
                    "description": "income requires source verification",
                    "evidence_refs": [material.detection.evidence.evidence_id],
                }
            ],
            "hypotheses": [
                {
                    "hypothesis": "source change",
                    "status": "uncertain",
                    "rationale": "source not inspected",
                }
            ],
            "uncertainties": [
                {
                    "topic": "source",
                    "description": "source state is unknown",
                    "needed_evidence": "source profile",
                }
            ],
            "tool_calls": [
                {
                    "call_id": "call-1",
                    "tool_name": "get_incident_evidence",
                    "arguments": {
                        "evidence_id": material.detection.evidence.evidence_id
                    },
                    "result": {"found": True},
                    "latency_ms": 1,
                    "status": "success",
                }
            ],
            "manifest_path": Path(".local/artifacts/investigation.json"),
        }
    )
    captured: dict[str, Any] = {}
    dataset_item = SimpleNamespace(
        id="item-1", input=review_input.model_dump(mode="json")
    )

    def run_experiment(**kwargs: Any) -> SimpleNamespace:
        captured.update(kwargs["task"](item=dataset_item))
        return SimpleNamespace(
            item_results=[SimpleNamespace(item=dataset_item, output=captured)],
            format=lambda: "offline",
        )

    dataset = MagicMock()
    dataset.items = [dataset_item]
    dataset.run_experiment.side_effect = run_experiment
    client = MagicMock()
    client.get_dataset.return_value = dataset
    monkeypatch.setattr(experiment, "get_client", lambda: client)
    monkeypatch.setattr(
        experiment, "investigate_incident", lambda *args, **kwargs: result
    )

    actual_exit_code = experiment.main(argv=[])

    assert actual_exit_code == exit_code
    assert captured == {**result.model_dump(mode="json"), "tool_calls_count": 1}


@pytest.mark.parametrize("returned_ids", [("first",), ("first", "first")])
def test_experiment_rejects_missing_or_duplicated_item_results(
    monkeypatch: pytest.MonkeyPatch, returned_ids: tuple[str, ...]
) -> None:
    dataset = MagicMock()
    dataset.items = [SimpleNamespace(id="first"), SimpleNamespace(id="second")]
    dataset.run_experiment.return_value = SimpleNamespace(
        item_results=[
            SimpleNamespace(
                item=SimpleNamespace(id=item_id), output={"status": "completed"}
            )
            for item_id in returned_ids
        ],
        format=lambda: "offline partial result",
    )
    client = MagicMock()
    client.get_dataset.return_value = dataset
    monkeypatch.setattr(experiment, "get_client", lambda: client)

    assert experiment.main(argv=[]) == 1
