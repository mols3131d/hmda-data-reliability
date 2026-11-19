import httpx
import pytest

from hmda_reliability.reliability_ai.ingestion.airflow import AirflowRunReader, RunRef

pytestmark = pytest.mark.component


@pytest.mark.parametrize(
    ("attempt", "version", "expected", "rows"),
    [
        (2, "abc", "matched", 9),
        (2, "def", "mismatched", 9),
        (1, "abc", "unknown", None),
        (None, "abc", "unknown", None),
    ],
)
def test_airflow_correlates_update_by_run_task_and_attempt(
    attempt: int | None, version: str, expected: str, rows: int | None
) -> None:
    ref = RunRef(run_id="manual__run")
    scope = {
        "source_root": "/raw",
        "source_year": 2025,
        "source_file": None,
        "raw_table_name": "raw.hmda_loans",
    }

    def get(req: httpx.Request) -> httpx.Response:
        assert req.method == "GET"
        if req.url.path.endswith("/assets/events"):
            return httpx.Response(
                200,
                json={
                    "asset_events": [
                        {
                            "source_dag_id": "hmda_data_plane",
                            "source_run_id": "manual__run",
                            "source_task_id": "load_raw_hmda_loans",
                            "source_map_index": -1,
                            "extra": {
                                "try_number": attempt,
                                "execution_stage": "raw_load",
                                "data_update": True,
                                "hmda_loans_row_count": 9,
                                "input_version": version,
                                "scope": scope,
                            },
                        }
                    ],
                    "total_entries": 1,
                },
            )
        assert req.url.path.endswith(
            "/dags/hmda_data_plane/dagRuns/manual__run/taskInstances/load_raw_hmda_loans"
        )
        return httpx.Response(
            200,
            json={
                "dag_id": "hmda_data_plane",
                "dag_run_id": "manual__run",
                "task_id": "load_raw_hmda_loans",
                "map_index": -1,
                "try_number": 2,
                "state": "success",
            },
        )

    with httpx.Client(
        base_url="http://test/api/v2/", transport=httpx.MockTransport(get)
    ) as client:
        stage = AirflowRunReader(client).read(
            ref, "raw_load", {"version": "abc", "scope": scope}, timeout=2
        )
    assert stage["state"] == "success"
    assert stage["row_count"] == rows
    assert stage["input_match"] == expected


def test_other_run_does_not_supply_stage_evidence() -> None:
    with httpx.Client(
        base_url="http://test/api/v2/",
        transport=httpx.MockTransport(
            lambda _: httpx.Response(
                200,
                json={
                    "dag_id": "hmda_data_plane",
                    "dag_run_id": "foreign",
                    "task_id": "load_raw_hmda_loans",
                    "map_index": -1,
                    "try_number": 1,
                    "state": "success",
                },
            )
        ),
    ) as client:
        stage = AirflowRunReader(client).read(
            RunRef(run_id="requested"), "raw_load", None, timeout=1
        )
    assert stage["state"] == "unknown"


@pytest.mark.parametrize(
    ("late_at", "expected_state", "expected_requests"),
    [("task", "unknown", 1), ("assets", "success", 2)],
)
def test_slow_response_preserves_only_timely_stage_evidence(
    late_at: str, expected_state: str, expected_requests: int
) -> None:
    now = 0.0
    requests: list[float] = []

    def get(req: httpx.Request) -> httpx.Response:
        nonlocal now
        requests.append(req.extensions["timeout"]["read"])
        if req.url.path.endswith("/assets/events"):
            now = 10.0
            return httpx.Response(
                200,
                json={
                    "asset_events": [
                        {
                            "source_dag_id": "hmda_data_plane",
                            "source_run_id": "run",
                            "source_task_id": "load_raw_hmda_loans",
                            "source_map_index": -1,
                            "extra": {
                                "execution_stage": "raw_load",
                                "try_number": 2,
                                "data_update": True,
                                "hmda_loans_row_count": 9,
                            },
                        }
                    ],
                    "total_entries": 1,
                },
            )
        now = 10.0 if late_at == "task" else 6.0
        return httpx.Response(
            200,
            json={
                "dag_id": "hmda_data_plane",
                "dag_run_id": "run",
                "task_id": "load_raw_hmda_loans",
                "map_index": -1,
                "try_number": 2,
                "state": "success",
            },
        )

    with httpx.Client(
        base_url="http://test/api/v2/", transport=httpx.MockTransport(get)
    ) as client:
        result = AirflowRunReader(client).read(
            RunRef(run_id="run"), "raw_load", None, deadline=10.0, clock=lambda: now
        )
    assert (result["state"], result["data_update"], result["row_count"]) == (
        expected_state,
        "unknown",
        None,
    )
    assert requests == [10.0, 4.0][:expected_requests]
