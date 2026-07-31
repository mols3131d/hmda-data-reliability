"""HMDA EDA representative fixture 테스트."""

from __future__ import annotations

from pathlib import Path

import pytest

from project_pivot.hmda_data.eda_fixture import (
    FIXTURE_VERSION,
    prepare_hmda_eda_fixture,
    validate_hmda_eda_fixture,
)
from project_pivot.hmda_data.errors import HMDADataValidationError

pytestmark = pytest.mark.component


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
    assert first.null_rates == {"loan_amount": 0.02, "income": 0.05}
    assert first.expected["activity_year_counts"] == [
        {"activity_year": 2023, "row_count": 10},
        {"activity_year": 2024, "row_count": 20},
        {"activity_year": 2025, "row_count": 70},
    ]
    assert first.files[0]["sha256"] == second.files[0]["sha256"]
    assert validated == first
    assert first_path.is_file()


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
