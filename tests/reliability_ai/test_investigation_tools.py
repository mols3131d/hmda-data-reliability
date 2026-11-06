"""Tests for investigation read-only tools and tool registry."""

from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest

from hmda_reliability.reliability import Evidence, EvidenceSource
from hmda_reliability.reliability_ai.investigation.tools import (
    ToolRegistry,
)
from hmda_reliability.runtime_ai.contracts import ToolCall, ToolCallFunction

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


def test_tool_registry_dispatches_inspect_dbt_impact() -> None:
    registry = ToolRegistry()
    call = ToolCall(
        id="call_3",
        function=ToolCallFunction(
            name="inspect_dbt_impact",
            arguments=json.dumps({"asset_name": "raw.hmda_loans"}),
        ),
    )
    record, output = registry.execute(call)

    assert record.status == "success"
    payload = json.loads(output)
    assert "stg_hmda_loans" in payload["downstream_models"]


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
