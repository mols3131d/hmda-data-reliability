"""평가 evidence를 집계하고 Markdown 보고서로 렌더링/작성하는 모듈."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from hmda_reliability.reliability.evaluation.case_result import EvaluationCaseResult
from hmda_reliability.reliability.evaluation.report import EvaluationReport


def build_evaluation_report(
    cases: Sequence[EvaluationCaseResult],
    *,
    generated_at: datetime | None = None,
) -> EvaluationReport:
    """평가 케이스 결과를 집계하여 요약 보고서 객체를 생성한다."""

    case_results = list(cases)
    total_cases = len(case_results)
    detection_passed = sum(case.detection_passed for case in case_results)
    action_passed = sum(case.action_passed for case in case_results)
    return EvaluationReport(
        generated_at=generated_at or datetime.now(UTC),
        total_cases=total_cases,
        detection_passed_cases=detection_passed,
        action_passed_cases=action_passed,
        detection_success_rate=_rate(detection_passed, total_cases),
        action_success_rate=_rate(action_passed, total_cases),
        cases=case_results,
    )


def render_evaluation_report_markdown(report: EvaluationReport) -> str:
    """Render an EvaluationReport without writing to the filesystem."""

    lines = [
        "# Pipeline Evaluation Report",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Total cases | {report.total_cases} |",
        f"| Detection passed | {report.detection_passed_cases} |",
        f"| Action passed | {report.action_passed_cases} |",
        f"| Detection success rate | {report.detection_success_rate:.2%} |",
        f"| Action success rate | {report.action_success_rate:.2%} |",
        "",
        "## Case Results",
        "",
        (
            "| Case | Expected incidents | Detected incidents | "
            "Detection | Action | Mutation | Failure stage | Reconciliation | "
            "Evidence refs | Artifact projections |"
        ),
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    lines.extend(_case_line(case) for case in report.cases)
    lines.append("")
    return "\n".join(lines)


def write_evaluation_report(report: EvaluationReport, output_path: str | Path) -> Path:
    """Create parent directories and overwrite output_path with rendered Markdown."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_evaluation_report_markdown(report), encoding="utf-8")
    return path


def _case_line(case: EvaluationCaseResult) -> str:
    return (
        f"| {case.case_name} | "
        f"{_join_values(case.expected_incident_types)} | "
        f"{_join_values(case.detected_incident_types)} | "
        f"{_status(case.detection_passed)} | "
        f"{_status(case.action_passed)} | "
        f"{_optional_bool(case.target_mutated)} | "
        f"{case.failure_stage or '-'} | "
        f"{case.reconciliation_action or '-'} | "
        f"{_join_values(case.evidence_refs)} | "
        f"{_join_values(case.artifact_projection_ids)} |"
    )


def _join_values(values: Sequence[str]) -> str:
    if not values:
        return "-"
    return ", ".join(values)


def _status(value: bool) -> str:
    return "PASS" if value else "FAIL"


def _optional_bool(value: bool | None) -> str:
    if value is None:
        return "-"
    return "YES" if value else "NO"


def _rate(passed: int, total: int) -> float:
    if total == 0:
        return 0.0
    return passed / total
