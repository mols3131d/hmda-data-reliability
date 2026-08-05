"""Append sanitized agent lifecycle events to the local Dogfooding ledger."""

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

LOGGABLE_EVENTS = {"SubagentStop", "PostToolUse"}
EVENT_FIELDS = (
    "session_id",
    "tool_name",
    "agent_id",
    "agent_type",
    "agent_name",
    "stop_reason",
)


def scalar_value(payload: dict[str, Any], key: str) -> str | None:
    value = payload.get(key)
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    return None


def event_from(payload: dict[str, Any]) -> dict[str, str] | None:
    event_name = scalar_value(payload, "hook_event_name")
    if event_name is None or event_name not in LOGGABLE_EVENTS:
        return None

    event = {
        "timestamp": scalar_value(payload, "timestamp")
        or datetime.now(UTC).isoformat(),
        "event": event_name,
    }
    for key in EVENT_FIELDS:
        value = scalar_value(payload, key)
        if value is not None:
            event[key] = value
    return event


def main() -> None:
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            return
        event = event_from(payload)
        if event is None:
            return
        log_path = Path(".local/artifacts/agent-events.jsonl")
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(event, ensure_ascii=True) + "\n")
    except (json.JSONDecodeError, OSError, TypeError):
        return


if __name__ == "__main__":
    main()
