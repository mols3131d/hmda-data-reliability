"""Tests for investigation read-only tools and tool registry."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from hmda_reliability.data_platform.artifacts import artifact_projection_id
from hmda_reliability.reliability import Evidence, EvidenceSource
from hmda_reliability.reliability_ai import AgenticReviewInput
from hmda_reliability.reliability_ai.investigation.tools import ToolRegistry
from hmda_reliability.runtime_ai.contracts import ToolCall, ToolCallFunction

from .conftest import NullSpikeReviewMaterial

pytestmark = pytest.mark.unit


def _evidence() -> Evidence:
    return Evidence(
        evidence_id="ev_test_1",
        source=EvidenceSource.PROFILE,
        asset_name="raw.hmda_loans",
        partition="2025",
        observed_at=datetime(2026, 8, 27, 0, 0, tzinfo=UTC),
        summary="Test profile summary",
        payload={"rule": "null_spike", "column": "income", "delta": 0.2},
    )


def test_tool_registry_dispatches_get_incident_evidence() -> None:
    ev = _evidence()
    registry = ToolRegistry(evidence_catalog={"ev_test_1": ev})

    call = ToolCall(
        id="call_1",
        function=ToolCallFunction(
            name="get_incident_evidence",
            arguments=json.dumps({"evidence_id": "ev_test_1"}),
        ),
    )
    record, output = registry.execute(call)

    assert record.status == "success"
    assert record.tool_name == "get_incident_evidence"
    payload = json.loads(output)
    assert payload["found"] is True
    assert payload["evidence_id"] == "ev_test_1"
    assert payload["summary"] == "Test profile summary"


def test_tool_registry_handles_missing_evidence() -> None:
    registry = ToolRegistry(evidence_catalog={})
    call = ToolCall(
        id="call_2",
        function=ToolCallFunction(
            name="get_incident_evidence",
            arguments=json.dumps({"evidence_id": "non_existent"}),
        ),
    )
    record, output = registry.execute(call)

    assert record.status == "success"
    payload = json.loads(output)
    assert payload["found"] is False


def test_evidence_tool_uses_bounded_payload_projection() -> None:
    evidence = _evidence().model_copy(
        update={
            "payload": {
                "rule": "null_spike",
                "column": "income",
                "delta": 0.2,
                "credentials": "private-evidence-value",
                "local_path": "/home/private/raw.csv",
            }
        }
    )
    registry = ToolRegistry(evidence_catalog={evidence.evidence_id: evidence})
    record, output = registry.execute(
        ToolCall(
            id="bounded-evidence",
            function=ToolCallFunction(
                name="get_incident_evidence",
                arguments=json.dumps({"evidence_id": evidence.evidence_id}),
            ),
        )
    )

    assert record.status == "success"
    assert json.loads(output)["payload"] == {
        "rule": "null_spike",
        "column": "income",
        "delta": 0.2,
    }
    assert "private-evidence-value" not in output
    assert "/home/private" not in output


def test_tool_registry_does_not_fabricate_unconfigured_observations() -> None:
    registry = ToolRegistry()
    assert [tool.function.name for tool in registry.definitions] == [
        "get_incident_evidence"
    ]
    for name in ("compare_profiles", "inspect_dbt_impact"):
        record, output = registry.execute(
            ToolCall(
                id="unavailable",
                function=ToolCallFunction(name=name, arguments="{}"),
            )
        )
        assert record.status == "error"
        assert "unavailable capability" in output


def test_tool_registry_preserves_configured_impact_observation() -> None:
    registry = ToolRegistry(
        impact_handler=lambda args: {"asset_name": args["asset_name"], "models": []}
    )
    record, output = registry.execute(
        ToolCall(
            id="call_3",
            function=ToolCallFunction(
                name="inspect_dbt_impact",
                arguments=json.dumps({"asset_name": "unrelated.asset"}),
            ),
        )
    )

    assert record.status == "success"
    assert json.loads(output) == {"asset_name": "unrelated.asset", "models": []}


def test_profile_tool_compares_bound_incident_snapshot(
    null_spike_review_material: NullSpikeReviewMaterial,
) -> None:
    material = null_spike_review_material
    evidence = material.detection.evidence.model_copy(
        update={
            "payload": {
                **material.detection.evidence.payload,
                "snapshot_id": "incident-profile",
                "baseline_snapshot_id": "baseline-profile",
                "current_snapshot_id": "current-profile",
            }
        }
    )
    review_input = AgenticReviewInput(
        incident=material.detection.incident,
        evidence=[evidence],
        draft=material.draft,
        project_revision="profile-tool-test",
    )
    registry = ToolRegistry.from_review_input(review_input)
    record, output = registry.execute(
        ToolCall(
            id="compare",
            function=ToolCallFunction(name="compare_profiles", arguments="{}"),
        )
    )
    payload = json.loads(output)
    assert record.status == "success"
    assert payload["baseline_null_rate"] == 0.01
    assert payload["current_null_rate"] == 0.21
    assert payload["delta"] == pytest.approx(0.2)
    assert payload["column"] == "income"
    assert payload["provenance"]["kind"] == "incident_snapshot"
    assert (
        payload["provenance"]["evidence_id"] == material.detection.evidence.evidence_id
    )
    assert payload["provenance"]["snapshot_id"] == "incident-profile"
    assert payload["provenance"]["baseline_snapshot_id"] == "baseline-profile"
    assert payload["provenance"]["current_snapshot_id"] == "current-profile"
    rejected, _ = registry.execute(
        ToolCall(
            id="unrelated-column",
            function=ToolCallFunction(
                name="compare_profiles", arguments='{"column":"unrelated"}'
            ),
        )
    )
    assert rejected.status == "error"


def test_profile_snapshot_reference_cannot_bypass_response_bound(
    null_spike_review_material: NullSpikeReviewMaterial,
) -> None:
    material = null_spike_review_material
    evidence = material.detection.evidence.model_copy(
        update={
            "payload": {
                **material.detection.evidence.payload,
                "snapshot_id": "snapshot-" + "x" * 2048,
            }
        }
    )
    registry = ToolRegistry.from_review_input(
        AgenticReviewInput(
            incident=material.detection.incident,
            evidence=[evidence],
            draft=material.draft,
            project_revision="bounded-snapshot-reference",
        )
    )
    record, output = registry.execute(
        ToolCall(
            id="oversized-snapshot",
            function=ToolCallFunction(name="compare_profiles", arguments="{}"),
        )
    )
    assert record.status == "error"
    assert json.loads(output)["error"] == "tool_execution_failed"
    assert "snapshot-" not in output


def test_tool_registry_blocks_disallowed_configured_tool() -> None:
    registry = ToolRegistry(
        evidence_catalog={"ev_test_1": _evidence()}, allowed_tools=()
    )
    assert registry.definitions == ()
    record, _ = registry.execute(
        ToolCall(
            id="denied",
            function=ToolCallFunction(
                name="get_incident_evidence", arguments='{"evidence_id":"ev_test_1"}'
            ),
        )
    )
    assert record.status == "error"
    assert "payload" not in record.result


def test_dbt_tool_analyzes_bound_artifact_projection(
    null_spike_review_material: NullSpikeReviewMaterial,
    tmp_path: Path,
) -> None:
    material = null_spike_review_material
    review_input = AgenticReviewInput(
        incident=material.detection.incident,
        evidence=[material.detection.evidence],
        draft=material.draft,
        project_revision="dbt-tool-test",
    )
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "sources": {
                    "source.test.hmda_loans": {
                        "name": "hmda_loans",
                        "schema": "raw",
                    }
                },
                "nodes": {
                    "model.test.staging": {
                        "name": "staging",
                        "depends_on": {"nodes": ["source.test.hmda_loans"]},
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    run_results_path = tmp_path / "run_results.json"
    run_results_path.write_text("{}", encoding="utf-8")
    registry = ToolRegistry.from_review_input(
        review_input, dbt_artifact_paths=(manifest_path, run_results_path)
    )
    call = ToolCall(
        id="impact",
        function=ToolCallFunction(
            name="inspect_dbt_impact",
            arguments=json.dumps({"asset_name": review_input.incident.asset_name}),
        ),
    )
    record, output = registry.execute(call)
    payload = json.loads(output)
    assert record.status == "success"
    assert payload["downstream_assets"] == ["staging"]
    assert payload["provenance"]["kind"] == "current_artifact_projection"
    assert payload["provenance"]["projection_id"] == artifact_projection_id(
        manifest_path, run_results_path
    )
    assert str(tmp_path) not in output
    assert payload["impact_status"] == "downstream_observed"
    rejected, _ = registry.execute(
        call.model_copy(
            update={
                "function": ToolCallFunction(
                    name="inspect_dbt_impact", arguments='{"asset_name":"unrelated"}'
                )
            }
        )
    )
    assert rejected.status == "error"
    run_results_path.unlink()
    missing, _ = registry.execute(call)
    assert missing.status == "error"
    assert "downstream_assets" not in missing.result
    assert str(tmp_path) not in json.dumps(missing.result)


def test_dbt_empty_downstream_does_not_claim_verified_no_impact(
    null_spike_review_material: NullSpikeReviewMaterial, tmp_path: Path
) -> None:
    material = null_spike_review_material
    manifest = tmp_path / "manifest.json"
    results = tmp_path / "run_results.json"
    manifest.write_text('{"sources":{},"nodes":{}}', encoding="utf-8")
    results.write_text("{}", encoding="utf-8")
    review_input = AgenticReviewInput(
        incident=material.detection.incident,
        evidence=[material.detection.evidence],
        draft=material.draft,
        project_revision="empty-impact",
    )
    registry = ToolRegistry.from_review_input(
        review_input, dbt_artifact_paths=(manifest, results)
    )
    record, output = registry.execute(
        ToolCall(
            id="empty-impact",
            function=ToolCallFunction(
                name="inspect_dbt_impact",
                arguments=json.dumps({"asset_name": review_input.incident.asset_name}),
            ),
        )
    )
    assert record.status == "success"
    assert json.loads(output)["impact_status"] == "unresolved_or_leaf"
    assert json.loads(output)["downstream_assets"] == []


@pytest.mark.parametrize(
    ("name", "arguments"),
    [
        ("get_incident_evidence", {"evidence_id": "ev_test_1", "extra": True}),
        ("get_incident_evidence", {"evidence_id": 1}),
        ("inspect_dbt_impact", {}),
        ("inspect_dbt_impact", {"asset_name": " "}),
        ("compare_profiles", {"column": ["income"]}),
        ("compare_profiles", {"sql": "select 1"}),
    ],
)
def test_tool_registry_rejects_schema_violations(
    name: str, arguments: dict[str, object]
) -> None:
    registry = ToolRegistry(
        evidence_catalog={"ev_test_1": _evidence()},
        profile_comparison_handler=lambda args: {"unexpected": True},
        impact_handler=lambda args: {"unexpected": True},
    )
    record, _ = registry.execute(
        ToolCall(
            id="invalid",
            function=ToolCallFunction(name=name, arguments=json.dumps(arguments)),
        )
    )
    assert record.status == "error"
    assert "unexpected" not in record.result


def test_tool_registry_handles_invalid_json_arguments() -> None:
    registry = ToolRegistry()
    call = ToolCall(
        id="call_4",
        function=ToolCallFunction(
            name="get_incident_evidence",
            arguments="invalid json",
        ),
    )
    record, output = registry.execute(call)

    assert record.status == "error"
    assert "invalid_arguments" in output


def test_tool_registry_handles_unknown_tool() -> None:
    registry = ToolRegistry()
    call = ToolCall(
        id="call_5",
        function=ToolCallFunction(
            name="unknown_arbitrary_tool",
            arguments="{}",
        ),
    )
    record, output = registry.execute(call)

    assert record.status == "error"
    assert "unknown tool" in output


def test_tool_registry_rejects_excessively_nested_arguments() -> None:
    registry = ToolRegistry()
    nested_json = "[" * 16000 + "0" + "]" * 16000
    record, output = registry.execute(
        ToolCall(
            id="nested",
            function=ToolCallFunction(
                name="get_incident_evidence", arguments=nested_json
            ),
        )
    )
    assert record.status == "error"
    assert "invalid_arguments" in output
