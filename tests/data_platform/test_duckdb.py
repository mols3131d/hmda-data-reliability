"""DuckDB 데이터 플랫폼 헬퍼 테스트."""

from __future__ import annotations

from pathlib import Path
from threading import Event, Thread

import pytest

import hmda_reliability.data_platform as data_platform
import hmda_reliability.data_platform.duckdb as duckdb_module
from hmda_reliability.data_platform.duckdb import (
    DuckDBConnectionManager,
    DuckDBMutationLockError,
    database_mutation_lock,
)

pytestmark = pytest.mark.component


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


def test_database_mutation_lock_setup_failure_is_typed(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Lock 준비 I/O failure는 typed Data Platform error로 변환한다."""

    def fail_mkdir(*args: object, **kwargs: object) -> None:
        raise OSError("cannot create mutation lock directory")

    monkeypatch.setattr(Path, "mkdir", fail_mkdir)

    with (
        pytest.raises(DuckDBMutationLockError, match="lock"),
        database_mutation_lock(tmp_path / "nested" / "hmda-reliability.duckdb"),
    ):
        pass


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
