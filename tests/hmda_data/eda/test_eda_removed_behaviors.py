"""Removed behaviors regression tests (Freshness removal, anomaly removal)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import duckdb
import pytest

from project_pivot.hmda_data.eda.analysis import analyze_hmda_csv

pytestmark = pytest.mark.component


def test_observed_at_column_does_not_trigger_freshness_query_or_evidence_key(
    tmp_path: Path,
) -> None:
    """observed_at이 있어도 MAX(observed_at) 쿼리와 freshness 반환 키가 없다."""
    csv_file = tmp_path / "hmda_with_observed_at.csv"
    csv_file.write_text(
        "activity_year,state_code,loan_purpose,action_taken,loan_amount,income,observed_at\n"
        "2025,CA,1,1,100000,50000,2025-01-01T00:00:00Z\n"
        "2025,NY,1,2,200000,80000,2025-01-02T00:00:00Z\n",
        encoding="utf-8",
    )

    executed_sqls: list[str] = []
    original_execute = duckdb.DuckDBPyConnection.execute

    def tracking_execute(
        self: duckdb.DuckDBPyConnection, query: str, *args: object, **kwargs: object
    ) -> duckdb.DuckDBPyConnection:
        executed_sqls.append(str(query))
        return original_execute(self, query, *args, **kwargs)

    with patch.object(duckdb.DuckDBPyConnection, "execute", new=tracking_execute):
        evidence = analyze_hmda_csv(
            source_path=csv_file,
            temp_directory=tmp_path / "tmp",
        )

    # 1. 반환 evidence에 freshness 키가 없어야 한다
    assert "freshness" not in evidence
    assert "observed_at" not in evidence

    # 2. 실행된 SQL 조각에 MAX(observed_at)이나 freshness 문구가 없어야 한다
    all_sqls = " ".join(executed_sqls).lower()
    assert "max(observed_at)" not in all_sqls
    assert "freshness" not in all_sqls
