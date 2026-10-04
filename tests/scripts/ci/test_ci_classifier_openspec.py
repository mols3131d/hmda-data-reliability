from __future__ import annotations

from pathlib import Path

import pytest

from tests.scripts.ci.helpers import run_classifier


@pytest.mark.unit
@pytest.mark.parametrize(
    ("spec_path", "expected_targets"),
    [
        (
            "openspec/specs/data-platform-dbt-analytics/spec.md",
            {"tests/dbt"},
        ),
        (
            "openspec/specs/orchestration-pipeline/spec.md",
            {
                "tests/orchestration",
                "tests/data_operations/test_quality_gate.py",
                "tests/data_operations/test_dbt_runner.py",
                "tests/reliability/test_quality_gate.py",
            },
        ),
        (
            "openspec/specs/reliability-agentic-review/spec.md",
            {"tests/review_ai", "tests/runtime_ai"},
        ),
    ],
)
def test_canonical_openspec_changes_select_executable_targets(
    spec_path: str,
    expected_targets: set[str],
) -> None:
    """Canonical Spec 변경은 구조 검증과 대응 executable test를 함께 선택한다."""
    out = run_classifier([spec_path])

    assert out["openspec"] == "true"
    assert out["openspec_bulk"] == "false"
    assert out["tests"] == "true"
    assert out["full_tests"] == "false"
    assert set(out["targets"].split()) == expected_targets


@pytest.mark.unit
def test_unknown_canonical_openspec_change_fails_safe_to_full_tests() -> None:
    """알 수 없는 신규 Spec capability는 executable validation을 생략하지 않는다."""
    out = run_classifier(["openspec/specs/new-capability/spec.md"])

    assert out["openspec"] == "true"
    assert out["openspec_bulk"] == "true"
    assert out["tests"] == "true"
    assert out["full_tests"] == "true"
    assert out["full_unit"] == "true"
    assert out["full_type"] == "true"


@pytest.mark.unit
def test_active_openspec_change_uses_affected_validation_target(
    openspec_repo: Path,
) -> None:
    """Active Change 변경은 해당 Change만 OpenSpec validation 대상으로 선택한다."""
    out = run_classifier(
        ["openspec/changes/orchestration-quality-gate/proposal.md"],
        repo_root=openspec_repo,
    )

    assert out["openspec"] == "true"
    assert out["openspec_bulk"] == "false"
    assert out["openspec_change_targets"].strip() == "orchestration-quality-gate"
    assert out["tests"] == "false"


@pytest.mark.unit
def test_archived_openspec_change_requests_archived_validation() -> None:
    """Archive 변경은 전체 active item 대신 archived validation을 선택한다."""
    out = run_classifier(
        [
            "openspec/changes/archive/2026-08-26-orchestration-pipeline-migrate-airflow/tasks.md"
        ]
    )

    assert out["openspec"] == "true"
    assert out["openspec_archived"] == "true"
    assert out["openspec_bulk"] == "false"
    assert out["openspec_change_targets"].strip() == ""
    assert out["tests"] == "false"


@pytest.mark.unit
def test_openspec_configuration_change_uses_bulk_validation() -> None:
    """OpenSpec configuration 변경은 bulk validation을 사용한다."""
    out = run_classifier(["openspec/config.yaml"])

    assert out["openspec"] == "true"
    assert out["openspec_bulk"] == "true"
    assert out["openspec_spec_targets"].strip() == ""
    assert out["openspec_change_targets"].strip() == ""


@pytest.mark.unit
def test_canonical_spec_selects_direct_active_change_validation(
    openspec_repo: Path,
) -> None:
    """Canonical Spec 변경은 같은 capability의 active Change도 검증한다."""
    out = run_classifier(
        ["openspec/specs/orchestration-pipeline/spec.md"], repo_root=openspec_repo
    )

    assert out["openspec_spec_targets"].strip() == "orchestration-pipeline"
    assert out["openspec_change_targets"].strip() == "orchestration-quality-gate"


@pytest.mark.unit
def test_canonical_spec_without_active_delta_keeps_change_targets_empty(
    openspec_repo: Path,
) -> None:
    """직접 연결된 active Change가 없으면 affected Spec만 유지한다."""
    out = run_classifier(
        ["openspec/specs/reliability-data-contracts/spec.md"], repo_root=openspec_repo
    )

    assert out["openspec_spec_targets"].strip() == "reliability-data-contracts"
    assert out["openspec_change_targets"].strip() == ""


@pytest.mark.unit
def test_mixed_canonical_spec_and_active_change_preserves_both_targets(
    openspec_repo: Path,
) -> None:
    """같은 change set의 Spec와 active Change target을 모두 중복 없이 보존한다."""
    out = run_classifier(
        [
            "openspec/specs/orchestration-pipeline/spec.md",
            "openspec/changes/orchestration-quality-gate/proposal.md",
        ],
        repo_root=openspec_repo,
    )

    assert out["openspec_spec_targets"].strip() == "orchestration-pipeline"
    assert out["openspec_change_targets"].strip() == "orchestration-quality-gate"
