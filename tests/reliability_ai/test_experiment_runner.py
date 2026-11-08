"""Offline Dataset task output and completion exit-code contracts."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest

from hmda_reliability.reliability_ai import AgenticReviewInput
from hmda_reliability.reliability_ai.context import project_remote_output
from hmda_reliability.reliability_ai.evaluation import experiment
from hmda_reliability.reliability_ai.evaluation import setup as evaluation_setup
from hmda_reliability.reliability_ai.investigation.contracts import InvestigationResult

from .conftest import NullSpikeReviewMaterial

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("status", "flush_failed", "exit_code"),
    [("completed", False, 0), ("completed", True, 0), ("error", False, 1)],
)
def test_experiment_preserves_investigation_output_and_exit_status(
    null_spike_review_material: NullSpikeReviewMaterial,
    monkeypatch: pytest.MonkeyPatch,
    status: str,
    flush_failed: bool,
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
    invocation: dict[str, Any] = {}
    dataset_item = SimpleNamespace(
        id="item-1",
        input=review_input.model_dump(mode="json"),
        metadata={"synthetic": True},
        expected_output={"oracle": "never send this to investigation"},
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
    if flush_failed:
        client.flush.side_effect = RuntimeError("synthetic observation failure")
    monkeypatch.setattr(experiment, "get_client", lambda: client)

    def investigate(*args: Any, **kwargs: Any) -> InvestigationResult:
        assert args[0].model_dump(mode="json")["project_revision"] != "input-revision"
        assert "never send this" not in args[0].model_dump_json()
        invocation.update(kwargs)
        return result

    monkeypatch.setattr(experiment, "investigate_incident", investigate)

    actual_exit_code = experiment.main(
        argv=[
            "--dbt-manifest",
            "manifest.json",
            "--dbt-run-results",
            "run_results.json",
            "--prompt-version",
            "7",
            "--max-tool-calls",
            "3",
            "--workflow-budget-seconds",
            "120",
            "--max-output-tokens",
            "2048",
        ]
    )

    assert actual_exit_code == exit_code
    assert captured == {
        **project_remote_output(result.model_dump(mode="json")),
        "tool_calls_count": 1,
    }
    assert invocation["dbt_artifact_paths"] == (
        Path("manifest.json"),
        Path("run_results.json"),
    )
    assert invocation["ai_settings"].prompt_version == 7
    assert invocation["ai_settings"].max_tool_calls == 3
    assert invocation["settings"].max_output_tokens == 2048
    assert invocation["observe_io"] is True
    selected_version = client.get_dataset.call_args.kwargs["version"]
    assert isinstance(selected_version, datetime)
    assert selected_version.tzinfo is not None
    assert (
        dataset.run_experiment.call_args.kwargs["metadata"]["dataset_version"]
        == selected_version.isoformat()
    )
    client.create_prompt.assert_not_called()
    client.create_dataset.assert_not_called()


@pytest.mark.parametrize("returned_ids", [("first",), ("first", "first")])
def test_experiment_rejects_missing_or_duplicated_item_results(
    monkeypatch: pytest.MonkeyPatch, returned_ids: tuple[str, ...]
) -> None:
    dataset = MagicMock()
    dataset.items = [
        SimpleNamespace(id="first", metadata={"synthetic": True}),
        SimpleNamespace(id="second", metadata={"synthetic": True}),
    ]
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


def test_explicit_prompt_setup_registers_pinned_native_composition(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = MagicMock()
    client.create_prompt.return_value.version = 3
    monkeypatch.setattr(evaluation_setup, "get_client", lambda: client)

    assert evaluation_setup.main(argv=["--prompts-only"]) == 0

    registered = [call.kwargs for call in client.create_prompt.call_args_list]
    assert len(registered) == 6
    assert len({entry["name"] for entry in registered}) == 6
    chat = registered[-1]
    assert chat["name"] == "hmda-reliability-ai/investigation"
    assert chat["type"] == "chat"
    assert "|version=3@@@" in chat["prompt"][0]["content"]
    assert chat["prompt"][1] == {"role": "user", "content": "{{canonical_input}}"}
    assert chat["prompt"][2] == {"type": "placeholder", "name": "history"}
    client.create_dataset.assert_not_called()


def test_invalid_dataset_input_is_rejected_without_invocation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    item = SimpleNamespace(
        id="invalid", input={"incident": "invalid"}, metadata={"synthetic": True}
    )
    dataset = MagicMock()
    dataset.items = [item]

    def run_experiment(**kwargs: Any) -> SimpleNamespace:
        output = kwargs["task"](item=item)
        assert output == {
            "status": "input_rejected",
            "failure_code": "invalid_review_input",
        }
        return SimpleNamespace(
            item_results=[SimpleNamespace(item=item, output=output)],
            format=lambda: "invalid input",
        )

    dataset.run_experiment.side_effect = run_experiment
    client = MagicMock()
    client.get_dataset.return_value = dataset
    monkeypatch.setattr(experiment, "get_client", lambda: client)
    invoke = MagicMock()
    monkeypatch.setattr(experiment, "investigate_incident", invoke)

    assert experiment.main(argv=[]) == 1
    invoke.assert_not_called()


@pytest.mark.parametrize(
    "metadata", [None, {}, {"synthetic": False}, {"synthetic": "true"}]
)
def test_unapproved_dataset_stops_before_native_experiment(
    monkeypatch: pytest.MonkeyPatch, metadata: object
) -> None:
    dataset = MagicMock()
    dataset.items = [
        SimpleNamespace(id="approved", metadata={"synthetic": True}, input={}),
        SimpleNamespace(id="unapproved", metadata=metadata, input={}),
    ]
    client = MagicMock()
    client.get_dataset.return_value = dataset
    monkeypatch.setattr(experiment, "get_client", lambda: client)
    invoke = MagicMock()
    monkeypatch.setattr(experiment, "investigate_incident", invoke)

    assert experiment.main(argv=[]) == 2
    dataset.run_experiment.assert_not_called()
    invoke.assert_not_called()
    client.flush.assert_not_called()
