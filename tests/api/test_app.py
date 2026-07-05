"""FastAPI app 테스트."""

from __future__ import annotations

import importlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import anyio
import pytest
from starlette.types import ASGIApp, Message, Scope

from project_pivot.pipeline import (
    MvpLifecycleResult,
    MvpPipelineRunRequest,
    MvpPipelineRunResult,
    RawLoadResult,
)

pytestmark = pytest.mark.component

api_app = importlib.import_module("project_pivot.api.app")


@dataclass(frozen=True)
class AsgiResponse:
    status_code: int
    body: bytes

    def json(self) -> Any:
        return json.loads(self.body)


def call_asgi_app(
    application: ASGIApp,
    method: str,
    path: str,
    json_payload: dict[str, object] | None = None,
) -> AsgiResponse:
    body = json.dumps(json_payload).encode() if json_payload is not None else b""
    headers = [(b"host", b"testserver")]
    if json_payload is not None:
        headers.append((b"content-type", b"application/json"))

    scope: Scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.4"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "root_path": "",
        "headers": headers,
        "client": ("testclient", 50000),
        "server": ("testserver", 80),
    }
    sent_messages: list[Message] = []
    request_sent = False

    async def receive() -> Message:
        nonlocal request_sent
        if request_sent:
            return {"type": "http.disconnect"}
        request_sent = True
        return {"type": "http.request", "body": body, "more_body": False}

    async def send(message: Message) -> None:
        sent_messages.append(message)

    async def run_app() -> None:
        await application(scope, receive, send)

    anyio.run(run_app)

    status_code = next(
        cast(int, message["status"])
        for message in sent_messages
        if message["type"] == "http.response.start"
    )
    response_body = b"".join(
        cast(bytes, message.get("body", b""))
        for message in sent_messages
        if message["type"] == "http.response.body"
    )
    return AsgiResponse(status_code=status_code, body=response_body)


def test_health_endpoint_returns_ok() -> None:
    """health endpoint 계약을 검증한다."""

    response = call_asgi_app(api_app.app, "GET", "/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_pipeline_run_endpoint_returns_pipeline_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """pipeline endpoint가 runner 결과를 JSON으로 반환하는지 검증한다."""

    def fake_run_pipeline(_request: MvpPipelineRunRequest) -> MvpPipelineRunResult:
        return MvpPipelineRunResult(
            status="completed",
            raw_load=RawLoadResult(
                database_path=Path("data/project_pivot.duckdb"),
                source_root=Path("data/raw/hmda"),
                source_file_count=1,
                source_year=2025,
                hmda_loans_row_count=4,
            ),
            dbt_build=None,
            lifecycle=MvpLifecycleResult(
                metadata_row_count=4,
                baseline_row_count=4,
                current_row_count=1,
                detected_incident_types=["volume_drop"],
                evidence_refs=["ev_1"],
                affected_assets=["mart_hmda_loan_outcomes"],
                recommended_actions=["prepare_partition_backfill"],
                backfill_actions=["prepare_partition_backfill"],
                validation_actions=["rerun_profile_snapshot"],
                evaluation_report_path=Path("scratch/evaluation/api_report.md"),
                detection_success_rate=1.0,
                action_success_rate=1.0,
            ),
        )

    monkeypatch.setattr(api_app, "run_mvp_pipeline", fake_run_pipeline)

    response = call_asgi_app(
        api_app.app,
        "POST",
        "/pipeline/run",
        json_payload={
            "database_path": "data/project_pivot.duckdb",
            "source_root": "data/raw/hmda",
            "run_dbt_build": False,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "completed"
    assert payload["lifecycle"]["detected_incident_types"] == ["volume_drop"]
