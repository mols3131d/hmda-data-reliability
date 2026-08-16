"""Synthetic case evaluation report."""

from project_pivot.reliability.evaluation.case_result import EvaluationCaseResult
from project_pivot.reliability.evaluation.freshness_delay import (
    FreshnessDelayVerticalSliceResult,
    evaluate_freshness_delay_vertical_slice,
)
from project_pivot.reliability.evaluation.null_spike import (
    NullSpikeVerticalSliceResult,
    evaluate_null_spike_vertical_slice,
)
from project_pivot.reliability.evaluation.recovery_case import (
    build_recovery_evaluation_case,
)
from project_pivot.reliability.evaluation.report import EvaluationReport
from project_pivot.reliability.evaluation.reporter import (
    build_evaluation_report,
    render_evaluation_report_markdown,
    write_evaluation_report,
)
from project_pivot.reliability.evaluation.schema_drift import (
    SchemaDriftVerticalSliceResult,
    evaluate_schema_drift_vertical_slice,
)
from project_pivot.reliability.evaluation.volume_drop import (
    VolumeDropVerticalSliceResult,
    evaluate_volume_drop_vertical_slice,
)

__all__ = [
    "EvaluationCaseResult",
    "EvaluationReport",
    "FreshnessDelayVerticalSliceResult",
    "NullSpikeVerticalSliceResult",
    "SchemaDriftVerticalSliceResult",
    "VolumeDropVerticalSliceResult",
    "build_evaluation_report",
    "build_recovery_evaluation_case",
    "evaluate_freshness_delay_vertical_slice",
    "evaluate_null_spike_vertical_slice",
    "evaluate_schema_drift_vertical_slice",
    "evaluate_volume_drop_vertical_slice",
    "render_evaluation_report_markdown",
    "write_evaluation_report",
]
