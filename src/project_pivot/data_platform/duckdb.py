"""DuckDB 연결 수명과 schema/table metadata helper."""

from pathlib import Path
from types import TracebackType

import duckdb

from project_pivot.data_platform.sql import qualify_table_name, quote_identifier
from project_pivot.logger import get_logger

_LOGGER = get_logger(__name__)


class DuckDBMetadataError(Exception):
    """DuckDB metadata 조회 실패를 나타낸다."""


class DuckDBConnectionManager:
    """DuckDB 연결 수명과 optional file cleanup을 관리한다.

    경로가 없으면 in-memory DB를 사용한다. File DB는 상위 directory를 만들며,
    ``cleanup_on_close=True``면 연결 종료 후 database와 ``.wal`` 파일을 제거한다.
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
            _LOGGER.debug(
                "DuckDB 연결 종료",
                extra={
                    "database": (
                        ":memory:"
                        if self.database_path is None
                        else str(self.database_path)
                    )
                },
            )
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
