"""HMDA EDA deterministic fixture와 expected-value contract.

Contract:
    - 같은 seed와 row count는 같은 fixture와 manifest evidence를 만든다.
    - Manifest는 distribution, numeric summary, anomaly, grain oracle을 소유한다.
    - Evidence validation은 manifest의 모든 deterministic invariant를 확인한다.

Risks:
    - Fixture generator와 expected manifest가 함께 잘못되어 self-confirming test가
      될 수 있다.
    - 실제 source observation이 fixture의 immutable assertion으로 굳을 수 있다.

Scope:
    Small deterministic fixture correctness only. Actual-source values와
    process memory budget은 포함하지 않는다.

Planning:
    ``_plan_*`` 함수는 pytest 수집 전 test design이며 구현 시 executable
    ``test_*`` 함수와 독립적인 expected values로 교체한다.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from project_pivot.hmda_data.eda import (
    FIXTURE_VERSION,
    MANIFEST_FILE_NAME,
    analyze_hmda_csv,
    prepare_hmda_eda_fixture,
    validate_hmda_eda_evidence,
    validate_hmda_eda_fixture,
)
from project_pivot.hmda_data.errors import HMDADataValidationError

pytestmark = pytest.mark.component


def _plan_fixture_declares_descriptive_expected_values() -> None:
    """Manifest가 새 descriptive evidence의 독립 oracle을 제공하도록 설계한다.

    Observable result:
        고정 fixture manifest에 code distribution, numeric summary, suspicious
        condition count/share, grain aggregate와 coverage expected value가 있다.
    Oracle:
        소수의 의도적으로 배치한 row에서 손으로 판정 가능한 exact value를 쓴다.
    """
    raise NotImplementedError


def _plan_fixture_contains_unknown_and_suspicious_values() -> None:
    """Fixture가 preservation/anomaly scenario를 실제 row로 포함하는지 검증한다.

    Observable result:
        Unknown code, negative income, nonpositive loan amount가 manifest에 선언된
        횟수만큼 존재하며 원천 값 자체도 확인 가능하다.
    """
    raise NotImplementedError


def _plan_evidence_validation_checks_descriptive_contract() -> None:
    """Evidence validator가 새 manifest invariant 전체를 검사하도록 설계한다.

    Scenario:
        Valid evidence는 통과하고 distribution, numeric summary, anomaly, grain
        값을 하나씩 변조하면 해당 contract를 식별하는 validation error가 난다.
    Boundary:
        Production 계산을 재실행해 expected value를 만들지 않는다.
    """
    raise NotImplementedError


def _plan_fixture_contract_excludes_actual_source_observations() -> None:
    """실제 source의 변동 가능한 관찰값이 manifest에 고정되지 않음을 검증한다.

    Observable result:
        Manifest schema와 fixture assertions는 source path, 실행 시점, 실제 전체
        분포나 extreme value를 required expected field로 취급하지 않는다.
    """
    raise NotImplementedError


def test_prepare_hmda_eda_fixture_is_deterministic(tmp_path: Path) -> None:
    """작은 대표 fixture가 고정 manifest와 hash를 만드는지 검증한다."""

    first_directory = tmp_path / "first"
    second_directory = tmp_path / "second"

    first = prepare_hmda_eda_fixture(first_directory, row_count=100, seed=7)
    second = prepare_hmda_eda_fixture(second_directory, row_count=100, seed=7)
    first_path, validated = validate_hmda_eda_fixture(first_directory)

    assert first.version == FIXTURE_VERSION
    assert first.row_count == 100
    assert first.activity_year_cardinality == 3
    assert first.activity_year_skew == {"2023": 0.1, "2024": 0.2, "2025": 0.7}
    assert first.null_rates == {
        "activity_year": 0.0,
        "state_code": 0.0,
        "county_code": 0.0,
        "loan_purpose": 0.0,
        "action_taken": 0.0,
        "loan_amount": 0.02,
        "income": 0.05,
    }
    assert [item.model_dump() for item in first.expected.activity_year_counts] == [
        {"activity_year": 2023, "row_count": 10},
        {"activity_year": 2024, "row_count": 20},
        {"activity_year": 2025, "row_count": 70},
    ]
    assert first.files[0].sha256 == second.files[0].sha256
    assert validated == first
    assert first_path.is_file()


def _rewrite_manifest(
    tmp_path: Path,
    update: Callable[[dict[str, Any]], object],
) -> None:
    manifest_path = tmp_path / MANIFEST_FILE_NAME
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    update(payload)
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")


def test_validate_hmda_eda_fixture_rejects_missing_required_field(
    tmp_path: Path,
) -> None:
    prepare_hmda_eda_fixture(tmp_path, row_count=10)
    _rewrite_manifest(tmp_path, lambda payload: payload.pop("seed"))

    with pytest.raises(HMDADataValidationError, match="Invalid fixture manifest"):
        validate_hmda_eda_fixture(tmp_path)


def test_validate_hmda_eda_fixture_rejects_unknown_field(tmp_path: Path) -> None:
    prepare_hmda_eda_fixture(tmp_path, row_count=10)
    _rewrite_manifest(tmp_path, lambda payload: payload.update(unknown=True))

    with pytest.raises(HMDADataValidationError, match="extra_forbidden"):
        validate_hmda_eda_fixture(tmp_path)


def test_validate_hmda_eda_fixture_rejects_file_count_mismatch(
    tmp_path: Path,
) -> None:
    prepare_hmda_eda_fixture(tmp_path, row_count=10)
    _rewrite_manifest(tmp_path, lambda payload: payload.update(file_count=2))

    with pytest.raises(HMDADataValidationError, match="file_count"):
        validate_hmda_eda_fixture(tmp_path)


def test_validate_hmda_eda_fixture_rejects_incomplete_null_counts(
    tmp_path: Path,
) -> None:
    prepare_hmda_eda_fixture(tmp_path, row_count=10)
    _rewrite_manifest(
        tmp_path,
        lambda payload: payload["expected"]["required_column_null_counts"].pop(
            "activity_year"
        ),
    )

    with pytest.raises(HMDADataValidationError, match="required_column_null_counts"):
        validate_hmda_eda_fixture(tmp_path)


def test_validate_hmda_eda_fixture_rejects_negative_null_rate(
    tmp_path: Path,
) -> None:
    prepare_hmda_eda_fixture(tmp_path, row_count=10)
    _rewrite_manifest(
        tmp_path,
        lambda payload: payload["null_rates"].update(income=-0.1),
    )

    with pytest.raises(HMDADataValidationError, match="null rates"):
        validate_hmda_eda_fixture(tmp_path)


def test_validate_hmda_eda_fixture_rejects_inconsistent_row_count(
    tmp_path: Path,
) -> None:
    prepare_hmda_eda_fixture(tmp_path, row_count=10)
    _rewrite_manifest(
        tmp_path,
        lambda payload: payload["expected"].update(row_count=11),
    )

    with pytest.raises(HMDADataValidationError, match="expected row count"):
        validate_hmda_eda_fixture(tmp_path)


def test_validate_hmda_eda_fixture_rejects_inconsistent_activity_year_contract(
    tmp_path: Path,
) -> None:
    prepare_hmda_eda_fixture(tmp_path, row_count=10)
    _rewrite_manifest(
        tmp_path,
        lambda payload: payload.update(activity_year_cardinality=2),
    )

    with pytest.raises(HMDADataValidationError, match="activity-year cardinality"):
        validate_hmda_eda_fixture(tmp_path)


@pytest.mark.parametrize(
    "skew",
    [
        {"2023": -0.1, "2024": 0.2, "2025": 0.9},
        {"2023": 0.1, "2024": 0.2, "2025": 0.6},
    ],
)
def test_validate_hmda_eda_fixture_rejects_invalid_skew(
    tmp_path: Path,
    skew: dict[str, float],
) -> None:
    prepare_hmda_eda_fixture(tmp_path, row_count=10)
    _rewrite_manifest(
        tmp_path,
        lambda payload: payload.update(activity_year_skew=skew),
    )

    with pytest.raises(HMDADataValidationError, match="activity-year skew"):
        validate_hmda_eda_fixture(tmp_path)


def test_validate_hmda_eda_fixture_rejects_changed_file(tmp_path: Path) -> None:
    """Manifest 생성 뒤 변경된 fixture를 유효한 workload로 인정하지 않는다."""

    prepare_hmda_eda_fixture(tmp_path, row_count=10)
    fixture_path, _ = validate_hmda_eda_fixture(tmp_path)
    fixture_path.write_text("changed", encoding="utf-8")

    with pytest.raises(HMDADataValidationError, match="size|hash"):
        validate_hmda_eda_fixture(tmp_path)


def test_validate_hmda_eda_fixture_rejects_missing_manifest(tmp_path: Path) -> None:
    """Manifest가 없으면 memory workload preflight를 실패시킨다."""

    with pytest.raises(HMDADataValidationError, match="manifest does not exist"):
        validate_hmda_eda_fixture(tmp_path)


def test_validate_hmda_eda_evidence_checks_all_required_columns(
    tmp_path: Path,
) -> None:
    manifest = prepare_hmda_eda_fixture(tmp_path, row_count=100, seed=7)
    fixture_path, _ = validate_hmda_eda_fixture(tmp_path)
    evidence = analyze_hmda_csv(
        fixture_path,
        temp_directory=tmp_path / "duckdb-temp",
    )

    validate_hmda_eda_evidence(evidence, manifest)
    evidence["null_counts"].pop("activity_year")

    with pytest.raises(HMDADataValidationError, match="all required columns"):
        validate_hmda_eda_evidence(evidence, manifest)


def test_validate_hmda_eda_evidence_checks_null_rate_and_freshness(
    tmp_path: Path,
) -> None:
    manifest = prepare_hmda_eda_fixture(tmp_path, row_count=100, seed=7)
    fixture_path, _ = validate_hmda_eda_fixture(tmp_path)
    evidence = analyze_hmda_csv(
        fixture_path,
        temp_directory=tmp_path / "duckdb-temp",
    )
    evidence["null_rates"]["income"] = 0.0

    with pytest.raises(HMDADataValidationError, match="null rate"):
        validate_hmda_eda_evidence(evidence, manifest)

    evidence["null_rates"]["income"] = manifest.null_rates["income"]
    evidence["freshness"]["status"] = "unmeasured"

    with pytest.raises(HMDADataValidationError, match="freshness"):
        validate_hmda_eda_evidence(evidence, manifest)
