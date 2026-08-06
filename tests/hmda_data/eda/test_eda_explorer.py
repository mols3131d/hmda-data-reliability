"""HMDA EDA 에이전트 친화적 탐색 API 및 정적 시각화 테스트."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from project_pivot.hmda_data.eda import (
    analyze_hmda_csv,
    export_eda_evidence_yaml,
    render_eda_static_charts,
)

pytestmark = pytest.mark.component


def test_export_eda_evidence_yaml_returns_valid_yaml(tmp_path: Path) -> None:
    """analyze_hmda_csv 연산 결과가 구조화된 YAML 형태로 직렬화되는지
    검증한다.
    """
    source_path = tmp_path / "hmda.csv"
    source_path.write_text(
        "\n".join(
            [
                "activity_year,state_code,county_code,loan_purpose,action_taken,loan_amount,income",
                "2024,CA,06001,1,1,350000,120",
                "2025,NY,36001,1,3,420000,150",
            ]
        ),
        encoding="utf-8",
    )

    evidence = analyze_hmda_csv(
        source_path,
        temp_directory=tmp_path / "duckdb-temp",
    )

    yaml_output = export_eda_evidence_yaml(evidence)
    parsed = yaml.safe_load(yaml_output)

    assert parsed["row_count"] == 2
    assert "schema" in parsed
    assert "distributions" in parsed
    assert "numeric_summaries" in parsed
    assert "grain" in parsed


def test_render_eda_static_charts_generates_files(tmp_path: Path) -> None:
    """EDA 에비던스로부터 정적 HTML 또는 PNG 차트 파일이 정상 생성되는지 검증한다."""
    source_path = tmp_path / "hmda.csv"
    source_path.write_text(
        "\n".join(
            [
                "activity_year,state_code,county_code,loan_purpose,action_taken,loan_amount,income",
                "2024,CA,06001,1,1,350000,120",
                "2025,NY,36001,1,3,420000,150",
            ]
        ),
        encoding="utf-8",
    )

    evidence = analyze_hmda_csv(
        source_path,
        temp_directory=tmp_path / "duckdb-temp",
    )

    output_dir = tmp_path / "charts"
    generated_files = render_eda_static_charts(evidence, output_directory=output_dir)

    assert len(generated_files) > 0
    for file_path in generated_files:
        assert file_path.exists()
        assert file_path.stat().st_size > 0
