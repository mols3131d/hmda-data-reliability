"""HMDA 연도/파일 파티션 적재 테스트."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from threading import Event, Lock, Thread

import duckdb
import pytest

import hmda_reliability.hmda_data.ingestion.partition as partition_module
from hmda_reliability.data_platform.duckdb import DuckDBConnectionManager
from hmda_reliability.hmda_data import (
    load_hmda_loans_partition,
    partition_content_identity,
    partition_max_ingested_at,
)
from hmda_reliability.hmda_data.errors import (
    HMDADataLoadError,
    HMDADataValidationError,
    HMDAStalePartitionError,
)

pytestmark = pytest.mark.component


def test_load_hmda_loans_partition_filters_by_source_year(
    hmda_csv_path: Path,
    hmda_parquet_path: Path,
) -> None:
    """source_year 기준으로 특정 연도 파일만 적재한다."""

    with DuckDBConnectionManager() as connection:
        row_count = load_hmda_loans_partition(
            connection,
            [hmda_csv_path, hmda_parquet_path],
            2025,
        )
        stats = connection.execute(
            """
            SELECT count(*), min(activity_year), max(activity_year), min(source_year)
            FROM raw.hmda_loans
            """
        ).fetchone()

    assert row_count == 2
    assert stats == (2, 2025, 2025, 2025)


def test_load_hmda_loans_partition_is_idempotent(
    hmda_csv_path: Path,
) -> None:
    """동일 source_year 재적재 시 중복 없이 덮어쓴다."""

    with DuckDBConnectionManager() as connection:
        assert load_hmda_loans_partition(connection, [hmda_csv_path], 2025) == 2
        assert load_hmda_loans_partition(connection, [hmda_csv_path], 2025) == 2

        row = connection.execute("SELECT count(*) FROM raw.hmda_loans").fetchone()

    assert row == (2,)


@pytest.mark.parametrize(
    "reverse_paths", [False, True], ids=["valid-first", "missing-first"]
)
def test_partition_load_rejects_missing_source_columns_without_changing_rows(
    hmda_csv_path: Path,
    hmda_parquet_path: Path,
    mixed_schema_source_paths: tuple[Path, Path],
    reverse_paths: bool,
) -> None:
    """누락 원천 실패 시 대상과 다른 연도의 값·provenance 전체를 보존한다."""

    valid_path, missing_path = mixed_schema_source_paths
    paths = [missing_path, valid_path] if reverse_paths else [valid_path, missing_path]
    with DuckDBConnectionManager() as connection:
        assert load_hmda_loans_partition(connection, [hmda_csv_path], 2025) == 2
        assert load_hmda_loans_partition(connection, [hmda_parquet_path], 2024) == 1
        before = connection.execute(
            "SELECT * FROM raw.hmda_loans ORDER BY source_year, loan_amount"
        ).fetchall()

        with pytest.raises(HMDADataValidationError, match="필수 컬럼") as raised:
            load_hmda_loans_partition(connection, paths, 2025)

        assert raised.value.context["missing_columns"] == ["county_code", "income"]
        assert raised.value.context["source_path"] == missing_path.as_posix()
        after = connection.execute(
            "SELECT * FROM raw.hmda_loans ORDER BY source_year, loan_amount"
        ).fetchall()

    assert len(before) == 3
    assert after == before


def test_partition_load_accepts_null_values_in_valid_csv_parquet_sources(
    nullable_mixed_source_paths: tuple[Path, Path],
) -> None:
    with DuckDBConnectionManager() as connection:
        assert (
            load_hmda_loans_partition(connection, nullable_mixed_source_paths, 2025)
            == 2
        )
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


def test_partition_load_validates_empty_requested_year_source_before_row_count(
    hmda_csv_path: Path,
    hmda_parquet_path: Path,
    tmp_path: Path,
) -> None:
    """다른 연도의 정상 컬럼이 빈 대상 원천의 구조 누락을 가리지 않아야 한다."""

    missing_path = tmp_path / "empty_missing_2025.parquet"
    with DuckDBConnectionManager() as connection:
        connection.execute(
            """
            CREATE TEMP TABLE empty_source AS
            SELECT * EXCLUDE (income, county_code)
            FROM read_parquet(?) WHERE FALSE
            """,
            [hmda_parquet_path.as_posix()],
        )
        connection.execute(
            "COPY empty_source TO ? (FORMAT PARQUET)",
            [missing_path.as_posix()],
        )
        assert load_hmda_loans_partition(connection, [hmda_csv_path], 2025) == 2
        assert load_hmda_loans_partition(connection, [hmda_parquet_path], 2024) == 1
        before = connection.execute(
            "SELECT * FROM raw.hmda_loans ORDER BY source_year, loan_amount"
        ).fetchall()

        with pytest.raises(HMDADataValidationError, match="필수 컬럼") as raised:
            load_hmda_loans_partition(
                connection,
                [hmda_parquet_path, missing_path],
                2025,
            )

        assert raised.value.context["missing_columns"] == ["county_code", "income"]
        assert raised.value.context["source_path"] == missing_path.as_posix()
        after = connection.execute(
            "SELECT * FROM raw.hmda_loans ORDER BY source_year, loan_amount"
        ).fetchall()

    assert len(before) == 3
    assert after == before


def test_partition_load_rejects_empty_requested_year_with_valid_source_columns(
    hmda_csv_path: Path,
    hmda_parquet_path: Path,
    tmp_path: Path,
) -> None:
    empty_path = tmp_path / "empty_valid_2025.parquet"
    with DuckDBConnectionManager() as connection:
        connection.execute(
            """
            CREATE TEMP TABLE empty_source AS
            SELECT * FROM read_parquet(?) WHERE FALSE
            """,
            [hmda_parquet_path.as_posix()],
        )
        connection.execute(
            "COPY empty_source TO ? (FORMAT PARQUET)",
            [empty_path.as_posix()],
        )
        assert load_hmda_loans_partition(connection, [hmda_csv_path], 2025) == 2
        assert load_hmda_loans_partition(connection, [hmda_parquet_path], 2024) == 1
        before = connection.execute(
            "SELECT * FROM raw.hmda_loans ORDER BY source_year, loan_amount"
        ).fetchall()

        with pytest.raises(HMDADataLoadError, match="적재할 행이 없습니다"):
            load_hmda_loans_partition(
                connection,
                [hmda_parquet_path, empty_path],
                2025,
            )

        after = connection.execute(
            "SELECT * FROM raw.hmda_loans ORDER BY source_year, loan_amount"
        ).fetchall()

    assert len(before) == 3
    assert after == before


def test_partition_reload_preserves_values_after_source_columns_are_reordered(
    hmda_csv_path: Path,
    hmda_parquet_path: Path,
) -> None:
    with DuckDBConnectionManager() as connection:
        load_hmda_loans_partition(connection, [hmda_csv_path], 2025)
        load_hmda_loans_partition(connection, [hmda_parquet_path], 2024)
        other_partition = connection.execute(
            "SELECT * FROM raw.hmda_loans WHERE source_year = 2024"
        ).fetchall()
        hmda_csv_path.write_text(
            "activity_year,loan_purpose,action_taken,income,loan_amount,"
            "state_code,county_code\n"
            "2025,1,1,120,350000,CA,06001\n"
            "2025,31,3,95,420000,NY,36061\n",
            encoding="utf-8",
        )

        assert load_hmda_loans_partition(connection, [hmda_csv_path], 2025) == 2

        assert connection.execute(
            "SELECT loan_amount, income FROM raw.hmda_loans "
            "WHERE source_year = 2025 ORDER BY loan_amount"
        ).fetchall() == [(350000, 120), (420000, 95)]
        assert (
            connection.execute(
                "SELECT * FROM raw.hmda_loans WHERE source_year = 2024"
            ).fetchall()
            == other_partition
        )


def test_partition_insert_failure_rolls_back_deleted_rows(
    hmda_csv_path: Path,
    hmda_parquet_path: Path,
) -> None:
    """실제 INSERT 제약 실패 뒤 기존 값·provenance와 staging 정리를 확인한다."""

    with DuckDBConnectionManager() as connection:
        load_hmda_loans_partition(connection, [hmda_csv_path], 2025)
        load_hmda_loans_partition(connection, [hmda_parquet_path], 2024)
        connection.execute(
            "CREATE UNIQUE INDEX unique_loan_amount ON raw.hmda_loans (loan_amount)"
        )
        before = connection.execute(
            "SELECT * FROM raw.hmda_loans ORDER BY source_year, loan_amount"
        ).fetchall()
        hmda_csv_path.write_text(
            hmda_csv_path.read_text(encoding="utf-8").replace("420000", "350000"),
            encoding="utf-8",
        )

        with pytest.raises(HMDADataLoadError, match="파티션 적재") as raised:
            load_hmda_loans_partition(connection, [hmda_csv_path], 2025)

        assert isinstance(raised.value.__cause__, duckdb.ConstraintException)
        after = connection.execute(
            "SELECT * FROM raw.hmda_loans ORDER BY source_year, loan_amount"
        ).fetchall()
        staging_tables = connection.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_name = '__hmda_loans_partition_stage'"
        ).fetchall()

    assert len(before) == 3
    assert after == before
    assert staging_tables == []


def test_file_scoped_reload_preserves_same_year_sibling(
    hmda_csv_path: Path,
    tmp_path: Path,
) -> None:
    sibling_path = tmp_path / "sibling_2025.csv"
    sibling_path.write_text(
        hmda_csv_path.read_text(encoding="utf-8").replace("120,CA", "777,CA"),
        encoding="utf-8",
    )
    with DuckDBConnectionManager() as connection:
        assert (
            load_hmda_loans_partition(connection, [hmda_csv_path, sibling_path], 2025)
            == 4
        )
        sibling_before = connection.execute(
            "SELECT * FROM raw.hmda_loans "
            "WHERE source_file_name = ? ORDER BY loan_amount",
            [sibling_path.name],
        ).fetchall()
        hmda_csv_path.write_text(
            hmda_csv_path.read_text(encoding="utf-8").replace("120,CA", "121,CA"),
            encoding="utf-8",
        )

        assert (
            load_hmda_loans_partition(
                connection,
                [hmda_csv_path, sibling_path],
                2025,
                source_file=hmda_csv_path.name,
            )
            == 2
        )
        selected_rows = connection.execute(
            "SELECT loan_amount, income FROM raw.hmda_loans "
            "WHERE source_file_name = ? ORDER BY loan_amount",
            [hmda_csv_path.name],
        ).fetchall()
        sibling_after = connection.execute(
            "SELECT * FROM raw.hmda_loans "
            "WHERE source_file_name = ? ORDER BY loan_amount",
            [sibling_path.name],
        ).fetchall()

    assert selected_rows == [(350000, 121), (420000, 95)]
    assert len(sibling_before) == 2
    assert sibling_after == sibling_before


def test_partition_content_identity_tracks_logical_row_multiset(
    hmda_csv_path: Path,
) -> None:
    """Identity는 row order/ingestion time을 무시하고 value와 duplicate를 보존한다."""

    with DuckDBConnectionManager() as connection:
        load_hmda_loans_partition(connection, [hmda_csv_path], 2025)
        baseline = partition_content_identity(connection, source_year=2025)

        connection.execute(
            """
            CREATE OR REPLACE TABLE reordered AS
            SELECT * REPLACE (ingested_at + INTERVAL '1 day' AS ingested_at)
            FROM raw.hmda_loans
            ORDER BY loan_amount DESC
            """
        )
        connection.execute("CREATE OR REPLACE TABLE raw.hmda_loans AS FROM reordered")
        reordered = partition_content_identity(connection, source_year=2025)

        connection.execute(
            """
            UPDATE raw.hmda_loans
            SET income = income + 1
            WHERE loan_amount = 350000
            """
        )
        changed_value = partition_content_identity(connection, source_year=2025)

        connection.execute(
            """
            INSERT INTO raw.hmda_loans
            SELECT *
            FROM raw.hmda_loans
            WHERE loan_amount = 350000
            LIMIT 1
            """
        )
        duplicated = partition_content_identity(connection, source_year=2025)

    assert reordered == baseline
    assert changed_value != baseline
    assert duplicated != changed_value


def test_partition_load_compares_expected_identity_before_replacement(
    hmda_csv_path: Path,
    tmp_path: Path,
) -> None:
    """Stale expected identity는 transaction 안에서 zero mutation으로 실패한다."""

    replacement_path = tmp_path / "year_2025_replacement.csv"
    replacement_path.write_text(
        hmda_csv_path.read_text(encoding="utf-8").replace("120,CA", "121,CA"),
        encoding="utf-8",
    )
    with DuckDBConnectionManager() as connection:
        load_hmda_loans_partition(connection, [hmda_csv_path], 2025)
        before = partition_content_identity(connection, source_year=2025)
        assert (
            load_hmda_loans_partition(
                connection,
                [replacement_path],
                2025,
                expected_identity=before,
            )
            == 2
        )
        replaced = partition_content_identity(connection, source_year=2025)

        with pytest.raises(HMDAStalePartitionError, match="stale"):
            load_hmda_loans_partition(
                connection,
                [hmda_csv_path],
                2025,
                expected_identity=before,
            )
        after_stale = partition_content_identity(connection, source_year=2025)

    assert replaced != before
    assert after_stale == replaced


def test_partition_load_rechecks_identity_after_waiting_for_writer(
    hmda_csv_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """대기 중 선행 writer가 commit하면 후행 request는 stale로 거부한다."""

    database_path = tmp_path / "hmda-reliability.duckdb"
    first_source = tmp_path / "year_2025_first.csv"
    second_source = tmp_path / "year_2025_second.csv"
    source_text = hmda_csv_path.read_text(encoding="utf-8")
    first_source.write_text(source_text.replace("120,CA", "121,CA"), encoding="utf-8")
    second_source.write_text(source_text.replace("120,CA", "122,CA"), encoding="utf-8")

    with DuckDBConnectionManager(database_path) as connection:
        load_hmda_loans_partition(connection, [hmda_csv_path], 2025)
        before = partition_content_identity(connection, source_year=2025)

    writer_gate = Lock()
    first_entered = Event()
    release_first = Event()
    second_attempted = Event()
    invocation_guard = Lock()
    invocation_count = 0

    @contextmanager
    def serialized_lock(database: str | Path | None):
        del database
        nonlocal invocation_count
        with invocation_guard:
            invocation_index = invocation_count
            invocation_count += 1
        if invocation_index == 1:
            second_attempted.set()
        with writer_gate:
            if invocation_index == 0:
                first_entered.set()
                assert release_first.wait(timeout=1)
            yield

    monkeypatch.setattr(partition_module, "database_mutation_lock", serialized_lock)
    failures: list[BaseException] = []

    def replace_partition(source_path: Path) -> None:
        try:
            with DuckDBConnectionManager(database_path) as connection:
                load_hmda_loans_partition(
                    connection,
                    [source_path],
                    2025,
                    expected_identity=before,
                )
        except BaseException as exc:
            failures.append(exc)

    first_writer = Thread(target=replace_partition, args=(first_source,), daemon=True)
    second_writer = Thread(target=replace_partition, args=(second_source,), daemon=True)
    first_writer.start()
    assert first_entered.wait(timeout=1)
    second_writer.start()
    assert second_attempted.wait(timeout=1)
    assert second_writer.is_alive()

    release_first.set()
    first_writer.join(timeout=2)
    second_writer.join(timeout=2)

    assert not first_writer.is_alive()
    assert not second_writer.is_alive()
    assert len(failures) == 1
    assert isinstance(failures[0], HMDAStalePartitionError)


def test_partition_load_compares_expected_freshness_before_replacement(
    hmda_csv_path: Path,
) -> None:
    """Content가 같아도 transaction 내부 temporal drift는 zero mutation이다."""

    with DuckDBConnectionManager() as connection:
        load_hmda_loans_partition(connection, [hmda_csv_path], 2025)
        identity = partition_content_identity(connection, source_year=2025)
        expected_freshness = partition_max_ingested_at(
            connection,
            source_year=2025,
        )
        assert expected_freshness is not None
        connection.execute(
            """
            UPDATE raw.hmda_loans
            SET ingested_at = TIMESTAMPTZ '2026-08-15 00:00:00+00'
            WHERE source_year = 2025
            """
        )
        before = connection.execute(
            "SELECT * FROM raw.hmda_loans ORDER BY loan_amount"
        ).fetchall()

        with pytest.raises(HMDAStalePartitionError, match="stale"):
            load_hmda_loans_partition(
                connection,
                [hmda_csv_path],
                2025,
                expected_identity=identity,
                expected_max_ingested_at=expected_freshness,
            )

        after = partition_max_ingested_at(connection, source_year=2025)
        after_rows = connection.execute(
            "SELECT * FROM raw.hmda_loans ORDER BY loan_amount"
        ).fetchall()

    assert after == datetime(2026, 8, 15, 0, 0, tzinfo=UTC)
    assert after_rows == before


def test_partition_load_preserves_approved_bronze_metadata(
    hmda_csv_path: Path,
    tmp_path: Path,
) -> None:
    candidate_path = tmp_path / "candidate.parquet"
    approved_at = datetime(2026, 8, 15, 9, 0, tzinfo=UTC)

    with DuckDBConnectionManager() as connection:
        load_hmda_loans_partition(connection, [hmda_csv_path], 2025)
        connection.execute(
            "UPDATE raw.hmda_loans SET ingested_at = ? WHERE source_year = 2025",
            [approved_at],
        )
        connection.execute(
            "COPY raw.hmda_loans TO ? (FORMAT PARQUET)",
            [candidate_path.as_posix()],
        )
        before = partition_content_identity(connection, source_year=2025)
        before_freshness = partition_max_ingested_at(connection, source_year=2025)
        assert before_freshness is not None
        approved_rows = connection.execute(
            "SELECT * FROM raw.hmda_loans ORDER BY loan_amount"
        ).fetchall()

        load_hmda_loans_partition(
            connection,
            [candidate_path],
            2025,
            expected_identity=before,
            expected_max_ingested_at=before_freshness,
            preserve_source_metadata=True,
        )
        metadata = connection.execute(
            """
            SELECT min(source_year), min(source_file_name), max(ingested_at)
            FROM raw.hmda_loans
            WHERE source_year = 2025
            """
        ).fetchone()
        actual_rows = connection.execute(
            "SELECT * FROM raw.hmda_loans ORDER BY loan_amount"
        ).fetchall()

    assert metadata == (2025, hmda_csv_path.name, approved_at)
    assert actual_rows == approved_rows


@pytest.mark.parametrize(
    "candidate_projection",
    [
        "* EXCLUDE (ingested_at)",
        "* REPLACE (CAST(loan_amount AS VARCHAR) AS loan_amount)",
    ],
    ids=["missing-provenance", "incompatible-schema"],
)
def test_partition_load_rejects_invalid_preserved_candidate_before_mutation(
    hmda_csv_path: Path,
    tmp_path: Path,
    candidate_projection: str,
) -> None:
    candidate_path = tmp_path / "invalid-candidate.parquet"

    with DuckDBConnectionManager() as connection:
        load_hmda_loans_partition(connection, [hmda_csv_path], 2025)
        before = partition_content_identity(connection, source_year=2025)
        before_rows = connection.execute(
            "SELECT * FROM raw.hmda_loans ORDER BY loan_amount"
        ).fetchall()
        connection.execute(
            f"""
            COPY (
                SELECT {candidate_projection}
                FROM raw.hmda_loans
            ) TO ? (FORMAT PARQUET)
            """,
            [candidate_path.as_posix()],
        )

        with pytest.raises(HMDADataLoadError, match="metadata|provenance|schema"):
            load_hmda_loans_partition(
                connection,
                [candidate_path],
                2025,
                expected_identity=before,
                preserve_source_metadata=True,
            )
        after = partition_content_identity(connection, source_year=2025)
        after_rows = connection.execute(
            "SELECT * FROM raw.hmda_loans ORDER BY loan_amount"
        ).fetchall()

    assert after == before
    assert after_rows == before_rows


def test_partition_load_creates_custom_target_schema(hmda_csv_path: Path) -> None:
    """파티션 적재는 configured qualified target의 schema를 새 DB에 생성한다."""

    with DuckDBConnectionManager() as connection:
        row_count = load_hmda_loans_partition(
            connection,
            [hmda_csv_path],
            2025,
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


def test_partition_load_rejects_multipart_target_table(hmda_csv_path: Path) -> None:
    """현재 loader contract 밖의 multipart target은 schema 생성 전에 거부한다."""

    with (
        DuckDBConnectionManager() as connection,
        pytest.raises(HMDADataLoadError, match="target table"),
    ):
        load_hmda_loans_partition(
            connection,
            [hmda_csv_path],
            2025,
            table_name="catalog.bronze.hmda_loans",
        )


def test_load_hmda_loans_partition_filters_by_source_file(
    hmda_csv_path: Path,
    hmda_parquet_path: Path,
) -> None:
    """source_file이 지정되면 해당 파일만 적재한다."""

    with DuckDBConnectionManager() as connection:
        row_count = load_hmda_loans_partition(
            connection,
            [hmda_csv_path, hmda_parquet_path],
            2024,
            source_file=hmda_parquet_path.name,
        )
        source_files = connection.execute(
            """
            SELECT DISTINCT source_file_name
            FROM raw.hmda_loans
            """
        ).fetchall()

    assert row_count == 1
    assert source_files == [(hmda_parquet_path.name,)]


def test_load_hmda_loans_partition_preserves_outlier_rows(tmp_path: Path) -> None:
    """비정상 HMDA 값도 품질 감지 evidence를 위해 보존한다."""

    path = tmp_path / "year_2025.csv"
    path.write_text(
        "\n".join(
            [
                "activity_year,loan_purpose,action_taken,loan_amount,income,state_code,county_code",
                "2025,1,99,999999999999,-10,ZZ,99999",
            ]
        ),
        encoding="utf-8",
    )

    with DuckDBConnectionManager() as connection:
        assert load_hmda_loans_partition(connection, [path], 2025) == 1
        row = connection.execute(
            """
            SELECT action_taken, loan_amount, income, state_code, county_code
            FROM raw.hmda_loans
            """
        ).fetchone()

    assert row == (99, 999999999999, -10, "ZZ", 99999)


def test_load_hmda_loans_partition_handles_empty_source_file(
    hmda_csv_path: Path,
) -> None:
    """빈 source_file도 SQL binding 오류 대신 도메인 오류로 반환한다."""

    with (
        DuckDBConnectionManager() as connection,
        pytest.raises(HMDADataLoadError, match="적재할 행이 없습니다"),
    ):
        load_hmda_loans_partition(
            connection,
            [hmda_csv_path],
            2025,
            source_file="",
        )
