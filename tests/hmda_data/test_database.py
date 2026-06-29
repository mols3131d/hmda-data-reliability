"""DuckDB 데이터베이스 세션 및 커넥션 테스트."""

from __future__ import annotations

from pathlib import Path

from project_pivot.hmda_data import temporary_duckdb_connection


def test_temporary_duckdb_connection_removes_database_file(tmp_path: Path) -> None:
    """임시 DuckDB 컨텍스트가 연결을 닫고 파일을 제거하는지 검증한다."""

    manager = temporary_duckdb_connection(tmp_path)
    database_path = manager.database_path
    assert database_path is not None

    with manager as connection:
        connection.execute("CREATE TABLE probe AS SELECT 1 AS value")
        assert database_path.exists()

    assert not database_path.exists()
