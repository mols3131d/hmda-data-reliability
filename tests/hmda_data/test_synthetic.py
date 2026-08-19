"""HMDA 합성 데이터 지표 생성 및 검증 테스트."""

from __future__ import annotations

from pathlib import Path

import duckdb
import pytest

from project_pivot.data_platform.duckdb import DuckDBConnectionManager
from project_pivot.hmda_data import (
    null_spike,
    row_count_drop,
    schema_drift,
)
from project_pivot.hmda_data.errors import SyntheticCaseError
from project_pivot.hmda_data.synthetic._writer import write_case_file

pytestmark = pytest.mark.component


def test_synthetic_cases_expose_expected_defect_statistics(
    tmp_path: Path,
    hmda_csv_path: Path,
) -> None:
    """HMDA 이상 파일이 기대 통계를 드러내는지 검증한다."""

    case_root = tmp_path / "cases"
    with DuckDBConnectionManager() as connection:
        row_drop_path = row_count_drop(
            connection,
            [hmda_csv_path],
            case_root,
            sample_fraction=0.5,
        )
        null_path = null_spike(
            connection,
            [hmda_csv_path],
            case_root,
            null_fraction=0.5,
            sample_fraction=1,
        )
        drift_path = schema_drift(
            connection,
            [hmda_csv_path],
            case_root,
            sample_fraction=1,
        )
        row_drop_count = _row_count(connection, row_drop_path)
        source_null_ratio = _csv_null_ratio(connection, hmda_csv_path, "income")
        null_ratio = _null_ratio(connection, null_path, "income")
        drift_type = _column_type(connection, drift_path, "loan_amount")

    assert row_drop_count == 1
    assert null_ratio > source_null_ratio
    assert drift_type == "VARCHAR"


def test_null_spike_increases_high_baseline_null_rate(tmp_path: Path) -> None:
    """A high existing null rate cannot turn a requested spike into a no-op."""

    source_path = tmp_path / "high-null.csv"
    source_path.write_text(
        "\n".join(
            [
                "activity_year,loan_amount,income",
                *[f"2025,{index}," for index in range(9)],
                "2025,9,1",
            ]
        ),
        encoding="utf-8",
    )

    with DuckDBConnectionManager() as connection:
        source_null_ratio = _csv_null_ratio(connection, source_path, "income")
        null_path = null_spike(
            connection,
            [source_path],
            tmp_path / "cases",
            null_fraction=0.2,
        )
        generated_null_ratio = _null_ratio(connection, null_path, "income")
        generated_non_null_count = connection.execute(
            "SELECT count(income) FROM read_parquet(?)",
            [str(null_path)],
        ).fetchone()

    assert source_null_ratio == 0.9
    assert generated_null_ratio > source_null_ratio
    assert generated_non_null_count == (0,)


def test_null_spike_partial_sample_exceeds_original_null_rate(tmp_path: Path) -> None:
    """A partial output remains a real spike relative to the full source."""

    source_path = tmp_path / "mixed-null.csv"
    source_path.write_text(
        "\n".join(
            [
                "activity_year,loan_amount,income",
                *[f"2025,{index}," for index in range(5)],
                *[f"2025,{index},{index + 2}" for index in range(5, 10)],
            ]
        ),
        encoding="utf-8",
    )

    with DuckDBConnectionManager() as connection:
        source_null_ratio = _csv_null_ratio(connection, source_path, "income")
        null_path = null_spike(
            connection,
            [source_path],
            tmp_path / "cases",
            null_fraction=0.2,
            sample_fraction=0.2,
        )
        generated_null_ratio = _null_ratio(connection, null_path, "income")
        generated_row_count = _row_count(connection, null_path)

    assert source_null_ratio == 0.5
    assert generated_row_count == 2
    assert generated_null_ratio > source_null_ratio


def test_null_spike_partial_sample_strict_increase_with_non_binary_exact_ratio(
    tmp_path: Path,
) -> None:
    """Non-binary-exact source ratio with partial sample strictly increases null.

    Verifies integer arithmetic strictly increases the null rate without
    floating-point ambiguity.
    """

    source_path = tmp_path / "imprecise-ratio.csv"
    source_path.write_text(
        "\n".join(
            [
                "activity_year,loan_amount,income",
                *[f"2025,{index}," for index in range(70)],
                *[f"2025,{index},{index + 1}" for index in range(70, 100)],
            ]
        ),
        encoding="utf-8",
    )

    with DuckDBConnectionManager() as connection:
        source_null_ratio = _csv_null_ratio(connection, source_path, "income")
        null_path = null_spike(
            connection,
            [source_path],
            tmp_path / "cases",
            null_fraction=0.01,
            sample_fraction=0.9,
        )
        generated_null_ratio = _null_ratio(connection, null_path, "income")
        generated_row_count = _row_count(connection, null_path)
        source_counts = connection.execute(
            """
            SELECT
                count(*) AS source_total,
                count(*) - count(income) AS source_nulls
            FROM read_csv_auto(?, header = true, nullstr = ['NA', ''])
            """,
            [str(source_path)],
        ).fetchone()
        output_counts = connection.execute(
            """
            SELECT
                count(*) AS output_total,
                count(*) - count(income) AS output_nulls
            FROM read_parquet(?)
            """,
            [str(null_path)],
        ).fetchone()

    assert source_null_ratio == 0.7
    assert generated_row_count == 90
    assert generated_null_ratio > source_null_ratio
    assert source_counts is not None and output_counts is not None
    source_total, source_nulls = source_counts
    output_total, output_nulls = output_counts
    assert output_nulls * source_total > source_nulls * output_total


def test_null_spike_rejects_all_null_target_without_output(tmp_path: Path) -> None:
    """An all-null target cannot produce a contract-compliant synthetic defect."""

    source_path = tmp_path / "all-null.csv"
    source_path.write_text(
        "\n".join(
            [
                "activity_year,loan_amount,income",
                "2025,1,",
                "2025,2,",
            ]
        ),
        encoding="utf-8",
    )
    case_root = tmp_path / "cases"

    with (
        DuckDBConnectionManager() as connection,
        pytest.raises(SyntheticCaseError, match="non-null"),
    ):
        null_spike(connection, [source_path], case_root)

    assert not (case_root / "null_spike").exists()


def test_null_spike_distributes_mutations_across_years(tmp_path: Path) -> None:
    """Each year receives its requested fraction of mutations, not concentrated."""

    source_path = tmp_path / "multi-year-clean.csv"
    source_path.write_text(
        "\n".join(
            [
                "activity_year,loan_amount,income",
                *[f"2024,{i},{100 + i}" for i in range(10)],
                *[f"2025,{i},{200 + i}" for i in range(10)],
            ]
        ),
        encoding="utf-8",
    )

    with DuckDBConnectionManager() as connection:
        null_path = null_spike(
            connection,
            [source_path],
            tmp_path / "cases",
            null_fraction=0.5,
        )
        year_nulls = connection.execute(
            """
            SELECT activity_year, count(*) - count(income) AS null_count
            FROM read_parquet(?)
            GROUP BY activity_year
            ORDER BY activity_year
            """,
            [str(null_path)],
        ).fetchall()

    assert len(year_nulls) == 2
    for _year, null_count in year_nulls:
        assert null_count >= 5, f"year {_year}: expected >= 5 nulls, got {null_count}"


def test_null_spike_requested_fraction_magnitude(tmp_path: Path) -> None:
    """The requested null_fraction is reflected in observable per-year null counts."""

    source_path = tmp_path / "clean-multi-year.csv"
    source_path.write_text(
        "\n".join(
            [
                "activity_year,loan_amount,income",
                *[f"2024,{i},{100 + i}" for i in range(10)],
                *[f"2025,{i},{200 + i}" for i in range(20)],
            ]
        ),
        encoding="utf-8",
    )

    with DuckDBConnectionManager() as connection:
        null_path = null_spike(
            connection,
            [source_path],
            tmp_path / "cases",
            null_fraction=0.3,
        )
        year_stats = connection.execute(
            """
            SELECT
                activity_year,
                count(*) AS total,
                count(*) - count(income) AS null_count
            FROM read_parquet(?)
            GROUP BY activity_year
            ORDER BY activity_year
            """,
            [str(null_path)],
        ).fetchall()

    from math import ceil

    for year, total, null_count in year_stats:
        expected = ceil(total * 0.3)
        assert null_count >= expected, (
            f"year {year}: expected >= {expected} nulls, got {null_count}"
        )


def test_synthetic_case_rejects_missing_columns(
    tmp_path: Path,
    hmda_csv_path: Path,
) -> None:
    """원천에 없는 컬럼 요청은 합성 데이터 예외로 실패한다."""

    with (
        DuckDBConnectionManager() as connection,
        pytest.raises(SyntheticCaseError, match="필요한 컬럼"),
    ):
        null_spike(
            connection,
            [hmda_csv_path],
            tmp_path / "cases",
            target_column="missing_column",
        )


def test_row_count_drop_is_invariant_to_input_order_for_partial_key_ties(
    tmp_path: Path,
) -> None:
    """Sampling은 HMDA partial key가 같은 row의 입력 순서에 의존하지 않는다."""

    header = (
        "activity_year,loan_purpose,action_taken,loan_amount,income,state_code,"
        "county_code,loan_type"
    )
    rows = [
        "2025,1,1,350000,120,CA,06001,conventional",
        "2025,1,1,350000,120,CA,06001,fha",
    ]
    first_source = tmp_path / "first.csv"
    second_source = tmp_path / "second.csv"
    first_source.write_text("\n".join([header, *rows]), encoding="utf-8")
    second_header = (
        "loan_type,county_code,state_code,income,loan_amount,action_taken,"
        "loan_purpose,activity_year"
    )
    second_rows = [",".join(reversed(row.split(","))) for row in reversed(rows)]
    second_source.write_text(
        "\n".join([second_header, *second_rows]),
        encoding="utf-8",
    )

    with DuckDBConnectionManager() as connection:
        first_path = row_count_drop(
            connection,
            [first_source],
            tmp_path / "first-case",
            sample_fraction=0.5,
        )
        second_path = row_count_drop(
            connection,
            [second_source],
            tmp_path / "second-case",
            sample_fraction=0.5,
        )
        selected_values = [
            row[0]
            for row in (
                connection.execute(
                    "SELECT loan_type FROM read_parquet(?)",
                    [str(path)],
                ).fetchall()
                for path in (first_path, second_path)
            )
        ]

    assert selected_values[0] == selected_values[1]


def test_row_count_drop_wraps_source_schema_failure(tmp_path: Path) -> None:
    """Synthetic schema 조회 실패는 domain error로 노출한다."""

    with (
        DuckDBConnectionManager() as connection,
        pytest.raises(SyntheticCaseError, match="스키마 조회"),
    ):
        row_count_drop(
            connection,
            [tmp_path / "missing.csv"],
            tmp_path / "cases",
        )


def test_write_case_file_rejects_parent_directory_case_name(tmp_path: Path) -> None:
    """case name이 출력 root 밖의 디렉터리를 가리키지 못하게 한다."""

    output_root = tmp_path / "cases"
    sentinel = tmp_path / "keep.txt"
    sentinel.write_text("keep", encoding="utf-8")

    with (
        DuckDBConnectionManager() as connection,
        pytest.raises(SyntheticCaseError, match="case_name"),
    ):
        write_case_file(
            connection=connection,
            case_name="..",
            output_root=output_root,
            query="SELECT 1",
            params=[],
        )

    assert sentinel.exists()


def _row_count(
    connection: duckdb.DuckDBPyConnection,
    case_path: Path,
) -> int:
    row = connection.execute(
        "SELECT count(*) FROM read_parquet(?)",
        [str(case_path)],
    ).fetchone()
    assert row is not None
    return int(row[0])


def _null_ratio(
    connection: duckdb.DuckDBPyConnection,
    case_path: Path,
    column_name: str,
) -> float:
    row = connection.execute(
        f"""
        SELECT avg(CASE WHEN "{column_name}" IS NULL THEN 1.0 ELSE 0.0 END)
        FROM read_parquet(?)
        """,
        [str(case_path)],
    ).fetchone()
    assert row is not None
    return float(row[0])


def _csv_null_ratio(
    connection: duckdb.DuckDBPyConnection,
    source_path: Path,
    column_name: str,
) -> float:
    row = connection.execute(
        f"""
        SELECT avg(CASE WHEN "{column_name}" IS NULL THEN 1.0 ELSE 0.0 END)
        FROM read_csv_auto(?, header = true, nullstr = ['NA', ''])
        """,
        [str(source_path)],
    ).fetchone()
    assert row is not None
    return float(row[0])


def _column_type(
    connection: duckdb.DuckDBPyConnection,
    case_path: Path,
    column_name: str,
) -> str:
    rows = connection.execute(
        "DESCRIBE SELECT * FROM read_parquet(?) LIMIT 0",
        [str(case_path)],
    ).fetchall()
    return next(str(row[1]) for row in rows if row[0] == column_name)
