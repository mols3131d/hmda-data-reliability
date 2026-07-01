"""HMDA 데이터 테스트용 pytest fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

from project_pivot.hmda_data import DuckDBConnectionManager
from project_pivot.shared.sql import quote_string_literal


@pytest.fixture
def hmda_csv_path(tmp_path: Path) -> Path:
    """테스트용 HMDA CSV 파일을 생성한다."""

    path = tmp_path / "year_2025.csv"
    path.write_text(
        "\n".join(
            [
                "activity_year,loan_purpose,action_taken,loan_amount,income,state_code,county_code",
                "2025,1,1,350000,120,CA,06001",
                "2025,31,3,420000,95,NY,36061",
            ]
        ),
        encoding="utf-8",
    )
    return path


@pytest.fixture
def hmda_parquet_path(tmp_path: Path) -> Path:
    """테스트용 HMDA Parquet 파일을 생성한다."""

    path = tmp_path / "hmda_2024.parquet"
    target_path = quote_string_literal(str(path))
    with DuckDBConnectionManager() as connection:
        connection.execute(
            f"""
            COPY (
                SELECT
                    2024 AS activity_year,
                    1 AS loan_purpose,
                    2 AS action_taken,
                    250000 AS loan_amount,
                    88 AS income,
                    'TX' AS state_code,
                    '48113' AS county_code
            )
            TO {target_path}
            (FORMAT PARQUET)
            """
        )
    return path
