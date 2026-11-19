"""Airflow 공개 API에서 지정한 DAG 실행의 단계별 관찰만 읽는다."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any, Literal
from urllib.parse import quote

import httpx
from pydantic import BaseModel, ConfigDict, Field

STAGES = {
    "raw_load": "load_raw_hmda_loans",
    "quality_gate": "evaluate_quality_gate",
    "dbt_build": "build_dbt_loan_analytics",
}


class RunRef(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    dag_id: Literal["hmda_data_plane"] = "hmda_data_plane"
    run_id: str = Field(pattern=r"^[A-Za-z0-9_][A-Za-z0-9_.:+~=-]{0,249}$")
    try_number: int | None = Field(default=None, ge=1, strict=True)
    map_index: Literal[-1] = -1


class AirflowRunReader:
    """호출자가 설정한 /api/v2/ 클라이언트로 인증·연결 경계를 유지한다."""

    def __init__(self, client: httpx.Client) -> None:
        self.client = client

    def read(
        self,
        run: RunRef,
        stage: str,
        prepared: dict[str, Any] | None,
        *,
        timeout: float | None = None,
        deadline: float | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> dict[str, Any]:
        if timeout is not None:
            request_deadline = clock() + timeout
            deadline = (
                request_deadline
                if deadline is None
                else min(deadline, request_deadline)
            )
        if deadline is None:
            raise ValueError("Airflow read requires a deadline or timeout")
        task = STAGES[stage]
        result: dict[str, Any] = {
            **run.model_dump(),
            "stage": stage,
            "task_id": task,
            "state": "unknown",
            "data_update": "unknown",
            "row_count": None,
            "input_match": "unknown",
        }
        run_path = f"dags/{run.dag_id}/dagRuns/{quote(run.run_id, safe='')}"
        path = f"{run_path}/taskInstances/{task}"
        if run.try_number is not None:
            path += f"/tries/{run.try_number}"
        try:
            remaining = deadline - clock()
            if remaining <= 0:
                return result
            response = self.client.get(path, timeout=remaining, follow_redirects=False)
            response.raise_for_status()
            item = response.json()
            if not isinstance(item, dict) or clock() >= deadline:
                return result
            attempt = item.get("try_number")
            if (
                (
                    item.get("dag_id"),
                    item.get("dag_run_id", item.get("run_id")),
                    item.get("task_id"),
                    item.get("map_index"),
                )
                != (run.dag_id, run.run_id, task, run.map_index)
                or type(attempt) is not int
                or (run.try_number is not None and attempt != run.try_number)
            ):
                return result
            state = item.get("state")
            result.update(
                try_number=attempt, state=state if isinstance(state, str) else "unknown"
            )
            if stage == "quality_gate":
                return result
            filters: dict[str, str | int] = {
                "source_dag_id": run.dag_id,
                "source_run_id": run.run_id,
                "source_task_id": task,
                "source_map_index": run.map_index,
            }
            remaining = deadline - clock()
            if remaining <= 0:
                return result
            response = self.client.get(
                "assets/events",
                params={**filters, "limit": 100},
                timeout=remaining,
                follow_redirects=False,
            )
            response.raise_for_status()
            page = response.json()
            if (
                not isinstance(page, dict)
                or not isinstance(page.get("asset_events"), list)
                or page.get("total_entries") != len(page["asset_events"])
            ):
                return result
            observations = []
            for event in page["asset_events"]:
                if not isinstance(event, dict) or any(
                    event.get(k) != v for k, v in filters.items()
                ):
                    continue
                extra = event.get("extra")
                if (
                    isinstance(extra, dict)
                    and extra.get("execution_stage")
                    == ("analytics_build" if stage == "dbt_build" else stage)
                    and type(extra.get("try_number")) is int
                    and extra["try_number"] == attempt
                    and extra.get("data_update") is True
                ):
                    observations.append(extra)
            if len(observations) == 1 and clock() < deadline:
                extra = observations[0]
                result["data_update"] = "confirmed"
                rows = extra.get("hmda_loans_row_count")
                if stage == "raw_load" and type(rows) is int and rows >= 0:
                    result["row_count"] = rows
                if (
                    stage == "raw_load"
                    and prepared
                    and prepared.get("version")
                    and isinstance(extra.get("input_version"), str)
                    and extra["input_version"]
                    and isinstance(extra.get("scope"), dict)
                ):
                    keys = (
                        "source_root",
                        "source_year",
                        "source_file",
                        "raw_table_name",
                    )
                    if all(
                        k in extra["scope"] and k in prepared["scope"] for k in keys
                    ):
                        match = (
                            all(extra["scope"][k] == prepared["scope"][k] for k in keys)
                            and extra["input_version"] == prepared["version"]
                        )
                        result["input_match"] = "matched" if match else "mismatched"
        except (httpx.HTTPError, ValueError):
            pass
        return result
