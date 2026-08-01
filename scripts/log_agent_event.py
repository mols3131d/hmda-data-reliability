"""Append sanitized agent lifecycle events to the local Dogfooding ledger."""

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

LOGGABLE_TOOL_NAMES = {"runTests", "testFailure", "run_task", "run_in_terminal"}
EVENT_KEYS = ("hookEventName", "toolName", "agentName", "status")


def first_value(payload: dict[str, Any], key: str) -> Any:
    sources = (payload, payload.get("tool_input", {}), payload.get("tool_response", {}))
    for source in sources:
        if isinstance(source, dict) and source.get(key) is not None:
            return source[key]
    return None


def event_from(payload: dict[str, Any]) -> dict[str, str] | None:
    event_name = str(first_value(payload, "hookEventName") or "")
    tool_name = str(first_value(payload, "toolName") or "")

    if event_name == "PostToolUse" and tool_name not in LOGGABLE_TOOL_NAMES:
        return None
    if event_name not in {"SubagentStop", "PostToolUse"}:
        return None

    event = {
        "timestamp": datetime.now(UTC).isoformat(),
        "event": event_name,
    }
    for key in EVENT_KEYS[1:]:
        value = first_value(payload, key)
        if isinstance(value, (str, int, float, bool)):
            event[key] = str(value)
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
