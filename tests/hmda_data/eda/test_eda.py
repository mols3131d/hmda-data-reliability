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


def test_returns_core_code_distributions(tmp_path: Path) -> None:
    """유효한 source의 핵심 code별 count/share를 검증한다."""
    source_path = tmp_path / "hmda.csv"
    source_path.write_text(
        "\n".join(
            [
                "activity_year,state_code,county_code,loan_purpose,action_taken,loan_amount,income",
                "2024,CA,06001,1,1,350000,120",
                "2025,NY,36001,1,3,420000,150",
                "2025,CA,06001,1,1,500000,200",
            ]
        ),
        encoding="utf-8",
    )

    evidence = analyze_hmda_csv(
        source_path,
        memory_limit="256MB",
        threads=1,
        temp_directory=tmp_path / "duckdb-temp",
    )

    assert "distributions" in evidence
    assert "county_code" not in evidence["distributions"]
    state_dist = evidence["distributions"]["state_code"]
    assert len(state_dist) == 2
    assert state_dist[0]["value"] == "CA"
    assert state_dist[0]["count"] == 2
    assert state_dist[0]["share"] == pytest.approx(2 / 3)
    assert state_dist[1]["value"] == "NY"
    assert state_dist[1]["count"] == 1
    assert state_dist[1]["share"] == pytest.approx(1 / 3)


def test_returns_numeric_summaries_without_clipping(tmp_path: Path) -> None:
    """대상 numeric field의 non-null count와 five-number summary를 검증한다."""
    source_path = tmp_path / "hmda.csv"
    source_path.write_text(
        "\n".join(
            [
                "activity_year,state_code,county_code,loan_purpose,action_taken,loan_amount,income",
                "2024,CA,06001,1,1,100,10",
                "2025,NY,36001,1,3,200,20",
                "2025,TX,48113,1,1,300,30",
            ]
        ),
        encoding="utf-8",
    )

    evidence = analyze_hmda_csv(
        source_path,
        memory_limit="256MB",
        threads=1,
        temp_directory=tmp_path / "duckdb-temp",
    )

    assert "numeric_summaries" in evidence
    income_summary = evidence["numeric_summaries"]["income"]
    assert income_summary["non_null_count"] == 3
    assert income_summary["min"] == 10.0
    assert income_summary["median"] == 20.0
    assert income_summary["max"] == 30.0


def test_reports_suspicious_numeric_observations(tmp_path: Path) -> None:
    """Configured suspicious condition의 field/condition/count/share를 검증한다."""
    source_path = tmp_path / "hmda.csv"
    source_path.write_text(
        "\n".join(
            [
                "activity_year,state_code,county_code,loan_purpose,action_taken,loan_amount,income",
                "2024,CA,06001,1,1,-50,-10",
                "2025,NY,36001,1,3,0,100",
                "2025,TX,48113,1,1,200,200",
            ]
        ),
        encoding="utf-8",
    )

    evidence = analyze_hmda_csv(
        source_path,
        memory_limit="256MB",
        threads=1,
        temp_directory=tmp_path / "duckdb-temp",
    )

    assert "anomalies" not in evidence


def test_returns_mart_grain_alignment_evidence(tmp_path: Path) -> None:
    """현재 mart grain의 aggregate count와 key coverage를 검증한다."""
    source_path = tmp_path / "hmda.csv"
    source_path.write_text(
        "\n".join(
            [
                "activity_year,state_code,county_code,loan_purpose,action_taken,loan_amount,income",
                "2024,CA,06001,1,1,100,10",
                "2024,CA,06001,1,1,200,20",
                "2025,NY,36001,2,3,300,30",
            ]
        ),
        encoding="utf-8",
    )

    evidence = analyze_hmda_csv(
        source_path,
        memory_limit="256MB",
        threads=1,
        temp_directory=tmp_path / "duckdb-temp",
    )

    assert "grain" in evidence
    grain = evidence["grain"]
    assert grain["columns"] == ["activity_year", "state_code", "loan_purpose"]
    assert grain["distinct_group_count"] == 2
    assert grain["null_key_rows"] == 0
    assert grain["coverage_rate"] == 1.0


def test_rejects_missing_descriptive_column_without_partial_evidence(
    tmp_path: Path,
) -> None:
    """필수 descriptive field 누락이 명시적으로 실패하는지 검증한다."""
    source_path = tmp_path / "hmda.csv"
    source_path.write_text(
        "\n".join(
            [
                "activity_year,state_code,county_code,loan_purpose",
                "2024,CA,06001,1",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        HMDADataValidationError, match="Required EDA column validation failed"
    ):
        analyze_hmda_csv(
            source_path,
            memory_limit="256MB",
            threads=1,
            temp_directory=tmp_path / "duckdb-temp",
        )


def test_eda_public_api_compatibility() -> None:
    """EDA namespace가 analyze_hmda_csv만 노출하는지 검증한다."""
    import project_pivot.hmda_data.eda as eda

    assert hasattr(eda, "analyze_hmda_csv")
    assert not hasattr(eda, "prepare_hmda_eda_fixture")
    assert not hasattr(eda, "run_hmda_eda_memory_workload")
    assert not hasattr(eda, "FIXTURE_VERSION")


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
    assert "schema_hash" not in evidence["schema"]
    assert "freshness" not in evidence
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
