"""HMDA 원천 EDA 계산 계약 및 도메인 분석 단위 테스트."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

import duckdb
import pytest

from project_pivot.hmda_data import analyze_hmda_csv
from project_pivot.hmda_data.errors import HMDADataValidationError

pytestmark = pytest.mark.component


def test_analyze_hmda_csv_returns_core_code_distributions(tmp_path: Path) -> None:
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


def test_analyze_hmda_csv_returns_numeric_summaries_without_clipping(
    tmp_path: Path,
) -> None:
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


def test_analyze_hmda_csv_reports_suspicious_numeric_observations(
    tmp_path: Path,
) -> None:
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


def test_analyze_hmda_csv_returns_mart_grain_alignment_evidence(
    tmp_path: Path,
) -> None:
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


def test_analyze_hmda_csv_six_core_source_without_county_code_succeeds(
    tmp_path: Path,
) -> None:
    """county_code가 없는 6개 core 컬럼만의 입력도 EDA 분석을 성공해야 한다."""
    source_path = tmp_path / "hmda_6core.csv"
    source_path.write_text(
        "\n".join(
            [
                "activity_year,state_code,loan_purpose,action_taken,loan_amount,income",
                "2024,CA,1,1,350000,120",
                "2025,NY,1,3,420000,150",
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

    assert evidence["row_count"] == 2
    assert "county_code" not in evidence["null_counts"]
    columns = [col["column"] for col in evidence["schema"]["required_columns"]]
    assert "county_code" not in columns


def test_analyze_hmda_csv_grain_alignment_excludes_null_keys_from_distinct_count(
    tmp_path: Path,
) -> None:
    """grain key 중 하나라도 null인 행은 distinct group count에서 제외된다."""
    source_path = tmp_path / "hmda_null_grain.csv"
    source_path.write_text(
        "\n".join(
            [
                "activity_year,state_code,loan_purpose,action_taken,loan_amount,income",
                "2024,CA,1,1,100,10",
                "2024,CA,1,1,200,20",
                "2024,,1,1,300,30",  # state_code null
                ",CA,1,1,400,40",  # activity_year null
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

    grain = evidence["grain"]
    assert grain["distinct_group_count"] == 1
    assert grain["null_key_rows"] == 2
    assert grain["coverage_rate"] == pytest.approx(2 / 4)


def test_analyze_hmda_csv_rejects_missing_descriptive_column_without_partial_evidence(
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
    """EDA namespace의 public API 구성을 검증한다."""
    import project_pivot.hmda_data.eda as eda

    assert hasattr(eda, "analyze_hmda_csv")
    assert hasattr(eda, "export_eda_evidence_yaml")
    assert hasattr(eda, "render_eda_static_charts")
    assert not hasattr(eda, "prepare_hmda_eda_fixture")
    assert not hasattr(eda, "run_hmda_eda_memory_workload")


def test_supports_expanded_type_families() -> None:
    """EXPECTED_TYPE_FAMILIES에 FLOAT/REAL 및 무부호 정수가 지원되는지 검증한다."""
    from project_pivot.hmda_data.eda.analysis import EXPECTED_TYPE_FAMILIES

    for col in ("activity_year", "action_taken", "loan_purpose"):
        for uint_type in ("UTINYINT", "USMALLINT", "UINTEGER", "UBIGINT"):
            assert uint_type in EXPECTED_TYPE_FAMILIES[col]

    for num_col in ("loan_amount", "income"):
        for float_type in ("FLOAT", "REAL"):
            assert float_type in EXPECTED_TYPE_FAMILIES[num_col]


def test_code_distributions_converts_non_primitive_types_for_json(
    tmp_path: Path,
) -> None:
    """_collect_code_distributions 결과 비기본 타입의 JSON 직렬화를 검증한다."""
    source_path = tmp_path / "hmda_decimal.csv"
    source_path.write_text(
        "\n".join(
            [
                "activity_year,state_code,loan_purpose,action_taken,loan_amount,income",
                "2024,CA,1,1,100,10",
                "2025,NY,2,3,200,20",
            ]
        ),
        encoding="utf-8",
    )

    from unittest.mock import MagicMock, patch

    original_execute = duckdb.DuckDBPyConnection.execute

    def mock_execute(
        self: duckdb.DuckDBPyConnection, query: str, *args: object, **kwargs: object
    ) -> duckdb.DuckDBPyConnection:
        res = original_execute(self, query, *args, **kwargs)
        if 'SELECT "action_taken" AS val' in str(query):
            import decimal

            mock_res = MagicMock()
            mock_res.fetchall.return_value = [
                (decimal.Decimal("1.000"), 2),
            ]
            return mock_res
        return res

    with patch.object(duckdb.DuckDBPyConnection, "execute", new=mock_execute):
        evidence = analyze_hmda_csv(
            source_path,
            memory_limit="256MB",
            threads=1,
            temp_directory=tmp_path / "duckdb-temp",
        )

    assert evidence["distributions"]["action_taken"][0]["value"] == "1.000"
    serialized = json.dumps(evidence)
    assert serialized is not None


def test_activity_year_sampling_order_has_secondary_sort(tmp_path: Path) -> None:
    """activity_year 쿼리에 2차 정렬 조건(activity_year ASC)을 검증한다."""
    from unittest.mock import patch

    executed_sqls: list[str] = []
    original_execute = duckdb.DuckDBPyConnection.execute

    def tracking_execute(
        self: duckdb.DuckDBPyConnection, query: str, *args: object, **kwargs: object
    ) -> duckdb.DuckDBPyConnection:
        executed_sqls.append(str(query))
        return original_execute(self, query, *args, **kwargs)

    source_path = tmp_path / "hmda.csv"
    source_path.write_text(
        "\n".join(
            [
                "activity_year,state_code,loan_purpose,action_taken,loan_amount,income",
                "2024,CA,1,1,100,10",
            ]
        ),
        encoding="utf-8",
    )

    with patch.object(duckdb.DuckDBPyConnection, "execute", new=tracking_execute):
        analyze_hmda_csv(
            source_path,
            temp_directory=tmp_path / "tmp",
        )

    grouping_sql = [sql for sql in executed_sqls if "GROUPING SETS" in sql]
    assert len(grouping_sql) > 0
    assert "ORDER BY is_total DESC, activity_year ASC" in grouping_sql[0]


def test_analyze_hmda_csv_observed_at_does_not_trigger_freshness(
    tmp_path: Path,
) -> None:
    """observed_at이 있어도 MAX(observed_at) 쿼리와 freshness 반환 키가 없다."""
    csv_file = tmp_path / "hmda_with_observed_at.csv"
    csv_file.write_text(
        "activity_year,state_code,loan_purpose,action_taken,loan_amount,income,observed_at\n"
        "2025,CA,1,1,100000,50000,2025-01-01T00:00:00Z\n"
        "2025,NY,1,2,200000,80000,2025-01-02T00:00:00Z\n",
        encoding="utf-8",
    )

    executed_sqls: list[str] = []
    original_execute = duckdb.DuckDBPyConnection.execute

    def tracking_execute(
        self: duckdb.DuckDBPyConnection, query: str, *args: object, **kwargs: object
    ) -> duckdb.DuckDBPyConnection:
        executed_sqls.append(str(query))
        return original_execute(self, query, *args, **kwargs)

    with patch.object(duckdb.DuckDBPyConnection, "execute", new=tracking_execute):
        evidence = analyze_hmda_csv(
            source_path=csv_file,
            temp_directory=tmp_path / "tmp",
        )

    assert "freshness" not in evidence
    assert "observed_at" not in evidence

    all_sqls = " ".join(executed_sqls).lower()
    assert "max(observed_at)" not in all_sqls
    assert "freshness" not in all_sqls


def test_inspect_and_validate_schema_helper() -> None:
    """_inspect_and_validate_schema 헬퍼 함수를 인메모리 릴레이션으로 검증한다."""
    from project_pivot.hmda_data.eda.analysis import _inspect_and_validate_schema

    conn = duckdb.connect()
    try:
        rel = conn.sql(
            "SELECT 2024 AS activity_year, 'CA' AS state_code, 1 AS loan_purpose, "
            "1 AS action_taken, 1000 AS loan_amount, 50 AS income"
        )
        schema_rows, inferred_types, required_schema, profile_columns = (
            _inspect_and_validate_schema(rel)
        )
        assert len(schema_rows) == 6
        assert inferred_types["state_code"] == "VARCHAR"
        assert all(col["status"] == "valid" for col in required_schema)
        assert len(profile_columns) == 6
    finally:
        conn.close()


def test_collect_volume_and_null_metrics_helper() -> None:
    """_collect_volume_and_null_metrics 헬퍼 함수를 인메모리 뷰로 검증한다."""
    from project_pivot.hmda_data.eda.analysis import _collect_volume_and_null_metrics

    conn = duckdb.connect()
    try:
        conn.execute(
            "CREATE VIEW hmda_eda_source AS "
            "SELECT 2024 AS activity_year, 'CA' AS state_code, 1 AS loan_purpose, "
            "1 AS action_taken, 1000 AS loan_amount, CAST(NULL AS INT) AS income"
        )
        inferred_types = {
            "activity_year": "INTEGER",
            "state_code": "VARCHAR",
            "loan_purpose": "INTEGER",
            "action_taken": "INTEGER",
            "loan_amount": "INTEGER",
            "income": "INTEGER",
        }
        profile_columns = [
            "activity_year",
            "state_code",
            "loan_purpose",
            "action_taken",
            "loan_amount",
            "income",
        ]
        row_count, null_counts, activity_year_rows, metric_offset = (
            _collect_volume_and_null_metrics(
                conn, inferred_types, profile_columns, max_activity_years=10
            )
        )
        assert row_count == 1
        assert null_counts["income"] == 1
        assert null_counts["loan_amount"] == 0
        assert len(activity_year_rows) == 1
        assert metric_offset == 2
    finally:
        conn.close()


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
