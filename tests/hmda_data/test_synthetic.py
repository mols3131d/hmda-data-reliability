"""HMDA 합성 데이터 지표 생성 및 검증 테스트."""

from __future__ import annotations

from collections.abc import Callable
from functools import partial
from pathlib import Path

import duckdb
import pytest

from hmda_reliability.data_platform.duckdb import DuckDBConnectionManager
from hmda_reliability.hmda_data import (
    load_hmda_loans_partition,
    null_spike,
    row_count_drop,
    schema_drift,
)
from hmda_reliability.hmda_data.errors import SyntheticCaseError
from hmda_reliability.hmda_data.synthetic._writer import write_case_file

pytestmark = pytest.mark.component

type SyntheticGenerator = Callable[[duckdb.DuckDBPyConnection, list[Path], Path], Path]


@pytest.mark.parametrize(
    ("generate_case", "case_name"),
    [
        (row_count_drop, "row_count_drop"),
        (null_spike, "null_spike"),
        (schema_drift, "schema_drift"),
        (partial(null_spike, case_name="custom_spike"), "custom_spike"),
        (partial(null_spike, target_year=2026), "null_spike_2026"),
    ],
)
@pytest.mark.parametrize(
    "path_alias",
    [
        "direct",
        "relative",
        "source_symlink",
        "output_symlink",
        "wildcard",
        "outward_file_symlink",
        "outward_directory_symlink",
        "intermediate_file_symlink",
        "intermediate_directory_symlink",
    ],
)
def test_synthetic_case_preserves_sources_inside_case_directory(
    tmp_path: Path,
    hmda_csv_path: Path,
    generate_case: SyntheticGenerator,
    case_name: str,
    path_alias: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """다중 입력 중 하나라도 삭제 범위에 있으면 기존 파일을 모두 보존한다."""

    source_bytes = hmda_csv_path.read_bytes()
    output_root = tmp_path / "cases"
    case_dir = output_root / case_name
    case_dir.mkdir(parents=True)
    source_path = case_dir / "year_2025.csv"
    source_path.write_bytes(source_bytes)
    previous_output = case_dir / "previous.parquet"
    previous_output.write_bytes(b"previous case output")
    source_argument = source_path
    output_argument = output_root
    if path_alias == "relative":
        monkeypatch.chdir(tmp_path)
        (case_dir / "nested").mkdir()
        source_argument = Path("cases") / case_name / "nested/../year_2025.csv"
        output_argument = Path("cases")
    elif path_alias == "source_symlink":
        source_argument = tmp_path / "source_alias.csv"
        source_argument.symlink_to(source_path)
    elif path_alias == "output_symlink":
        output_argument = tmp_path / "output_alias"
        output_argument.symlink_to(output_root, target_is_directory=True)
    elif path_alias == "wildcard":
        source_argument = output_root / "*" / "year_2025.csv"
        sibling_source = output_root / "sibling" / "year_2025.csv"
        sibling_source.parent.mkdir()
        sibling_source.write_bytes(source_bytes)
    elif path_alias == "outward_file_symlink":
        source_path.unlink()
        source_path.symlink_to(hmda_csv_path)
    elif path_alias == "outward_directory_symlink":
        source_argument = case_dir / "source_alias" / hmda_csv_path.name
        source_argument.parent.symlink_to(
            hmda_csv_path.parent, target_is_directory=True
        )

    elif path_alias == "intermediate_file_symlink":
        source_path.unlink()
        source_path.symlink_to(hmda_csv_path)
        source_argument = tmp_path / "indirect_source.csv"
        source_argument.symlink_to(source_path)
    elif path_alias == "intermediate_directory_symlink":
        intermediate = case_dir / "intermediate"
        intermediate.symlink_to(hmda_csv_path.parent, target_is_directory=True)
        alias = tmp_path / "indirect_source"
        alias.symlink_to(intermediate, target_is_directory=True)
        source_argument = alias / hmda_csv_path.name

    with DuckDBConnectionManager() as connection, pytest.raises(SyntheticCaseError):
        generate_case(connection, [hmda_csv_path, source_argument], output_argument)

    assert source_path.is_file()
    assert source_path.read_bytes() == source_bytes
    assert hmda_csv_path.read_bytes() == source_bytes
    assert previous_output.read_bytes() == b"previous case output"
    if path_alias == "wildcard":
        assert sibling_source.read_bytes() == source_bytes
    else:
        assert source_argument.read_bytes() == source_bytes


@pytest.mark.parametrize("generate_case", [row_count_drop, null_spike, schema_drift])
def test_synthetic_case_preserves_source_when_reusing_its_parquet_output(
    tmp_path: Path,
    hmda_csv_path: Path,
    generate_case: SyntheticGenerator,
) -> None:
    output_root = tmp_path / "cases"
    with DuckDBConnectionManager() as connection:
        source_path = generate_case(connection, [hmda_csv_path], output_root)
        source_bytes = source_path.read_bytes()
        with pytest.raises(SyntheticCaseError):
            generate_case(connection, [source_path], output_root)

    assert source_path.is_file()
    assert source_path.read_bytes() == source_bytes


@pytest.mark.parametrize(
    ("generate_case", "case_name"),
    [
        (row_count_drop, "row_count_drop"),
        (null_spike, "null_spike"),
        (schema_drift, "schema_drift"),
    ],
)
@pytest.mark.parametrize("source_form", ["direct", "wildcard", "symlink_parent"])
def test_synthetic_case_replaces_output_without_changing_sibling_source(
    tmp_path: Path,
    hmda_csv_path: Path,
    generate_case: SyntheticGenerator,
    case_name: str,
    source_form: str,
) -> None:
    source_bytes = hmda_csv_path.read_bytes()
    output_root = tmp_path / "cases"
    source_path = output_root / f"{case_name}_source" / "year_2025.csv"
    source_path.parent.mkdir(parents=True)
    source_path.write_bytes(source_bytes)
    source_argument = source_path
    if source_form == "wildcard":
        source_argument = source_path.parent / "*.csv"
    elif source_form == "symlink_parent":
        case_dir = output_root / case_name
        case_dir.mkdir()
        alias = tmp_path / "case_alias"
        alias.symlink_to(case_dir, target_is_directory=True)
        source_argument = alias / ".." / source_path.parent.name / source_path.name

    with DuckDBConnectionManager() as connection:
        first_output = generate_case(connection, [source_argument], output_root)
        first_rows = connection.execute(
            "SELECT * FROM read_parquet(?) ORDER BY ALL", [str(first_output)]
        ).fetchall()
        stale_output = first_output.parent / "nested" / "stale.txt"
        stale_output.parent.mkdir()
        stale_output.write_text("stale", encoding="utf-8")
        regenerated = generate_case(connection, [source_argument], output_root)
        regenerated_rows = connection.execute(
            "SELECT * FROM read_parquet(?) ORDER BY ALL", [str(regenerated)]
        ).fetchall()

    assert regenerated == first_output
    assert regenerated_rows == first_rows
    assert list(regenerated.parent.iterdir()) == [regenerated]
    assert source_path.read_bytes() == source_bytes
    if source_form != "wildcard":
        assert source_argument.read_bytes() == source_bytes


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
            source_paths=[],
            query="SELECT 1",
            params=[],
        )

    assert sentinel.exists()


def test_null_spike_supports_target_year_override(
    tmp_path: Path,
    hmda_csv_path: Path,
) -> None:
    """합성 결함 생성 시 target_year를 지정하면 activity_year 파티션이 교체된다."""

    case_root = tmp_path / "cases"
    with DuckDBConnectionManager() as connection:
        null_path = null_spike(
            connection,
            [hmda_csv_path],
            case_root,
            null_fraction=0.3,
            target_year=2026,
        )
        years = connection.execute(
            "SELECT DISTINCT activity_year FROM read_parquet(?)",
            [str(null_path)],
        ).fetchall()
        null_ratio = _null_ratio(connection, null_path, "income")

    assert null_path.name == "null_spike_2026.parquet"
    assert years == [(2026,)]
    assert null_ratio >= 0.3


def test_null_spike_rejects_activity_year_target_column_with_target_year(
    tmp_path: Path,
    hmda_csv_path: Path,
) -> None:
    """target_year와 target_column='activity_year'의 동시 지정은 거부된다."""

    with (
        DuckDBConnectionManager() as connection,
        pytest.raises(SyntheticCaseError, match="activity_year"),
    ):
        null_spike(
            connection,
            [hmda_csv_path],
            tmp_path / "cases",
            target_column="activity_year",
            target_year=2026,
        )


def test_null_spike_rejects_case_name_without_target_year_when_target_year_is_set(
    tmp_path: Path,
    hmda_csv_path: Path,
) -> None:
    """target_year 지정 시 case_name에 해당 연도가 없거나 다른 연도면 거부된다."""

    with (
        DuckDBConnectionManager() as connection,
        pytest.raises(SyntheticCaseError, match="ASCII 4자리 연도가 포함"),
    ):
        null_spike(
            connection,
            [hmda_csv_path],
            tmp_path / "cases",
            target_year=2026,
            case_name="custom_spike",
        )

    with (
        DuckDBConnectionManager() as connection,
        pytest.raises(SyntheticCaseError, match="첫 번째 4자리 연도"),
    ):
        null_spike(
            connection,
            [hmda_csv_path],
            tmp_path / "cases",
            target_year=2026,
            case_name="null_spike_2024",
        )


def test_null_spike_rejects_case_name_with_conflicting_first_year(
    tmp_path: Path,
    hmda_csv_path: Path,
) -> None:
    """Filename parser가 먼저 읽는 연도가 target_year와 다르면 거부한다."""

    with (
        DuckDBConnectionManager() as connection,
        pytest.raises(SyntheticCaseError, match="첫 번째 4자리 연도"),
    ):
        null_spike(
            connection,
            [hmda_csv_path],
            tmp_path / "cases",
            target_year=2026,
            case_name="null_spike_2025_2026",
        )


def test_null_spike_rejects_case_name_with_non_ascii_year(
    tmp_path: Path,
    hmda_csv_path: Path,
) -> None:
    """Ingestion이 연도로 읽지 못하는 Unicode digit filename을 거부한다."""

    with (
        DuckDBConnectionManager() as connection,
        pytest.raises(SyntheticCaseError, match="ASCII 4자리 연도"),
    ):
        null_spike(
            connection,
            [hmda_csv_path],
            tmp_path / "cases",
            target_year=2026,
            case_name="null_spike_２０２６",
        )


def test_null_spike_allows_case_name_with_matching_first_year(
    tmp_path: Path,
    hmda_csv_path: Path,
) -> None:
    """첫 번째 filename 연도가 target_year와 같으면 custom name을 허용한다."""

    with DuckDBConnectionManager() as connection:
        null_path = null_spike(
            connection,
            [hmda_csv_path],
            tmp_path / "cases",
            target_year=2026,
            case_name="null_spike_2026_revision_2025",
        )
        loaded_rows = load_hmda_loans_partition(connection, [null_path], 2026)
        source_years = connection.execute(
            "SELECT DISTINCT source_year FROM raw.hmda_loans"
        ).fetchall()

    assert null_path.name == "null_spike_2026_revision_2025.parquet"
    assert loaded_rows > 0
    assert source_years == [(2026,)]


@pytest.mark.parametrize(
    "invalid_year",
    [1999, 2101, True, False, "2026", 0],
)
def test_null_spike_rejects_invalid_target_year(
    tmp_path: Path,
    hmda_csv_path: Path,
    invalid_year: object,
) -> None:
    """유효하지 않은 target_year(범위 밖, bool, 비정수)는 거부된다."""

    with (
        DuckDBConnectionManager() as connection,
        pytest.raises(SyntheticCaseError, match="target_year"),
    ):
        from typing import cast

        null_spike(
            connection,
            [hmda_csv_path],
            tmp_path / "cases",
            target_year=cast(int, invalid_year),
        )


def test_null_spike_rejects_multi_year_source_with_target_year(
    tmp_path: Path,
) -> None:
    """다중 연도 원천 데이터에 target_year 지정 시
    파티션 붕괴를 방지하기 위해 거부된다.
    """

    source_path = tmp_path / "multi-year.csv"
    source_path.write_text(
        "\n".join(
            [
                "activity_year,loan_amount,income",
                "2024,100,200",
                "2025,110,210",
            ]
        ),
        encoding="utf-8",
    )

    with (
        DuckDBConnectionManager() as connection,
        pytest.raises(SyntheticCaseError, match="단일 연도"),
    ):
        null_spike(
            connection,
            [source_path],
            tmp_path / "cases",
            target_year=2026,
        )


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
