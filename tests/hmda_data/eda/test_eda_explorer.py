"""HMDA EDA 에이전트 친화적 탐색 API 및 정적 시각화 테스트."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import yaml

from hmda_reliability.hmda_data.eda import (
    analyze_hmda_csv,
    export_eda_evidence_yaml,
    render_eda_static_charts,
)

pytestmark = pytest.mark.component


def test_export_eda_evidence_yaml_returns_valid_yaml(
    hmda_csv_path: Path, tmp_path: Path
) -> None:
    """analyze_hmda_csv 연산 결과가 구조화된 YAML 형태로 직렬화되는지 검증한다."""
    evidence = analyze_hmda_csv(
        hmda_csv_path,
        temp_directory=tmp_path / "duckdb-temp",
    )
    evidence["note"] = "원천 관측값"

    yaml_output = export_eda_evidence_yaml(evidence)
    parsed = yaml.safe_load(yaml_output)

    assert parsed == evidence
    assert list(parsed) == list(evidence)
    assert "원천 관측값" in yaml_output


def test_render_eda_static_charts_generates_files(
    hmda_csv_path: Path, tmp_path: Path
) -> None:
    """EDA 에비던스로부터 정적 HTML 차트 파일이 정상 생성되는지 검증한다."""
    evidence = analyze_hmda_csv(
        hmda_csv_path,
        temp_directory=tmp_path / "duckdb-temp",
    )

    output_dir = tmp_path / "charts"
    generated_files = render_eda_static_charts(evidence, output_directory=output_dir)

    assert {path.name for path in generated_files} == {
        "activity_year_volume.html",
        "null_baseline.html",
    }
    for file_path in generated_files:
        html = file_path.read_text(encoding="utf-8")
        spec, _end = json.JSONDecoder().raw_decode(html.split("var spec = ", 1)[1])
        rows = spec["datasets"][spec["data"]["name"]]
        if file_path.name == "activity_year_volume.html":
            assert rows == [{"activity_year": 2025, "row_count": 2}]
            assert spec["encoding"]["y"]["field"] == "row_count"
        else:
            assert rows == [
                {"column": column, "null_count": 0, "null_rate": 0.0}
                for column in (
                    "activity_year",
                    "state_code",
                    "loan_purpose",
                    "action_taken",
                    "loan_amount",
                    "income",
                )
            ]
            assert spec["encoding"]["x"]["field"] == "null_rate"


@pytest.mark.parametrize(
    ("evidence", "expected_names"),
    [
        ({}, set()),
        (
            {"activity_year_counts": [{"activity_year": 2025, "row_count": 2}]},
            {"activity_year_volume.html"},
        ),
        (
            {"null_counts": {"income": 1}, "null_rates": {"income": 0.5}},
            {"null_baseline.html"},
        ),
    ],
    ids=["empty", "volume-only", "null-only"],
)
def test_render_eda_static_charts_skips_unavailable_slices_and_preserves_other_files(
    tmp_path: Path, evidence: dict[str, Any], expected_names: set[str]
) -> None:
    output_dir = tmp_path / "charts"
    output_dir.mkdir()
    retained = output_dir / "retained.html"
    retained.write_text("previous output", encoding="utf-8")

    generated = render_eda_static_charts(evidence, output_directory=output_dir)

    assert {path.name for path in generated} == expected_names
    assert {path.name for path in output_dir.iterdir()} == expected_names | {
        "retained.html"
    }
    assert retained.read_text(encoding="utf-8") == "previous output"
