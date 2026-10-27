"""실제 DuckDB 연결·metadata와 단일 호스트 mutation lock의 계약을 검증한다."""

from __future__ import annotations

from contextlib import nullcontext
from multiprocessing import get_context
from multiprocessing.synchronize import Event as ProcessEvent
from pathlib import Path
from threading import Event, Thread

import duckdb
import pytest

import hmda_reliability.data_platform as data_platform
import hmda_reliability.data_platform.duckdb as duckdb_module
from hmda_reliability.data_platform.duckdb import (
    DuckDBConnectionManager,
    DuckDBMutationLockError,
    current_database_path,
    database_mutation_lock,
    ensure_schema,
    table_columns,
    table_row_count,
)

pytestmark = pytest.mark.component


@pytest.mark.parametrize("body_failure", [False, True], ids=["success", "exception"])
def test_duckdb_connection_manager_closes_connection_after_scope(
    body_failure: bool,
) -> None:
    expected_error = (
        pytest.raises(ValueError, match="connection body failed")
        if body_failure
        else nullcontext()
    )

    with expected_error, DuckDBConnectionManager() as connection:
        assert connection.execute("SELECT 7").fetchone() == (7,)
        if body_failure:
            raise ValueError("connection body failed")

    with pytest.raises(duckdb.ConnectionException, match="closed"):
        connection.execute("SELECT 7")


def test_duckdb_connection_manager_isolates_in_memory_databases() -> None:
    with (
        DuckDBConnectionManager() as first,
        DuckDBConnectionManager() as second,
    ):
        first.execute("CREATE TABLE private_probe AS SELECT 7 AS value")

        assert current_database_path(first) is None
        assert current_database_path(second) is None
        with pytest.raises(duckdb.CatalogException, match="private_probe"):
            second.execute("SELECT * FROM private_probe")
        assert first.execute("SELECT * FROM private_probe").fetchall() == [(7,)]


def test_duckdb_read_only_connection_rejects_writes(tmp_path: Path) -> None:
    database_path = tmp_path / "nested" / "probe.duckdb"
    with DuckDBConnectionManager(database_path) as connection:
        connection.execute("CREATE TABLE probe AS SELECT 7 AS value")

    with DuckDBConnectionManager(database_path, read_only=True) as connection:
        assert current_database_path(connection) == database_path
        assert connection.execute("SELECT * FROM probe").fetchall() == [(7,)]
        with pytest.raises(duckdb.InvalidInputException, match="read-only"):
            connection.execute("INSERT INTO probe VALUES (9)")

    with DuckDBConnectionManager(database_path) as connection:
        assert connection.execute("SELECT * FROM probe").fetchall() == [(7,)]


def test_duckdb_schema_and_metadata_preserve_quoted_names_and_null_rows() -> None:
    with DuckDBConnectionManager() as connection:
        ensure_schema(connection, 'probe"schema')
        ensure_schema(connection, 'probe"schema')
        connection.execute(
            'CREATE TABLE "probe""schema"."loans""table" '
            '("borrower""id" INTEGER, amount INTEGER)'
        )
        assert table_row_count(connection, 'probe"schema.loans"table') == 0
        connection.execute(
            'INSERT INTO "probe""schema"."loans""table" '
            "VALUES (1, 5), (1, 5), (NULL, NULL)"
        )

        assert table_row_count(connection, 'probe"schema.loans"table') == 3
        assert table_columns(connection, 'probe"schema.loans"table') == {
            'borrower"id',
            "amount",
        }


def test_duckdb_connection_manager_removes_database_file(tmp_path: Path) -> None:
    """cleanup_on_close가 연결 종료 후 DB 파일을 제거하는지 검증한다."""

    manager = DuckDBConnectionManager(
        tmp_path / "hmda_reliability_test.duckdb",
        cleanup_on_close=True,
    )
    database_path = manager.database_path
    assert database_path is not None

    with manager as connection:
        connection.execute("CREATE TABLE probe AS SELECT 1 AS value")
        assert database_path.exists()

    assert not database_path.exists()


@pytest.mark.parametrize("alias_kind", ["relative", "symlink"])
def test_database_mutation_lock_serializes_canonical_aliases(
    alias_kind: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """같은 canonical database의 alias는 하나의 exclusive lock을 사용한다."""

    database_path = tmp_path / "hmda-reliability.duckdb"
    database_path.touch()
    if alias_kind == "relative":
        monkeypatch.chdir(tmp_path)
        alias_path = Path(database_path.name)
    else:
        alias_path = tmp_path / "hmda-reliability-alias.duckdb"
        alias_path.symlink_to(database_path)

    attempted = Event()
    acquired = Event()

    def acquire_alias() -> None:
        attempted.set()
        with database_mutation_lock(alias_path):
            acquired.set()

    with database_mutation_lock(database_path):
        worker = Thread(target=acquire_alias, daemon=True)
        worker.start()
        assert attempted.wait(timeout=1)
        assert not acquired.wait(timeout=0.05)

    assert acquired.wait(timeout=1)
    worker.join(timeout=1)
    assert not worker.is_alive()


def _exercise_nested_mutation_lock(
    database_path: Path,
    alias_path: Path,
    inner_failure: bool,
) -> None:
    attempted = Event()
    acquired = Event()

    def acquire_alias() -> None:
        attempted.set()
        with database_mutation_lock(alias_path):
            acquired.set()

    with database_mutation_lock(database_path):
        expected_error = (
            pytest.raises(ValueError, match="nested mutation failed")
            if inner_failure
            else nullcontext()
        )
        with expected_error, database_mutation_lock(alias_path):
            if inner_failure:
                raise ValueError("nested mutation failed")

        worker = Thread(target=acquire_alias, daemon=True)
        worker.start()
        assert attempted.wait(timeout=1)
        assert not acquired.wait(timeout=0.05)

    assert acquired.wait(timeout=1)
    worker.join(timeout=1)
    assert not worker.is_alive()


@pytest.mark.parametrize("alias_kind", ["relative", "symlink"])
@pytest.mark.parametrize("inner_failure", [False, True], ids=["success", "exception"])
def test_database_mutation_lock_reenters_alias_without_releasing_outer_lock(
    alias_kind: str,
    inner_failure: bool,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """중첩 획득의 deadlock은 격리하고 outer lock의 thread 배타성을 보존한다."""

    database_path = tmp_path / "hmda-reliability.duckdb"
    database_path.touch()
    if alias_kind == "relative":
        monkeypatch.chdir(tmp_path)
        alias_path = Path(database_path.name)
    else:
        alias_path = tmp_path / "hmda-reliability-alias.duckdb"
        alias_path.symlink_to(database_path)

    worker = get_context("spawn").Process(
        target=_exercise_nested_mutation_lock,
        args=(database_path, alias_path, inner_failure),
    )
    worker.start()
    try:
        worker.join(timeout=3)
        assert worker.exitcode == 0, (
            "nested mutation lock did not complete successfully"
        )
    finally:
        if worker.is_alive():
            worker.kill()
            worker.join(timeout=1)
        worker.close()


def _acquire_forked_mutation_lock(
    database_path: Path,
    attempted: ProcessEvent,
    acquired: ProcessEvent,
) -> None:
    attempted.set()
    with database_mutation_lock(database_path):
        acquired.set()


def test_database_mutation_lock_does_not_inherit_reentrancy_after_fork(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "hmda-reliability.duckdb"
    context = get_context("fork")
    attempted = context.Event()
    acquired = context.Event()
    worker = context.Process(
        target=_acquire_forked_mutation_lock,
        args=(database_path, attempted, acquired),
    )

    try:
        with database_mutation_lock(database_path):
            worker.start()
            assert attempted.wait(timeout=1)
            assert not acquired.wait(timeout=0.05)

        assert acquired.wait(timeout=1)
        worker.join(timeout=1)
        assert worker.exitcode == 0
    finally:
        if worker.pid is not None:
            if worker.is_alive():
                worker.kill()
                worker.join(timeout=1)
            worker.close()


def test_database_mutation_lock_is_noop_for_in_memory_database(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """In-memory mutation boundary는 file을 생성하지 않는다."""

    def fail_open(*args: object, **kwargs: object) -> None:
        raise AssertionError("in-memory lock must not open a file")

    monkeypatch.setattr(Path, "open", fail_open)

    with database_mutation_lock(None):
        pass

    assert (
        getattr(data_platform, "DuckDBMutationLockError", None)
        is DuckDBMutationLockError
    )
    assert (
        getattr(data_platform, "database_mutation_lock", None) is database_mutation_lock
    )


@pytest.mark.parametrize("failure_stage", ["prepare", "acquire"])
def test_database_mutation_lock_acquisition_failure_is_typed(
    failure_stage: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Lock 준비·획득 I/O failure는 body 진입 전에 typed error로 변환한다."""

    failure = OSError("cannot acquire mutation lock")

    def fail_lock_io(*args: object, **kwargs: object) -> None:
        raise failure

    if failure_stage == "prepare":
        monkeypatch.setattr(Path, "mkdir", fail_lock_io)
    else:
        monkeypatch.setattr(duckdb_module.fcntl, "flock", fail_lock_io)

    with (
        pytest.raises(DuckDBMutationLockError, match="lock") as error,
        database_mutation_lock(tmp_path / "nested" / "hmda-reliability.duckdb"),
    ):
        pytest.fail("mutation body must not run after lock acquisition failure")

    assert error.value.__cause__ is failure


def test_database_mutation_lock_release_failure_is_typed(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """성공한 body 뒤 release failure는 typed error로 변환한다."""

    original_flock = duckdb_module.fcntl.flock

    def fail_unlock(file_descriptor: int, operation: int) -> None:
        if operation == duckdb_module.fcntl.LOCK_UN:
            raise OSError("cannot release mutation lock")
        original_flock(file_descriptor, operation)

    monkeypatch.setattr(duckdb_module.fcntl, "flock", fail_unlock)

    with (
        pytest.raises(DuckDBMutationLockError, match="lock"),
        database_mutation_lock(tmp_path / "hmda-reliability.duckdb"),
    ):
        pass


def test_database_mutation_lock_preserves_body_failure(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Body와 release가 모두 실패하면 원래 body failure를 보존한다."""

    original_flock = duckdb_module.fcntl.flock

    class MutationBodyError(Exception):
        pass

    def fail_unlock(file_descriptor: int, operation: int) -> None:
        if operation == duckdb_module.fcntl.LOCK_UN:
            raise OSError("cannot release mutation lock")
        original_flock(file_descriptor, operation)

    monkeypatch.setattr(duckdb_module.fcntl, "flock", fail_unlock)

    with (
        pytest.raises(MutationBodyError),
        database_mutation_lock(tmp_path / "hmda-reliability.duckdb"),
    ):
        raise MutationBodyError
