"""orchestration quality gate 단위 및 통합 테스트."""

from __future__ import annotations

import importlib
import logging
from pathlib import Path

import duckdb
import pytest

from hmda_reliability.data_operations import DataOperationRequest
from hmda_reliability.orchestration.quality_gate import (
    QualityGateError,
    evaluate_quality_gate,
)

pytestmark = pytest.mark.integration

_CLEAN_NULL_RATES = {"income": 0.002, "loan_amount": 0.0}
_ANOMALOUS_NULL_RATE = 0.4  # income Null 40% → null_spike 탐지


def _make_db_with_partition(
    tmp_path: Path,
    null_rate: float,
    year: int = 2025,
    n_rows: int = 1000,
) -> Path:
    """테스트용 DuckDB 파일을 생성하고 raw.hmda_loans 파티션을 삽입한다."""

    db_path = tmp_path / f"test_{year}_{int(null_rate * 100)}.duckdb"
    null_count = int(n_rows * null_rate)

    con = duckdb.connect(str(db_path))
    con.execute("CREATE SCHEMA IF NOT EXISTS raw")
    con.execute(
        f"""
        CREATE TABLE raw.hmda_loans AS
        SELECT
            {year} AS activity_year,
            'CA' AS state_code,
            '001' AS county_code,
            1 AS loan_purpose,
            1 AS action_taken,
            200000 AS loan_amount,
            CASE
                WHEN row_number() OVER () <= {null_count} THEN NULL
                ELSE 80000
            END AS income,
            'year_{year}.csv' AS source_file,
            {year} AS source_year
        FROM range({n_rows})
        """
    )
    con.close()
    return db_path


def test_quality_gate_passes_when_no_anomaly_detected(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """정상 null rate 데이터에서 게이트가 통과하고 clean 로그가 남는다."""

    caplog.set_level(logging.INFO)
    db_path = _make_db_with_partition(tmp_path, null_rate=0.002)
    request = DataOperationRequest(
        database_path=db_path,
        source_year=2025,
    )

    evaluate_quality_gate(request)

    # Scenario: Quality gate evidence 검증
    assert any(
        "품질 게이트 통과" in record.message
        and "status=clean" in record.message
        or getattr(record, "status", None) == "clean"
        for record in caplog.records
    )


def test_quality_gate_raises_on_null_spike(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """null spike가 탐지되면 QualityGateError를 발생시키고 실패 로그가 남는다."""

    caplog.set_level(logging.WARNING)
    db_path = _make_db_with_partition(tmp_path, null_rate=_ANOMALOUS_NULL_RATE)
    request = DataOperationRequest(
        database_path=db_path,
        source_year=2025,
    )

    with pytest.raises(QualityGateError) as exc_info:
        evaluate_quality_gate(request)

    assert "null_spike(income)" in str(exc_info.value)
    assert exc_info.value.detected_incident_types == ["null_spike(income)"]

    # Scenario: Quality gate evidence 실패 로그 검증
    assert any(
        "품질 게이트 실패" in record.message
        or "null_spike(income)" in str(getattr(record, "detected_incident_types", ""))
        for record in caplog.records
    )


def test_quality_gate_ignores_volume_drop_by_design(tmp_path: Path) -> None:
    """MVP 범위에서 volume_drop은 baseline 저장소 부재로 비활성화되어 있다."""

    # row_count가 극단적으로 적어도 null rate가 정상(0.0)이면 통과해야 함
    db_path = _make_db_with_partition(tmp_path, null_rate=0.0, n_rows=5)
    request = DataOperationRequest(
        database_path=db_path,
        source_year=2025,
    )

    evaluate_quality_gate(request)  # volume_drop으로 실패하지 않아야 함


def test_quality_gate_rejects_unsupported_profile_columns(tmp_path: Path) -> None:
    """지원되지 않는 profile_columns 지정 시 ValueError를 발생시킨다."""

    db_path = _make_db_with_partition(tmp_path, null_rate=0.002)
    request = DataOperationRequest(
        database_path=db_path,
        source_year=2025,
        profile_columns=("loan_amount", "income", "loan_purpose"),
    )

    with pytest.raises(ValueError, match="baseline을 지원하지 않습니다.*loan_purpose"):
        evaluate_quality_gate(request)


def test_quality_gate_has_no_airflow_dependency() -> None:
    """quality_gate 모듈은 Airflow를 import하지 않는다."""

    module_name = "hmda_reliability.orchestration.quality_gate"
    quality_gate = importlib.import_module(module_name)
    module_file = quality_gate.__file__ or ""

    source = Path(module_file).read_text()
    assert "from airflow" not in source
    assert "import airflow" not in source
