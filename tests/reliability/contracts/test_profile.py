"""Profile contract tests."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from project_pivot.reliability.contracts import (
    FreshnessMeasurementStatus,
    ProfileSnapshot,
)

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
            freshness_status=FreshnessMeasurementStatus.MEASURED,
        )


@pytest.mark.parametrize(
    ("freshness_at", "freshness_status"),
    [
        (None, FreshnessMeasurementStatus.MEASURED),
        (
            datetime(2026, 6, 6, 0, 0, tzinfo=UTC),
            FreshnessMeasurementStatus.UNAVAILABLE,
        ),
    ],
)
def test_profile_snapshot_rejects_inconsistent_freshness_fields(
    freshness_at: datetime | None,
    freshness_status: FreshnessMeasurementStatus,
) -> None:
    observed_at = datetime(2026, 6, 6, 0, 0, tzinfo=UTC)

    with pytest.raises(ValidationError, match="freshness"):
        ProfileSnapshot(
            snapshot_id="profile_invalid_freshness",
            asset_name="raw.hmda_loans",
            partition="2025",
            observed_at=observed_at,
            row_count=1,
            null_rates={},
            schema_hash="sha256:synthetic-schema",
            freshness_at=freshness_at,
            freshness_status=freshness_status,
        )


def test_profile_snapshot_serializes_unavailable_freshness() -> None:
    snapshot = ProfileSnapshot(
        snapshot_id="profile_unavailable_freshness",
        asset_name="raw.hmda_loans",
        partition="2025",
        observed_at=datetime(2026, 6, 6, 0, 0, tzinfo=UTC),
        row_count=0,
        null_rates={},
        schema_hash="sha256:synthetic-schema",
        freshness_at=None,
        freshness_status=FreshnessMeasurementStatus.UNAVAILABLE,
    )

    assert snapshot.model_dump(mode="json")["freshness_status"] == "unavailable"
    assert snapshot.model_dump(mode="json")["freshness_at"] is None


def test_profile_snapshot_normalizes_measured_timestamp_to_utc() -> None:
    snapshot = ProfileSnapshot(
        snapshot_id="profile_measured_freshness",
        asset_name="raw.hmda_loans",
        partition="2025",
        observed_at=datetime(2026, 6, 6, 0, 0),
        row_count=1,
        null_rates={},
        schema_hash="sha256:synthetic-schema",
        freshness_at=datetime(2026, 6, 5, 23, 30),
        freshness_status=FreshnessMeasurementStatus.MEASURED,
    )

    assert snapshot.observed_at.tzinfo is UTC
    assert snapshot.freshness_at is not None
    assert snapshot.freshness_at.tzinfo is UTC
