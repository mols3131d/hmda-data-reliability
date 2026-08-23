"""HMDA 연도/파일 파티션 적재 테스트."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from threading import Event, Lock, Thread

import pytest

import hmda_reliability.hmda_data.ingestion.partition as partition_module
from hmda_reliability.data_platform.duckdb import DuckDBConnectionManager
from hmda_reliability.hmda_data import (
    load_hmda_loans_partition,
    partition_content_identity,
    partition_max_ingested_at,
)
from hmda_reliability.hmda_data.errors import HMDADataLoadError, HMDAStalePartitionError

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

    database_path = tmp_path / "project-pivot.duckdb"
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

        with pytest.raises(HMDAStalePartitionError, match="stale"):
            load_hmda_loans_partition(
                connection,
                [hmda_csv_path],
                2025,
                expected_identity=identity,
                expected_max_ingested_at=expected_freshness,
            )

        after = partition_max_ingested_at(connection, source_year=2025)

    assert after == datetime(2026, 8, 15, 0, 0, tzinfo=UTC)


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

    assert metadata == (2025, hmda_csv_path.name, approved_at)


def test_partition_load_rejects_missing_preserved_provenance_before_mutation(
    hmda_csv_path: Path,
    tmp_path: Path,
) -> None:
    candidate_path = tmp_path / "candidate-without-ingested-at.parquet"

    with DuckDBConnectionManager() as connection:
        load_hmda_loans_partition(connection, [hmda_csv_path], 2025)
        before = partition_content_identity(connection, source_year=2025)
        connection.execute(
            """
            COPY (
                SELECT * EXCLUDE (ingested_at)
                FROM raw.hmda_loans
            ) TO ? (FORMAT PARQUET)
            """,
            [candidate_path.as_posix()],
        )

        with pytest.raises(HMDADataLoadError, match="metadata|provenance"):
            load_hmda_loans_partition(
                connection,
                [candidate_path],
                2025,
                expected_identity=before,
                preserve_source_metadata=True,
            )
        after = partition_content_identity(connection, source_year=2025)

    assert after == before


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
