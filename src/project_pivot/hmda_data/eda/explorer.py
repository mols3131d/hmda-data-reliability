"""HMDA EDA 에이전트 탐색용 YAML 직렬화 및 정적 시각화 모듈."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import altair as alt
import polars as pl
import yaml


def export_eda_evidence_yaml(evidence: dict[str, Any]) -> str:
    """EDA evidence 결과 dictionary를 구조화된 YAML 문자열로 변환한다."""
    return yaml.dump(evidence, sort_keys=False, allow_unicode=True)


def render_eda_static_charts(
    evidence: dict[str, Any],
    *,
    output_directory: str | Path,
) -> list[Path]:
    """EDA evidence 결과를 정적 시각화 파일(HTML)로 생성하여 저장한다."""
    out_dir = Path(output_directory).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []

    volume_chart_path = _render_activity_year_volume_chart(evidence, out_dir)
    if volume_chart_path:
        generated.append(volume_chart_path)

    null_chart_path = _render_null_baseline_chart(evidence, out_dir)
    if null_chart_path:
        generated.append(null_chart_path)

    return generated


def _render_activity_year_volume_chart(
    evidence: dict[str, Any],
    out_dir: Path,
) -> Path | None:
    activity_year_counts = evidence.get("activity_year_counts", [])
    if not activity_year_counts:
        return None

    year_df = pl.DataFrame(activity_year_counts)
    chart_base: Any = alt.Chart(year_df)
    chart_mark: Any = chart_base.mark_bar(color="#3182bd")
    volume_chart = chart_mark.encode(
        x=alt.X("activity_year:O", title="Activity Year"),
        y=alt.Y("row_count:Q", title="Row Count"),
        tooltip=["activity_year", "row_count"],
    ).properties(
        title="Activity Year별 파티션 행 수 분포",
        width=500,
        height=250,
    )
    volume_html_path = out_dir / "activity_year_volume.html"
    volume_chart.save(str(volume_html_path))
    return volume_html_path


def _render_null_baseline_chart(
    evidence: dict[str, Any],
    out_dir: Path,
) -> Path | None:
    null_counts = evidence.get("null_counts", {})
    null_rates = evidence.get("null_rates", {})
    if not null_counts:
        return None

    null_baseline = [
        {
            "column": column,
            "null_count": null_count,
            "null_rate": null_rates.get(column, 0.0),
        }
        for column, null_count in null_counts.items()
    ]
    null_df = pl.DataFrame(null_baseline)
    null_base: Any = alt.Chart(null_df)
    null_mark: Any = null_base.mark_bar(color="#e6550d")
    null_chart = null_mark.encode(
        x=alt.X("null_rate:Q", title="Null Rate", axis=alt.Axis(format="%")),
        y=alt.Y("column:N", title="Column", sort="-x"),
        tooltip=[
            "column",
            "null_count",
            alt.Tooltip("null_rate:Q", format=".2%"),
        ],
    ).properties(
        title="필수 컬럼별 Null 비율 Baseline",
        width=500,
        height=200,
    )
    null_html_path = out_dir / "null_baseline.html"
    null_chart.save(str(null_html_path))
    return null_html_path
