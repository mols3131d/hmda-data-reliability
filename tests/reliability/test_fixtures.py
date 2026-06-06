"""Serialization and fixture tests."""

from project_pivot.reliability.contracts import (
    HumanReviewStatus,
    can_execute_risky_action,
)


def test_synthetic_incident_fixture_has_required_contract_links(
    synthetic_incident_fixture,
) -> None:
    """Synthetic fixture가 incident/evidence/lineage 연결을 보존하는지 검증한다."""
    fixture = synthetic_incident_fixture

    assert fixture.incident.evidence_refs == [fixture.evidence.evidence_id]
    assert (
        fixture.incident.affected_assets == fixture.lineage_evidence.downstream_assets
    )
    assert fixture.incident.human_review_status is HumanReviewStatus.PENDING
    assert not can_execute_risky_action(fixture.approval)


def test_contracts_dump_to_json_stable_values(synthetic_incident_fixture) -> None:
    """Contract의 JSON 직렬화 값이 안정적인 문자열로 나오는지 검증한다."""
    fixture = synthetic_incident_fixture

    incident_json = fixture.incident.model_dump(mode="json")
    evidence_json = fixture.evidence.model_dump(mode="json")
    profile_json = fixture.profile_snapshot.model_dump(mode="json")

    assert incident_json["severity"] == "high"
    assert incident_json["status"] == "detected"
    assert incident_json["human_review_status"] == "pending"
    assert evidence_json["source"] == "profile"
    assert profile_json["freshness_at"] == "2026-06-06T00:00:00Z"
