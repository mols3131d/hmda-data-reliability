"""DuckDB 연결 수명, mutation lock과 schema/table metadata helper."""

from __future__ import annotations

import fcntl
from collections.abc import Iterator
from contextlib import contextmanager
from os import getpid
from pathlib import Path
from threading import local
from types import TracebackType

import duckdb

from hmda_reliability.data_platform.sql import qualify_table_name, quote_identifier
from hmda_reliability.logger import get_logger

_LOGGER = get_logger(__name__)


class _MutationLockOwnership(local):
    def __init__(self) -> None:
        self.paths: set[tuple[int, Path]] = set()


_MUTATION_LOCK_OWNERSHIP = _MutationLockOwnership()


class DuckDBMetadataError(Exception):
    """DuckDB metadata 조회 실패를 나타낸다."""


class DuckDBMutationLockError(Exception):
    """Local DuckDB mutation lock 준비·해제 I/O 실패를 나타낸다."""


@contextmanager
def database_mutation_lock(
    database_path: str | Path | None,
) -> Iterator[None]:
    """File-based DuckDB mutation을 canonical path별로 직렬화한다.

    동시성 및 락 수명 규칙:
        - `None`과 `:memory:`는 메모리 내 격리 DB이므로 파일 락 없이 no-op 통과한다.
        - 파일 기반 DB는 symlink나 relative alias에 관계없이 canonical 경로 기준의
          락 파일(`.<dbname>.mutation.lock`)을 배타적(`fcntl.LOCK_EX`)으로 획득한다.
        - 같은 process/thread의 canonical path 중첩은 outer lock을 재사용한다.
          Inner exit나 예외는 outer lock을 해제하지 않으며 다른 thread나 fork된
          child process는 별도로 lock을 획득해야 한다.
        - Body 블록의 예외는 뒤따른 unlock/close 실패보다 우선 보존된다.
        - Body가 성공한 경우에만 락 해제 실패가 `DuckDBMutationLockError`로 노출된다.

    Exceptions:
        - DuckDBMutationLockError: 락 파일 생성, 획득 또는 해제 I/O 실패 시 발생.
    """

    if database_path is None or str(database_path) == ":memory:":
        yield
        return

    canonical_path = Path(database_path).resolve(strict=False)
    ownership = (getpid(), canonical_path)
    owned_paths = _MUTATION_LOCK_OWNERSHIP.paths
    if ownership in owned_paths:
        yield
        return
    lock_path = canonical_path.with_name(f".{canonical_path.name}.mutation.lock")
    try:
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        lock_file = lock_path.open("w")
        fcntl.flock(lock_file, fcntl.LOCK_EX)
    except OSError as exc:
        msg = f"DuckDB mutation lock을 획득할 수 없습니다: {canonical_path}"
        raise DuckDBMutationLockError(msg) from exc

    owned_paths.add(ownership)
    body_failed = False
    try:
        yield
    except BaseException:
        body_failed = True
        raise
    finally:
        owned_paths.remove(ownership)
        release_error: OSError | None = None
        try:
            fcntl.flock(lock_file, fcntl.LOCK_UN)
        except OSError as exc:
            release_error = exc
        try:
            lock_file.close()
        except OSError as exc:
            release_error = release_error or exc
        if release_error is not None and not body_failed:
            msg = f"DuckDB mutation lock을 해제할 수 없습니다: {canonical_path}"
            raise DuckDBMutationLockError(msg) from release_error


def current_database_path(
    connection: duckdb.DuckDBPyConnection,
) -> Path | None:
    """Connection의 current file database path를 반환한다.

    Attached된 database 중 현재 활성 database의 파일 경로를 조회합니다.
    Isolated in-memory database(:memory:)는 ``None``을 반환합니다.
    """

    row = connection.execute(
        """
        SELECT path
        FROM duckdb_databases()
        WHERE database_name = current_database()
        """
    ).fetchone()
    if row is None or row[0] is None:
        return None
    return Path(str(row[0]))


class DuckDBConnectionManager:
    """DuckDB 연결 수명과 optional file cleanup을 관리하는 컨텍스트 매니저.

    Contract:
        - `database_path`가 없으면 `:memory:` 인메모리 데이터베이스를 사용한다.
        - 파일 데이터베이스인 경우 상위 디렉터리를 자동 생성한다.
        - `cleanup_on_close=True`면 연결 종료 후 메인 DB 파일 및 `.wal` 파일을 삭제한다.
    """

    def __init__(
        self,
        database_path: str | Path | None = None,
        *,
        read_only: bool = False,
        cleanup_on_close: bool = False,
    ) -> None:
        self.database_path: Path | None = (
            Path(database_path) if database_path is not None else None
        )
        self.read_only: bool = read_only
        self.cleanup_on_close: bool = cleanup_on_close
        self._connection: duckdb.DuckDBPyConnection | None = None

    def __enter__(self) -> duckdb.DuckDBPyConnection:
        database = ":memory:" if self.database_path is None else str(self.database_path)
        if self.database_path is not None:
            self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = duckdb.connect(database=database, read_only=self.read_only)
        _LOGGER.debug(
            "DuckDB 연결 생성",
            extra={"database": database, "read_only": self.read_only},
        )
        return self._connection

    def __exit__(
        self,
        _exc_type: type[BaseException] | None,
        _exc_value: BaseException | None,
        _traceback: TracebackType | None,
    ) -> None:
        connection = self._connection
        if connection is not None:
            connection.close()
            self._connection = None
            database = (
                ":memory:" if self.database_path is None else str(self.database_path)
            )
            _LOGGER.debug("DuckDB 연결 종료", extra={"database": database})
        if self.cleanup_on_close and self.database_path is not None:
            # DuckDB가 database/WAL file handle을 해제한 뒤에만 파일을 제거한다.
            self._remove_database_files()

    def _remove_database_files(self) -> None:
        if self.database_path is None:
            return
        database_path = self.database_path
        wal_path = Path(f"{database_path}.wal")
        for path in (database_path, wal_path):
            if path.exists():
                path.unlink()
                _LOGGER.debug("DuckDB 파일 제거", extra={"path": str(path)})


def ensure_schema(
    connection: duckdb.DuckDBPyConnection,
    schema_name: str = "raw",
) -> None:
    """DuckDB schema가 없으면 생성한다."""

    connection.execute(f"CREATE SCHEMA IF NOT EXISTS {quote_identifier(schema_name)}")


def table_row_count(
    connection: duckdb.DuckDBPyConnection,
    table_name: str,
) -> int:
    """Table 전체 행 수를 반환한다. 결과가 없으면 ``DuckDBMetadataError``다."""

    result = connection.execute(
        f"SELECT count(*) FROM {qualify_table_name(table_name)}"
    ).fetchone()
    if result is None:
        msg = f"테이블 행 수를 조회할 수 없습니다: {table_name}"
        raise DuckDBMetadataError(msg)
    return int(result[0])


def table_columns(
    connection: duckdb.DuckDBPyConnection,
    table_name: str,
) -> set[str]:
    """DuckDB table의 컬럼명 집합을 조회한다."""

    rows = connection.execute(f"DESCRIBE {qualify_table_name(table_name)}").fetchall()
    return {str(row[0]) for row in rows}
