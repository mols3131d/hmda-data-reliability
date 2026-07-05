"""Profile contract tests."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from project_pivot.reliability.contracts import ProfileSnapshot

pytestmark = pytest.mark.unit


def test_profile_snapshot_rejects_invalid_null_rate() -> None:
    """ProfileSnapshot이 허용 범위를 벗어난 null rate를 거부하는지 검증한다."""
    observed_at = datetime(2026, 6, 6, 0, 0, tzinfo=UTC)

    with pytest.raises(ValidationError):
        ProfileSnapshot(
            snapshot_id="profile_invalid",
            asset_name="mart.hmda_loan_outcomes",
            partition="2026-06-05",
            observed_at=observed_at,
            row_count=12_000,
            null_rates={"loan_amount": 1.2},
            schema_hash="sha256:synthetic-schema",
            freshness_at=observed_at,
        )
