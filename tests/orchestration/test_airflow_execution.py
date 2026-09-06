"""Airflow task execution and evidence-boundary tests."""

from pathlib import Path

import pytest
from airflow.sdk.exceptions import AirflowException, AirflowSkipException

from hmda_reliability.data_operations import DataOperationError, DataOperationRequest
from hmda_reliability.data_operations.dbt_result import DbtBuildResult
from hmda_reliability.data_operations.raw_result import RawLoadResult
from hmda_reliability.orchestration.dags import hmda_data_plane as airflow_dag
from hmda_reliability.reliability import QualityGateError

pytestmark = pytest.mark.integration


class _OutletEvent:
    def __init__(self) -> None:
        self.extra: dict[str, object] = {}


class _OutletEvents(dict):
    def __init__(self) -> None:
        super().__init__()
        self.events: dict[object, _OutletEvent] = {}

    def __getitem__(self, asset: object) -> _OutletEvent:
        return self.events.setdefault(asset, _OutletEvent())

    def event_for(self, asset: object) -> _OutletEvent:
        return self[asset]


def _runtime_context(
    monkeypatch: pytest.MonkeyPatch,
    overrides: dict[str, object] | None = None,
) -> _OutletEvents:
    outlet_events = _OutletEvents()
    monkeypatch.setattr(
        airflow_dag,
        "get_current_context",
        lambda: {"params": overrides or {}, "outlet_events": outlet_events},
    )
    return outlet_events


def _raw_result(tmp_path: Path) -> RawLoadResult:
    return RawLoadResult(
        database_path=tmp_path / "hmda_reliability.duckdb",
        source_root=tmp_path / "raw",
        source_file_count=2,
        source_year=2025,
        hmda_loans_row_count=4,
    )


def _dbt_result(tmp_path: Path) -> DbtBuildResult:
    return DbtBuildResult(
        command=["dbt", "build"],
        return_code=0,
        manifest_path=tmp_path / "manifest.json",
        run_results_path=tmp_path / "run_results.json",
        projection_id="projection-1",
        succeeded=True,
    )


def test_tasks_delegate_in_order_and_record_separate_update_evidence(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Raw load precedes dbt and promotion, with no domain result transport."""

    outlet_events = _runtime_context(monkeypatch, {"run_dbt_build": True})
    calls: list[str] = []
    raw_result = _raw_result(tmp_path)
    dbt_result = _dbt_result(tmp_path)

    monkeypatch.setattr(
        airflow_dag,
        "load_raw_data",
        lambda _request: calls.append("raw") or raw_result,
    )
    monkeypatch.setattr(
        airflow_dag,
        "evaluate_quality_gate",
        lambda _request: calls.append("gate"),
    )
    monkeypatch.setattr(
        airflow_dag,
        "run_quality_gated_dbt_build",
        lambda _request: calls.append("dbt") or dbt_result,
    )
    monkeypatch.setattr(
        airflow_dag,
        "promote_dbt_artifacts",
        lambda _result, _request: calls.append("promote"),
    )

    airflow_dag.load_raw_hmda_loans.function()
    airflow_dag.evaluate_quality_gate_task.function()
    airflow_dag.build_dbt_loan_analytics.function()

    assert calls == ["raw", "gate", "dbt", "promote"]
    assert outlet_events.event_for(airflow_dag.RAW_HMDA_LOANS_ASSET).extra == {
        "execution_stage": "raw_load",
        "data_update": True,
        "database_path": str(tmp_path / "hmda_reliability.duckdb"),
        "source_root": str(tmp_path / "raw"),
        "source_file_count": 2,
        "source_year": 2025,
        "hmda_loans_row_count": 4,
    }
    assert outlet_events.event_for(airflow_dag.ANALYTICS_LOAN_ASSET).extra == {
        "execution_stage": "analytics_build",
        "data_update": True,
        "return_code": 0,
        "manifest_path": str(tmp_path / "manifest.json"),
        "run_results_path": str(tmp_path / "run_results.json"),
        "projection_id": "projection-1",
    }


def test_raw_failure_prevents_downstream_execution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A raw exception remains a task failure and cannot produce analytics work."""

    _runtime_context(monkeypatch)
    calls: list[str] = []

    def fail_raw(_request: DataOperationRequest) -> RawLoadResult:
        calls.append("raw")
        raise DataOperationError("raw failed")

    monkeypatch.setattr(airflow_dag, "load_raw_data", fail_raw)
    monkeypatch.setattr(
        airflow_dag,
        "run_quality_gated_dbt_build",
        lambda _request: calls.append("dbt"),
    )

    with pytest.raises(DataOperationError, match="raw failed"):
        airflow_dag.load_raw_hmda_loans.function()

    assert calls == ["raw"]
    assert (
        airflow_dag.hmda_data_plane.get_task("build_dbt_loan_analytics").trigger_rule
        == "all_success"
    )


def test_disabled_dbt_is_skipped_without_update_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The disabled analytics stage raises Airflow's explicit skip signal."""

    outlet_events = _runtime_context(monkeypatch, {"run_dbt_build": False})
    calls: list[str] = []
    monkeypatch.setattr(
        airflow_dag,
        "run_quality_gated_dbt_build",
        lambda _request: calls.append("dbt"),
    )
    monkeypatch.setattr(
        airflow_dag,
        "promote_dbt_artifacts",
        lambda _result, _request: calls.append("promote"),
    )

    with pytest.raises(AirflowSkipException, match="run_dbt_build=false"):
        airflow_dag.build_dbt_loan_analytics.function()

    assert calls == []
    assert outlet_events.event_for(airflow_dag.ANALYTICS_LOAN_ASSET).extra == {}


@pytest.mark.parametrize("failure", ["build", "promotion"])
def test_analytics_failure_does_not_record_update_evidence(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    failure: str,
) -> None:
    """A failed candidate or promotion cannot be represented as a successful update."""

    outlet_events = _runtime_context(monkeypatch, {"run_dbt_build": True})
    result = _dbt_result(tmp_path)

    if failure == "build":
        monkeypatch.setattr(
            airflow_dag,
            "run_quality_gated_dbt_build",
            lambda _request: (_ for _ in ()).throw(DataOperationError("dbt failed")),
        )
    else:
        monkeypatch.setattr(
            airflow_dag,
            "run_quality_gated_dbt_build",
            lambda _request: result,
        )
        monkeypatch.setattr(
            airflow_dag,
            "promote_dbt_artifacts",
            lambda _result, _request: (_ for _ in ()).throw(
                DataOperationError("promotion failed")
            ),
        )

    expected_message = "dbt failed" if failure == "build" else "promotion failed"
    with pytest.raises(DataOperationError, match=expected_message):
        airflow_dag.build_dbt_loan_analytics.function()

    assert outlet_events.event_for(airflow_dag.ANALYTICS_LOAN_ASSET).extra == {}


def test_invalid_runtime_request_fails_before_domain_execution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Final DataOperationRequest validation remains before domain calls."""

    _runtime_context(monkeypatch, {"source_year": 1999})
    calls: list[str] = []
    monkeypatch.setattr(
        airflow_dag,
        "data_operation_request_from_runtime",
        lambda _overrides: (_ for _ in ()).throw(ValueError("source_year")),
    )
    monkeypatch.setattr(
        airflow_dag,
        "load_raw_data",
        lambda _request: calls.append("raw"),
    )

    with pytest.raises(ValueError, match="source_year"):
        airflow_dag.load_raw_hmda_loans.function()

    assert calls == []


def test_quality_gate_failure_raises_airflow_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """QualityGateError is converted into AirflowException to fail the task."""

    _runtime_context(monkeypatch)
    gate_error = QualityGateError(
        "품질 게이트 실패: detected=[null_spike(income)]",
        ["null_spike(income)"],
    )

    def fail_gate(_request: DataOperationRequest) -> None:
        raise gate_error

    monkeypatch.setattr(airflow_dag, "evaluate_quality_gate", fail_gate)

    pattern = "품질 게이트 실패.*null_spike"
    with pytest.raises(AirflowException, match=pattern) as exc_info:
        airflow_dag.evaluate_quality_gate_task.function()

    # raise ... from exc 계약으로 __cause__가 원본 에러로 보존되어야 함
    assert exc_info.value.__cause__ is gate_error


def test_quality_gate_unexpected_error_is_not_normalized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unexpected programming/infrastructure errors preserve their original type."""

    _runtime_context(monkeypatch)

    def crash_gate(_request: DataOperationRequest) -> None:
        raise RuntimeError("database connection lost at /secret/path/internal.duckdb")

    monkeypatch.setattr(airflow_dag, "evaluate_quality_gate", crash_gate)

    with pytest.raises(RuntimeError, match="database connection lost"):
        airflow_dag.evaluate_quality_gate_task.function()


def test_analytics_quality_gate_failure_raises_airflow_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Build 직전 재검증 실패도 동일한 Airflow failure contract를 사용한다."""

    _runtime_context(monkeypatch, {"run_dbt_build": True})
    gate_error = QualityGateError(
        "품질 게이트 실패: detected=[null_spike(income)]",
        ["null_spike(income)"],
    )

    def fail_gate(_request: DataOperationRequest) -> None:
        raise gate_error

    monkeypatch.setattr(airflow_dag, "run_quality_gated_dbt_build", fail_gate)

    with pytest.raises(AirflowException, match="null_spike") as exc_info:
        airflow_dag.build_dbt_loan_analytics.function()

    assert exc_info.value.__cause__ is gate_error
