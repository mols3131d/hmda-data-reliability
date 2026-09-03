"""Airflow data-plane DAG structure tests."""

from typing import Any, cast

import pytest
from airflow.sdk import Asset

from hmda_reliability.orchestration.dags.hmda_data_plane import (
    ANALYTICS_LOAN_ASSET,
    RAW_HMDA_LOANS_ASSET,
    hmda_data_plane,
)

pytestmark = pytest.mark.integration


def test_airflow_dag_owns_the_ordered_data_plane() -> None:
    """The Airflow surface has exactly the raw-to-analytics dependency."""

    assert hmda_data_plane.dag_id == "hmda_data_plane"
    assert hmda_data_plane.schedule is None
    assert hmda_data_plane.catchup is False
    assert hmda_data_plane.max_active_runs == 1
    assert set(hmda_data_plane.task_ids) == {
        "load_raw_hmda_loans",
        "evaluate_quality_gate",
        "build_dbt_loan_analytics",
    }

    raw_task = cast(Any, hmda_data_plane.get_task("load_raw_hmda_loans"))
    gate_task = cast(Any, hmda_data_plane.get_task("evaluate_quality_gate"))
    analytics_task = cast(
        Any,
        hmda_data_plane.get_task("build_dbt_loan_analytics"),
    )

    assert raw_task.upstream_task_ids == set()
    assert raw_task.downstream_task_ids == {"evaluate_quality_gate"}
    assert gate_task.upstream_task_ids == {"load_raw_hmda_loans"}
    assert gate_task.downstream_task_ids == {"build_dbt_loan_analytics"}
    assert analytics_task.upstream_task_ids == {"evaluate_quality_gate"}
    assert analytics_task.downstream_task_ids == set()
    assert raw_task.retries == 0
    assert gate_task.retries == 0
    assert analytics_task.retries == 0


def test_airflow_tasks_expose_stable_assets_without_domain_payloads() -> None:
    """Assets identify updates while domain objects stay out of task transport."""

    raw_task = cast(Any, hmda_data_plane.get_task("load_raw_hmda_loans"))
    analytics_task = cast(
        Any,
        hmda_data_plane.get_task("build_dbt_loan_analytics"),
    )

    assert raw_task.outlets == [RAW_HMDA_LOANS_ASSET]
    assert analytics_task.outlets == [ANALYTICS_LOAN_ASSET]
    assert Asset("hmda/raw/hmda_loans") == RAW_HMDA_LOANS_ASSET
    assert Asset("hmda/analytics/loan_analytics") == ANALYTICS_LOAN_ASSET
    assert raw_task.do_xcom_push is False
    assert analytics_task.do_xcom_push is False
    assert raw_task.multiple_outputs is False
    assert analytics_task.multiple_outputs is False


def test_airflow_dag_exposes_only_supported_runtime_params() -> None:
    """The Airflow trigger surface does not expose the full domain request."""

    assert set(hmda_data_plane.params) == {
        "database_path",
        "source_root",
        "source_year",
        "source_file",
        "run_dbt_build",
    }
