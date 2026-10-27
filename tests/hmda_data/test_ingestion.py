"""HMDA 원천 데이터 적재 기능 테스트."""

from __future__ import annotations

from pathlib import Path

import pytest

import hmda_reliability.hmda_data.ingestion.full_load as full_load_module
from hmda_reliability.data_platform.duckdb import (
    DuckDBConnectionManager,
    DuckDBMutationLockError,
)
from hmda_reliability.hmda_data import (
    discover_hmda_files,
    load_hmda_loans,
    load_hmda_loans_partition,
)
from hmda_reliability.hmda_data.errors import HMDADataLoadError, HMDADataValidationError

pytestmark = pytest.mark.component


def test_discover_hmda_files_filters_supported_files(tmp_path: Path) -> None:
    """지원하는 CSV/Parquet 파일만 정렬해 찾는다."""

    expected_paths = [
        tmp_path / "hmda_2024.parquet",
        tmp_path / "year_2025.csv",
    ]
    ignored_paths = [
        tmp_path / "data_fields.html",
        tmp_path / "data_fields.md",
    ]
    for path in [*expected_paths, *ignored_paths]:
        path.touch()

    assert discover_hmda_files(tmp_path) == expected_paths


def test_discover_hmda_files_rejects_missing_directory(tmp_path: Path) -> None:
    """없는 원천 디렉터리는 명확한 적재 예외로 실패한다."""

    with pytest.raises(
        HMDADataLoadError,
        match="원천 디렉터리",
    ):
        discover_hmda_files(tmp_path / "missing")


def test_load_hmda_loans_loads_csv_and_parquet_idempotently(
    hmda_csv_path: Path,
    hmda_parquet_path: Path,
) -> None:
    """CSV/Parquet 원천 적재가 중복 없이 테이블을 재생성하는지 검증한다."""

    source_paths = [hmda_csv_path, hmda_parquet_path]
    with DuckDBConnectionManager() as connection:
        assert load_hmda_loans(connection, source_paths) == 3
        assert load_hmda_loans(connection, source_paths) == 3

        stats = connection.execute(
            """
            SELECT
                count(*),
                count(DISTINCT source_file),
                min(source_year),
                max(source_year),
                count(ingested_at)
            FROM raw.hmda_loans
            """
        ).fetchone()

    assert stats == (3, 2, 2024, 2025, 3)


def test_load_hmda_loans_creates_custom_target_schema(hmda_csv_path: Path) -> None:
    """전체 적재는 configured qualified target의 schema를 새 DB에 생성한다."""

    with DuckDBConnectionManager() as connection:
        row_count = load_hmda_loans(
            connection,
            [hmda_csv_path],
            table_name="bronze.hmda_loans",
        )
        table = connection.execute(
            """
            SELECT table_schema, table_name
            FROM information_schema.tables
            WHERE table_schema = 'bronze' AND table_name = 'hmda_loans'
            """
        ).fetchone()

    assert row_count == 2
    assert table == ("bronze", "hmda_loans")


def test_load_hmda_loans_rejects_multipart_target_table(hmda_csv_path: Path) -> None:
    """현재 loader contract 밖의 multipart target은 schema 생성 전에 거부한다."""

    with (
        DuckDBConnectionManager() as connection,
        pytest.raises(HMDADataLoadError, match="target table"),
    ):
        load_hmda_loans(
            connection,
            [hmda_csv_path],
            table_name="catalog.bronze.hmda_loans",
        )


def test_load_hmda_loans_partition_after_full_load(
    hmda_csv_path: Path,
    hmda_parquet_path: Path,
) -> None:
    """전체 적재 후 파티션 적재가 같은 raw 스키마를 공유하는지 검증한다."""

    with DuckDBConnectionManager() as connection:
        assert load_hmda_loans(connection, [hmda_parquet_path]) == 1
        assert load_hmda_loans_partition(connection, [hmda_csv_path], 2025) == 2

        stats = connection.execute(
            """
            SELECT
                count(*),
                count(DISTINCT source_file_name),
                min(source_year),
                max(source_year)
            FROM raw.hmda_loans
            """
        ).fetchone()

    assert stats == (3, 2, 2024, 2025)


def test_load_hmda_loans_wraps_duckdb_errors(tmp_path: Path) -> None:
    """원천 파일 오류가 HMDA 적재 예외로 변환되는지 검증한다."""

    missing_csv_path = tmp_path / "missing.csv"

    with (
        DuckDBConnectionManager() as connection,
        pytest.raises(
            HMDADataLoadError,
            match="HMDA 원천 데이터 적재",
        ),
    ):
        load_hmda_loans(connection, [missing_csv_path])


def test_load_hmda_loans_validates_required_columns(tmp_path: Path) -> None:
    """필수 컬럼 누락이 검증 예외로 드러나는지 확인한다."""

    path = tmp_path / "year_2025.csv"
    path.write_text(
        "\n".join(
            [
                "activity_year,loan_purpose,action_taken,loan_amount,state_code,county_code",
                "2025,1,1,350000,CA,06001",
            ]
        ),
        encoding="utf-8",
    )

    with DuckDBConnectionManager() as connection:
        with pytest.raises(HMDADataValidationError, match="필수 컬럼"):
            load_hmda_loans(connection, [path])
        columns = {
            str(row[0])
            for row in connection.execute("DESCRIBE raw.hmda_loans").fetchall()
        }

    assert "income" not in columns


@pytest.mark.parametrize(
    "reverse_paths", [False, True], ids=["valid-first", "missing-first"]
)
def test_full_load_rejects_missing_source_columns_after_replacing_target(
    hmda_csv_path: Path,
    mixed_schema_source_paths: tuple[Path, Path],
    reverse_paths: bool,
) -> None:
    """개별 원천의 누락은 거부하되 full-load의 교체 후 검증 계약을 유지한다."""

    valid_path, missing_path = mixed_schema_source_paths
    paths = [missing_path, valid_path] if reverse_paths else [valid_path, missing_path]
    with DuckDBConnectionManager() as connection:
        assert load_hmda_loans(connection, [hmda_csv_path]) == 2

        with pytest.raises(HMDADataValidationError, match="필수 컬럼") as raised:
            load_hmda_loans(connection, paths)

        assert raised.value.context["missing_columns"] == ["county_code", "income"]
        assert raised.value.context["source_path"] == missing_path.as_posix()
        rows = connection.execute(
            """
            SELECT activity_year, loan_purpose, action_taken, loan_amount,
                   income, state_code, CAST(county_code AS VARCHAR), source_file,
                   source_file_name, source_year, ingested_at IS NOT NULL
            FROM raw.hmda_loans ORDER BY loan_amount
            """
        ).fetchall()

    assert rows == [
        (
            2025,
            1,
            1,
            111000,
            80,
            "TX",
            "48113",
            valid_path.as_posix(),
            valid_path.name,
            2025,
            True,
        ),
        (
            2025,
            31,
            3,
            222000,
            None,
            "NY",
            None,
            missing_path.as_posix(),
            missing_path.name,
            2025,
            True,
        ),
    ]


def test_full_load_accepts_null_values_in_valid_csv_parquet_sources(
    nullable_mixed_source_paths: tuple[Path, Path],
) -> None:
    with DuckDBConnectionManager() as connection:
        assert load_hmda_loans(connection, nullable_mixed_source_paths) == 2
        rows = connection.execute(
            """
            SELECT loan_amount, income, state_code, county_code,
                   source_file_name, source_year, ingested_at IS NOT NULL
            FROM raw.hmda_loans ORDER BY loan_amount
            """
        ).fetchall()

    csv_path, parquet_path = nullable_mixed_source_paths
    assert rows == [
        (111000, None, "TX", "48113", csv_path.name, 2025, True),
        (222000, None, "NY", "36061", parquet_path.name, 2025, True),
    ]


def test_load_hmda_loans_translates_mutation_lock_failure(
    hmda_csv_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Full-load lock failure는 target mutation 전 domain error로 변환한다."""

    def fail_lock(database_path: str | Path | None) -> None:
        del database_path
        raise DuckDBMutationLockError("cannot acquire mutation lock")

    monkeypatch.setattr(full_load_module, "database_mutation_lock", fail_lock)

    with DuckDBConnectionManager() as connection:
        with pytest.raises(HMDADataLoadError, match="mutation lock"):
            load_hmda_loans(connection, [hmda_csv_path])
        table = connection.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'raw' AND table_name = 'hmda_loans'
            """
        ).fetchone()

    assert table is None


@pytest.mark.parametrize("partitioned", [False, True], ids=["full", "partition"])
def test_loaders_use_canonical_database_lock_before_mutation(
    hmda_csv_path: Path,
    tmp_path: Path,
    partitioned: bool,
) -> None:
    """실제 canonical lock file 획득 실패가 symlink로 연 DB의 교체도 막는다."""

    database_path = tmp_path / "database" / "hmda.duckdb"
    with DuckDBConnectionManager(database_path) as connection:
        load_hmda_loans(connection, [hmda_csv_path])
        before = connection.execute(
            "SELECT * FROM raw.hmda_loans ORDER BY loan_amount"
        ).fetchall()

    alias_path = tmp_path / "alias.duckdb"
    alias_path.symlink_to(database_path)
    lock_path = database_path.with_name(f".{database_path.name}.mutation.lock")
    lock_path.unlink(missing_ok=True)
    lock_path.mkdir()
    hmda_csv_path.write_text(
        hmda_csv_path.read_text(encoding="utf-8").replace("120,CA", "121,CA"),
        encoding="utf-8",
    )

    with DuckDBConnectionManager(alias_path) as connection:
        with pytest.raises(HMDADataLoadError, match="mutation lock") as raised:
            if partitioned:
                load_hmda_loans_partition(connection, [hmda_csv_path], 2025)
            else:
                load_hmda_loans(connection, [hmda_csv_path])
        assert isinstance(raised.value.__cause__, DuckDBMutationLockError)
        after = connection.execute(
            "SELECT * FROM raw.hmda_loans ORDER BY loan_amount"
        ).fetchall()

    assert after == before


def test_load_hmda_loans_rejects_malformed_csv_rows(tmp_path: Path) -> None:
    """손상된 CSV 행을 조용히 버리지 않고 적재 실패로 반환한다."""

    path = tmp_path / "malformed_2025.csv"
    path.write_text(
        "\n".join(
            [
                "activity_year,loan_purpose,action_taken,loan_amount,income,state_code,county_code",
                "2025,1,1,350000,120,CA,06001",
                "2025,1,1,350000,120,CA,06001,unexpected",
            ]
        ),
        encoding="utf-8",
    )

    with (
        DuckDBConnectionManager() as connection,
        pytest.raises((HMDADataLoadError, HMDADataValidationError)),
    ):
        load_hmda_loans(connection, [path])
