"""DuckDB 데이터 플랫폼 헬퍼 테스트."""

from __future__ import annotations

from pathlib import Path

from project_pivot.data_platform.duckdb import DuckDBConnectionManager


def test_duckdb_connection_manager_removes_database_file(tmp_path: Path) -> None:
    """cleanup_on_close가 연결 종료 후 DB 파일을 제거하는지 검증한다."""

    manager = DuckDBConnectionManager(
        tmp_path / "project_pivot_test.duckdb",
        cleanup_on_close=True,
    )
    database_path = manager.database_path
    assert database_path is not None

    with manager as connection:
        connection.execute("CREATE TABLE probe AS SELECT 1 AS value")
        assert database_path.exists()

    assert not database_path.exists()
