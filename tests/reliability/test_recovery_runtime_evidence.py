"""Recovery runtime evidence tests."""

from __future__ import annotations

import logging
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import duckdb
import pytest

import hmda_reliability.reliability.recovery.executor as recovery_executor
from hmda_reliability.hmda_data.errors import HMDADataLoadError
from hmda_reliability.reliability import (
    ApprovedBackfillRequest,
    BackfillValidationError,
)


@pytest.mark.unit
def test_overwrite_boundary_is_recorded_before_storage_failure(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Storage failure 전 destructive overwrite 진입 evidence를 남긴다."""

    approved_before_identity = object()
    approval = SimpleNamespace(
        incident_id="inc-runtime-evidence",
        approval_id="approval-runtime-evidence",
    )
    proposal = SimpleNamespace(
        approved_before_identity=approved_before_identity,
        expected_after_identity=object(),
        freshness_binding=None,
    )
    request = SimpleNamespace(
        approval=approval,
        proposal=proposal,
        source_year=2025,
        source_file=None,
        table_name="raw.hmda_loans",
        profile_request=object(),
    )

    monkeypatch.setattr(
        recovery_executor,
        "_ensure_approved",
        lambda _request: _request,
    )
    monkeypatch.setattr(
        recovery_executor,
        "_stage_approved_candidate_source",
        lambda _request, _directory: Path("approved-candidate.parquet"),
    )
    monkeypatch.setattr(
        recovery_executor,
        "partition_content_identity",
        lambda *_args, **_kwargs: approved_before_identity,
    )

    def fail_target_load(*_args: object, **_kwargs: object) -> int:
        raise HMDADataLoadError("storage failed")

    monkeypatch.setattr(
        recovery_executor,
        "load_hmda_loans_partition",
        fail_target_load,
    )

    validator = recovery_executor.ApprovalBackfillValidator(
        cast(duckdb.DuckDBPyConnection, object())
    )
    with (
        caplog.at_level(logging.INFO, logger=recovery_executor.__name__),
        pytest.raises(BackfillValidationError, match="backfill validation"),
    ):
        validator.execute(cast(ApprovedBackfillRequest, request))

    overwrite_attempt_records = [
        record
        for record in caplog.records
        if record.getMessage() == "recovery partition overwrite attempt"
    ]
    assert len(overwrite_attempt_records) == 1
    overwrite_attempt_context = overwrite_attempt_records[0].__dict__
    assert overwrite_attempt_context["incident_id"] == "inc-runtime-evidence"
    assert overwrite_attempt_context["approval_id"] == "approval-runtime-evidence"
    assert overwrite_attempt_context["source_year"] == 2025
    assert overwrite_attempt_context["table_name"] == "raw.hmda_loans"
