"""HMDA EDA process-level memory workload 테스트."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from project_pivot.hmda_data.eda_memory import run_hmda_eda_memory_workload

pytestmark = pytest.mark.memory


def test_hmda_eda_representative_memory_workload() -> None:
    """Runner가 제공한 대표 fixture의 결과 invariant를 검증한다."""

    fixture_directory = Path(os.environ["HMDA_EDA_FIXTURE_DIR"])
    temp_directory = Path(os.environ["HMDA_EDA_TEMP_DIR"])
    output_path = Path(os.environ["HMDA_EDA_RESULT_PATH"])
    result = run_hmda_eda_memory_workload(
        fixture_directory,
        temp_directory=temp_directory,
        output_path=output_path,
        memory_limit=os.environ["HMDA_EDA_DUCKDB_LIMIT"],
        threads=int(os.environ["HMDA_EDA_DUCKDB_THREADS"]),
    )

    assert result["status"] == "passed"
    assert result["output_validation"] == "passed"
