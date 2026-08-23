"""Freshness-bound recovery proposal contract tests."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from hmda_reliability.hmda_data import PartitionContentIdentity
from hmda_reliability.reliability import RecoveryProposal

pytestmark = pytest.mark.unit


def test_freshness_proposal_preserves_exact_temporal_binding() -> None:
    proposal = RecoveryProposal.model_validate(
        {
            **_base_payload(),
            "incident_type": "freshness_delay",
            "freshness_binding": {
                "approved_before": {
                    "freshness_status": "measured",
                    "freshness_at": "2026-08-15T07:00:00Z",
                    "observed_at": "2026-08-15T09:00:00Z",
                },
                "expected_after_freshness_at": "2026-08-15T09:00:00Z",
                "max_age_minutes": 60,
            },
        },
    )

    assert proposal.incident_type == "freshness_delay"
    assert proposal.freshness_binding is not None
    assert proposal.freshness_binding.approved_before.freshness_at == datetime(
        2026, 8, 15, 7, 0, tzinfo=UTC
    )


def test_freshness_proposal_requires_binding() -> None:
    with pytest.raises(ValidationError, match="freshness"):
        RecoveryProposal.model_validate(
            {**_base_payload(), "incident_type": "freshness_delay"}
        )


def test_content_proposal_forbids_freshness_binding() -> None:
    with pytest.raises(ValidationError, match="freshness"):
        RecoveryProposal.model_validate(
            {
                **_base_payload(),
                "incident_type": "volume_drop",
                "freshness_binding": {
                    "approved_before": {
                        "freshness_status": "measured",
                        "freshness_at": "2026-08-15T07:00:00Z",
                        "observed_at": "2026-08-15T09:00:00Z",
                    },
                    "expected_after_freshness_at": "2026-08-15T09:00:00Z",
                    "max_age_minutes": 60,
                },
            },
        )


def test_freshness_proposal_rejects_non_stale_before_observation() -> None:
    with pytest.raises(ValidationError, match="stale|max_age"):
        RecoveryProposal.model_validate(
            {
                **_base_payload(),
                "incident_type": "freshness_delay",
                "freshness_binding": {
                    "approved_before": {
                        "freshness_status": "measured",
                        "freshness_at": "2026-08-15T08:30:00Z",
                        "observed_at": "2026-08-15T09:00:00Z",
                    },
                    "expected_after_freshness_at": "2026-08-15T09:00:00Z",
                    "max_age_minutes": 60,
                },
            },
        )


def _base_payload() -> dict[str, object]:
    identity = PartitionContentIdentity(
        table_name="raw.hmda_loans",
        source_year=2025,
        row_count=2,
        digest="sha256-v1:content",
    )
    return {
        "proposal_id": "recovery_freshness_delay_2025",
        "incident_id": "inc_freshness_delay_2025",
        "table_name": "raw.hmda_loans",
        "source_year": 2025,
        "candidate_identity": identity,
        "approved_before_identity": identity,
        "expected_after_identity": identity,
        "validation_evidence_refs": ("candidate-content", "candidate-freshness"),
        "dbt_projection_id": "sha256:projection",
        "target_actions": ("overwrite_partition", "rerun_profile_snapshot"),
    }
