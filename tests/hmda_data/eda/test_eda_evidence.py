"""HMDA EDA actual-source evidence 수집 및 검증 모듈 테스트."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.run_actual_source import write_evidence

pytestmark = pytest.mark.component


def test_write_evidence_generates_consistent_json_and_markdown(tmp_path: Path) -> None:
    """단일 evidence 객체에서 일치하는 JSON과 Markdown을 생성한다."""
    evidence = {
        "row_count": 1000,
        "duration_seconds": 1.23,
        "null_counts": {"income": 50},
        "grain": {"distinct_group_count": 327},
        "source": {
            "path": "/machine-specific/path/year_2025.csv",
            "duckdb_config": {"temp_directory": "/machine-specific/tmp"},
        },
    }

    json_path = tmp_path / "reference.json"
    markdown_path = tmp_path / "reference.md"

    write_evidence(
        evidence,
        json_path=json_path,
        markdown_path=markdown_path,
        source_id="year_2025.csv",
        source_sha256="4a3226c6a86e61ec1e49509f39dfe9986e969b37808408df5f7eddbde3d7561f",
        repository_revision="abc123",
        observed_at="2026-08-06T00:00:00+00:00",
    )

    assert json_path.exists()
    assert markdown_path.exists()

    json_data = json.loads(json_path.read_text(encoding="utf-8"))
    assert json_data["source_id"] == "year_2025.csv"
    assert json_data["source_sha256"] == (
        "4a3226c6a86e61ec1e49509f39dfe9986e969b37808408df5f7eddbde3d7561f"
    )
    assert json_data["repository_revision"] == "abc123"
    assert json_data["observed_at"] == "2026-08-06T00:00:00+00:00"
    assert json_data["evidence"]["row_count"] == 1000

    md_text = markdown_path.read_text(encoding="utf-8")
    assert "Total Row Count: 1,000" in md_text
    assert "Income Null Count: 50" in md_text
    assert "Mart Grain Distinct Group Count: 327" in md_text
    assert "/machine-specific" not in json_path.read_text(encoding="utf-8")
    assert "/machine-specific" not in md_text
