"""HMDA 원천 EDA 계산 contract와 확장 계획.

Contract:
    - 기존 schema, volume, null, freshness evidence key를 유지한다.
    - 핵심 code distribution, numeric summary, anomaly, grain evidence를
      JSON-serializable한 read-only 결과로 제공한다.
    - unknown/suspicious raw value를 보존하고 observation으로만 노출한다.

Risks:
    - 새 evidence 계산이 기존 결과를 깨거나 원천을 변경할 수 있다.
    - distribution population, quantile, anomaly share의 분모가 어긋날 수 있다.
    - missing column과 query failure에서 partial evidence가 노출될 수 있다.

Scope:
    Component-level public entrypoint behavior. Notebook rendering, actual-source
    observation, resource budget은 각각 독립 validation surface에서 검증한다.

Planning:
    ``_plan_*`` 함수는 pytest가 수집하지 않는 test design이다. Production
    implementation과 함께 실행 가능한 ``test_*`` 함수로 전환한다.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import duckdb
import pytest

from project_pivot.hmda_data import analyze_hmda_csv
from project_pivot.hmda_data.errors import HMDADataValidationError

pytestmark = pytest.mark.component


def _plan_returns_core_code_distributions() -> None:
    """유효한 source의 핵심 code별 count/share를 검증한다.

    Setup:
        Null과 반복 code를 포함한 작은 CSV를 사용한다.
    Observable result:
        ``action_taken``, ``loan_purpose``, ``state_code``의 observed value별
        count/share가 반환되고 count 합이 명시된 analysis population과 같다.
    Oracle:
        입력 row를 직접 세어 만든 exact count와 단순 비율을 비교한다.
    """
    raise NotImplementedError


def _plan_preserves_unknown_codes_as_observations() -> None:
    """허용 목록 밖 code가 raw 보존형 anomaly로 기록되는지 검증한다.

    Observable result:
        Unknown value와 count가 anomaly evidence에 남고 전체 row count와
        distribution count가 줄지 않는다.
    Exclusion:
        Unknown value의 domain 의미나 정제 규칙은 이 test가 결정하지 않는다.
    """
    raise NotImplementedError


def _plan_returns_numeric_summaries_without_clipping() -> None:
    """대상 numeric field의 non-null count와 five-number summary를 검증한다.

    Setup:
        Null, 음수 income, zero amount, extreme value를 포함한 고정 입력을 쓴다.
    Observable result:
        ``loan_amount``와 ``income`` 각각의 non-null count, min, p25, median,
        p75, max가 반환되며 extreme raw value가 summary에서 제거되지 않는다.
    Oracle:
        DuckDB 구현을 복제하지 않고 소수의 정렬된 고정 값으로 expected
        quantile을 명시한다.
    """
    raise NotImplementedError


def _plan_reports_suspicious_numeric_observations() -> None:
    """Configured suspicious condition의 field/condition/count/share를 검증한다.

    Observable result:
        ``income < 0``과 ``loan_amount <= 0`` observation이 독립적으로
        직렬화되고 원천 row 삭제, clipping, incident 생성은 발생하지 않는다.
    """
    raise NotImplementedError


def _plan_returns_mart_grain_alignment_evidence() -> None:
    """현재 mart grain의 aggregate count와 key coverage를 검증한다.

    Observable result:
        ``activity_year + state_code + loan_purpose`` grouping별 row count와
        grain key null/coverage 상태가 반환되고 aggregate 합이 전체 row와 같다.
    Boundary:
        EDA는 새로운 canonical grain이나 mart grouping rule을 정의하지 않는다.
    """
    raise NotImplementedError


def _plan_rejects_missing_descriptive_column_without_partial_evidence() -> None:
    """필수 descriptive field 누락이 명시적으로 실패하는지 검증한다.

    Observable result:
        Public validation exception이 발생하고 evidence 반환, 원천 변경,
        열린 DuckDB connection이 남지 않는다.
    """
    raise NotImplementedError


def _plan_preserves_existing_evidence_contract() -> None:
    """확장 후에도 기존 evidence key와 read-only regression을 보호한다.

    Observable result:
        기존 baseline assertions, JSON serialization, source byte equality,
        success/failure connection close가 새 evidence와 함께 유지된다.
    """
    raise NotImplementedError


def test_analyze_hmda_csv_returns_baseline_evidence(tmp_path: Path) -> None:
    """작은 원천 CSV의 baseline evidence 계약을 고정한다."""

    source_path = tmp_path / "hmda.csv"
    source_path.write_text(
        "\n".join(
            [
                "activity_year,state_code,county_code,loan_purpose,action_taken,loan_amount,income,observed_at",
                "2024,CA,06001,1,1,350000,120,2025-01-02T03:04:05",
                "2025,NY,unknown,31,3,420000,NA,2025-02-03T04:05:06",
                "2025,TX,48113,1,1,,95,",
            ]
        ),
        encoding="utf-8",
    )

    evidence = analyze_hmda_csv(
        source_path,
        memory_limit="256MB",
        threads=1,
        temp_directory=tmp_path / "duckdb-temp",
        max_activity_years=4,
    )

    assert evidence["row_count"] == 3
    assert evidence["activity_year_counts"] == [
        {"activity_year": 2024, "row_count": 1},
        {"activity_year": 2025, "row_count": 2},
    ]
    assert evidence["null_counts"] == {
        "activity_year": 0,
        "state_code": 0,
        "county_code": 0,
        "loan_purpose": 0,
        "action_taken": 0,
        "loan_amount": 1,
        "income": 1,
    }
    assert evidence["null_rates"]["loan_amount"] == pytest.approx(1 / 3)
    assert evidence["null_rates"]["income"] == pytest.approx(1 / 3)
    assert evidence["schema"]["required_columns"] == [
        {
            "column": "activity_year",
            "inferred_type": "BIGINT",
            "status": "valid",
        },
        {"column": "state_code", "inferred_type": "VARCHAR", "status": "valid"},
        {
            "column": "county_code",
            "inferred_type": "VARCHAR",
            "status": "valid",
        },
        {
            "column": "loan_purpose",
            "inferred_type": "BIGINT",
            "status": "valid",
        },
        {
            "column": "action_taken",
            "inferred_type": "BIGINT",
            "status": "valid",
        },
        {
            "column": "loan_amount",
            "inferred_type": "BIGINT",
            "status": "valid",
        },
        {"column": "income", "inferred_type": "BIGINT", "status": "valid"},
    ]
    assert evidence["freshness"] == {
        "status": "measured",
        "source_column": "observed_at",
        "freshness_at": "2025-02-03T04:05:06",
        "boundary": {
            "file_mtime": "filesystem metadata; not source freshness",
            "bronze_ingested_at": "ingestion time from separate raw-table EDA path",
        },
    }
    assert evidence["source"]["path"] == str(source_path.resolve())
    assert evidence["source"]["scope"] == "full_file"
    assert evidence["source"]["csv_options"] == {
        "header": True,
        "nullstr": ["NA", ""],
        "sample_size": 200_000,
    }
    assert evidence["source"]["duckdb_config"] == {
        "memory_limit": "256MB",
        "threads": 1,
        "temp_directory": str((tmp_path / "duckdb-temp").resolve()),
    }
    json.dumps(evidence)


def test_analyze_hmda_csv_fails_without_partial_evidence_and_closes_connection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """CSV parse 실패가 원천을 바꾸지 않고 connection을 닫는지 확인한다."""

    source_path = tmp_path / "malformed.csv"
    source_path.write_bytes(
        b"activity_year,state_code,county_code,loan_purpose,action_taken,"
        b"loan_amount,income\n2025,CA,06001,1,1,350000,\xff\n"
    )
    source_before = source_path.read_bytes()
    connection_closed = False
    real_connect = duckdb.connect

    class TrackingConnection:
        def __init__(self, connection: duckdb.DuckDBPyConnection) -> None:
            self.connection = connection

        def __getattr__(self, name: str) -> Any:
            return getattr(self.connection, name)

        def close(self) -> None:
            nonlocal connection_closed
            connection_closed = True
            self.connection.close()

    def tracking_connect(*args: Any, **kwargs: Any) -> TrackingConnection:
        return TrackingConnection(real_connect(*args, **kwargs))

    monkeypatch.setattr(
        "project_pivot.hmda_data.eda.analysis.duckdb.connect", tracking_connect
    )

    with pytest.raises(duckdb.Error):
        analyze_hmda_csv(
            source_path,
            temp_directory=tmp_path / "duckdb-temp",
        )

    assert connection_closed
    assert source_path.read_bytes() == source_before


def test_analyze_hmda_csv_closes_connection_without_changing_source(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """정상 실행도 connection을 닫고 원천 byte를 유지한다."""

    source_path = tmp_path / "valid.csv"
    source_path.write_text(
        "\n".join(
            [
                "activity_year,state_code,county_code,loan_purpose,action_taken,loan_amount,income",
                "2025,CA,06001,1,1,350000,120",
            ]
        ),
        encoding="utf-8",
    )
    source_before = source_path.read_bytes()
    connection_closed = False
    real_connect = duckdb.connect

    class TrackingConnection:
        def __init__(self, connection: duckdb.DuckDBPyConnection) -> None:
            self.connection = connection

        def __getattr__(self, name: str) -> Any:
            return getattr(self.connection, name)

        def close(self) -> None:
            nonlocal connection_closed
            connection_closed = True
            self.connection.close()

    def tracking_connect(*args: Any, **kwargs: Any) -> TrackingConnection:
        return TrackingConnection(real_connect(*args, **kwargs))

    monkeypatch.setattr(
        "project_pivot.hmda_data.eda.analysis.duckdb.connect", tracking_connect
    )

    evidence = analyze_hmda_csv(
        source_path,
        temp_directory=tmp_path / "duckdb-temp",
    )

    assert evidence["row_count"] == 1
    assert connection_closed
    assert source_path.read_bytes() == source_before


def test_analyze_hmda_csv_closes_connection_after_query_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Aggregate query 실패를 전달한 뒤에도 connection을 닫는다."""

    source_path = tmp_path / "valid.csv"
    source_path.write_text(
        "\n".join(
            [
                "activity_year,state_code,county_code,loan_purpose,action_taken,loan_amount,income",
                "2025,CA,06001,1,1,350000,120",
            ]
        ),
        encoding="utf-8",
    )
    connection_closed = False
    real_connect = duckdb.connect

    class FailingConnection:
        def __init__(self, connection: duckdb.DuckDBPyConnection) -> None:
            self.connection = connection

        def __getattr__(self, name: str) -> Any:
            return getattr(self.connection, name)

        def execute(self, *_args: Any, **_kwargs: Any) -> None:
            raise duckdb.Error("aggregate query failed")

        def close(self) -> None:
            nonlocal connection_closed
            connection_closed = True
            self.connection.close()

    def failing_connect(*args: Any, **kwargs: Any) -> FailingConnection:
        return FailingConnection(real_connect(*args, **kwargs))

    monkeypatch.setattr(
        "project_pivot.hmda_data.eda.analysis.duckdb.connect", failing_connect
    )

    with pytest.raises(duckdb.Error, match="aggregate query failed"):
        analyze_hmda_csv(
            source_path,
            temp_directory=tmp_path / "duckdb-temp",
        )

    assert connection_closed


def test_analyze_hmda_csv_rejects_unbounded_activity_years(tmp_path: Path) -> None:
    """비정상적인 연도 cardinality를 bounded query 뒤 거부한다."""

    source_path = tmp_path / "many-years.csv"
    source_path.write_text(
        "\n".join(
            [
                "activity_year,state_code,county_code,loan_purpose,action_taken,loan_amount,income",
                "2023,CA,06001,1,1,350000,120",
                "2024,NY,36061,1,1,420000,95",
                "2025,TX,48113,1,1,250000,88",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(HMDADataValidationError, match="cardinality"):
        analyze_hmda_csv(
            source_path,
            temp_directory=tmp_path / "duckdb-temp",
            max_activity_years=2,
        )


def test_analyze_hmda_csv_rejects_missing_input(tmp_path: Path) -> None:
    """없는 원천은 DuckDB connection 생성 전에 실패한다."""

    with pytest.raises(FileNotFoundError, match="does not exist"):
        analyze_hmda_csv(
            tmp_path / "missing.csv",
            temp_directory=tmp_path / "duckdb-temp",
        )
