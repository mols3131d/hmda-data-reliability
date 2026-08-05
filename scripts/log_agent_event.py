"""Append sanitized agent lifecycle events to the local Dogfooding ledger."""

import json
import os
import sys
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TypeAlias

from dotenv import load_dotenv

Scalar: TypeAlias = str | int | float | bool

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS_DIR_ENV = "PROJECT_PIVOT_ARTIFACTS_DIR"
DEFAULT_ARTIFACTS_DIR = ".local/artifacts"
EVENT_LOG_NAME = "agent-events.jsonl"

EVENT_STATUS = {
    "PostToolUse": "success",
    "Stop": "stopped",
    "SubagentStart": "started",
    "SubagentStop": "completed",
}
EVENT_FIELDS = (
    "session_id",
    "tool_name",
    "tool_use_id",
    "agent_id",
    "agent_type",
    "agent_name",
    "agent_display_name",
    "stop_reason",
    "stop_hook_active",
)


def load_local_environment() -> None:
    load_dotenv(REPOSITORY_ROOT / ".env", override=False)


def artifact_log_path(environment: Mapping[str, str] | None = None) -> Path:
    source = os.environ if environment is None else environment
    configured = source.get(ARTIFACTS_DIR_ENV, "").strip()
    artifacts_dir = Path(configured or DEFAULT_ARTIFACTS_DIR)
    if not artifacts_dir.is_absolute():
        artifacts_dir = REPOSITORY_ROOT / artifacts_dir
    return artifacts_dir / EVENT_LOG_NAME


def scalar_value(payload: dict[str, Any], key: str) -> Scalar | None:
    value = payload.get(key)
    if isinstance(value, (str, int, float, bool)):
        return value
    return None


def event_from(payload: dict[str, Any]) -> dict[str, Scalar] | None:
    event_name = scalar_value(payload, "hook_event_name")
    if not isinstance(event_name, str) or event_name not in EVENT_STATUS:
        return None

    event: dict[str, Scalar] = {
        "timestamp": scalar_value(payload, "timestamp")
        or datetime.now(UTC).isoformat(),
        "event": event_name,
        "status": EVENT_STATUS[event_name],
    }
    for key in EVENT_FIELDS:
        value = scalar_value(payload, key)
        if value is not None:
            event[key] = value
    return event


def main() -> None:
    try:
        load_local_environment()
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            return
        event = event_from(payload)
        if event is None:
            return
        log_path = artifact_log_path()
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(event, ensure_ascii=True) + "\n")
    except (json.JSONDecodeError, OSError, TypeError):
        return


if __name__ == "__main__":
    main()
