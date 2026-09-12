"""Append sanitized agent lifecycle events to the local Dogfooding ledger.

Reads JSON event payloads from stdin, sanitizes sensitive fields
(stripping raw prompts, messages, tool inputs, and outputs),
extracts permitted scalar tracking metadata, and appends the structured
record to `agent-events.jsonl` under the configured artifacts directory.

Failure Semantics:
- Fails closed and silently on any JSON decoding errors, missing fields,
  or OS/IO issues to ensure telemetry never breaks the primary agent loop.
"""

import json
import os
import sys
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

type Scalar = str | int | float | bool

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS_DIR_ENV = "HMDA_RELIABILITY_ARTIFACTS_DIR"
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
    """Load local .env settings without overriding existing environment variables."""
    load_dotenv(REPOSITORY_ROOT / ".env", override=False)


def artifact_log_path(environment: Mapping[str, str] | None = None) -> Path:
    """Determine the destination path for the agent event ledger.

    Resolves `HMDA_RELIABILITY_ARTIFACTS_DIR` if set, otherwise falls back to
    `.local/artifacts/agent-events.jsonl` relative to the repository root.

    Args:
        environment: Optional environment mapping (defaults to `os.environ`).

    Returns:
        The resolved Path to the target `agent-events.jsonl` file.
    """
    source = os.environ if environment is None else environment
    configured = source.get(ARTIFACTS_DIR_ENV, "").strip()
    artifacts_dir = Path(configured or DEFAULT_ARTIFACTS_DIR)
    if not artifacts_dir.is_absolute():
        artifacts_dir = REPOSITORY_ROOT / artifacts_dir
    return artifacts_dir / EVENT_LOG_NAME


def scalar_value(payload: dict[str, Any], key: str) -> Scalar | None:
    """Extract value from payload only if it is a primitive scalar.

    Ensures compound objects (dicts, lists) containing raw prompts or responses
    are filtered out at the boundary.
    """
    value = payload.get(key)
    if isinstance(value, (str, int, float, bool)):
        return value
    return None


def event_from(payload: dict[str, Any]) -> dict[str, Scalar] | None:
    """Transform and sanitize a raw hook payload into a ledger event.

    Validates that `hook_event_name` is one of the recognized lifecycle events.
    Applies current UTC timestamp if omitted, maps status, and retains only
    allow-listed scalar fields.

    Args:
        payload: Decoded JSON dictionary received from the hook invocation.

    Returns:
        A sanitized dictionary mapping field names to scalar values, or None
        if the event name is missing or unsupported.
    """
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
    """Read hook payload from stdin, format event, and append to JSONL ledger."""
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
