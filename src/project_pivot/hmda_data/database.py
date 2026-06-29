"""DuckDB 연결 수명주기를 관리한다."""

from __future__ import annotations

from pathlib import Path
from types import TracebackType
from uuid import uuid4

import duckdb

from project_pivot.logger import get_logger

LOGGER = get_logger(__name__)


class DuckDBConnectionManager:
    """DuckDB 연결 생성과 종료를 보장한다."""

    def __init__(
        self,
        database_path: str | Path | None = None,
        *,
        read_only: bool = False,
        cleanup_on_close: bool = False,
    ) -> None:
        self.database_path = Path(database_path) if database_path is not None else None
        self.read_only = read_only
        self.cleanup_on_close = cleanup_on_close
        self._connection: duckdb.DuckDBPyConnection | None = None

    def __enter__(self) -> duckdb.DuckDBPyConnection:
        database = ":memory:" if self.database_path is None else str(self.database_path)
        if self.database_path is not None:
            self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = duckdb.connect(database=database, read_only=self.read_only)
        LOGGER.debug(
            "DuckDB 연결 생성",
            extra={"database": database, "read_only": self.read_only},
        )
        return self._connection

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self._connection is not None:
            self._connection.close()
            self._connection = None
            LOGGER.debug("DuckDB 연결 종료")
        if self.cleanup_on_close and self.database_path is not None:
            self._remove_database_files()

    def _remove_database_files(self) -> None:
        if self.database_path is None:
            return
        database_path = self.database_path
        wal_path = Path(f"{database_path}.wal")
        for path in (database_path, wal_path):
            if path.exists():
                path.unlink()
                LOGGER.debug("DuckDB 파일 제거", extra={"path": str(path)})


def temporary_duckdb_connection(tmp_dir: str | Path) -> DuckDBConnectionManager:
    """테스트별 고유 DuckDB 파일을 생성하고 종료 시 제거한다."""

    database_path = Path(tmp_dir) / f"project_pivot_{uuid4().hex}.duckdb"
    return DuckDBConnectionManager(database_path, cleanup_on_close=True)
