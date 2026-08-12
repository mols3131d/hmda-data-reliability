"""Exact null-rate evidence regressions for post-recovery failures."""

from __future__ import annotations

from pathlib import Path

import pytest

import project_pivot.data_operations as data_operations
from project_pivot.data_operations import DataOperationRequest, LifecycleResult
from project_pivot.data_operations.errors import DataOperationError
from project_pivot.reliability import ProfileSnapshot
from tests.reliability.test_null_spike_evaluation import (
    _approved,
    _evaluate_null_spike,
    _null_spike_fixture,
)


def _assert_exact_null_rate_evidence(evidence_refs: list[str]) -> None:
    for rate in ("baseline", "recovery", "replay"):
        assert f"{rate}-null-rate:income:0.0" in evidence_refs


@pytest.mark.integration
def test_post_recovery_lifecycle_failure_keeps_exact_null_rate_evidence(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source_path, request = _null_spike_fixture(tmp_path)
    original_lifecycle = data_operations.run_incident_lifecycle
    lifecycle_count = 0

    def fail_post_recovery_lifecycle(
        lifecycle_request: DataOperationRequest,
        baseline: ProfileSnapshot,
    ) -> LifecycleResult:
        nonlocal lifecycle_count
        lifecycle_count += 1
        if lifecycle_count == 3:
            raise DataOperationError("post-recovery lifecycle failed")
        return original_lifecycle(lifecycle_request, baseline)

    monkeypatch.setattr(
        data_operations,
        "run_incident_lifecycle",
        fail_post_recovery_lifecycle,
    )

    result = _evaluate_null_spike(
        request=request,
        source_paths=(source_path,),
        workspace=tmp_path / "run",
        target_column="income",
        approve=_approved,
        validate_candidate=lambda _request: "sha256:candidate",
        validate_target=lambda _request: "sha256:target",
    )

    _assert_exact_null_rate_evidence(result.post_recovery_case.evidence_refs)


@pytest.mark.integration
@pytest.mark.parametrize("error_type", [DataOperationError, ValueError])
def test_target_validation_failure_keeps_exact_null_rate_evidence(
    tmp_path: Path,
    error_type: type[Exception],
) -> None:
    source_path, request = _null_spike_fixture(tmp_path)

    def fail_target(_request: DataOperationRequest) -> str:
        raise error_type("target validation failed")

    result = _evaluate_null_spike(
        request=request,
        source_paths=(source_path,),
        workspace=tmp_path / "run",
        target_column="income",
        approve=_approved,
        validate_candidate=lambda _request: "sha256:candidate",
        validate_target=fail_target,
    )

    _assert_exact_null_rate_evidence(result.post_recovery_case.evidence_refs)
