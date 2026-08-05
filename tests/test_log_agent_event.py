"""Dogfooding observability hook payload contract 테스트."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest

pytestmark = pytest.mark.unit
REPOSITORY_ROOT = Path(__file__).parents[1]


def load_logger_module() -> ModuleType:
    script_path = REPOSITORY_ROOT / "scripts" / "log_agent_event.py"
    spec = importlib.util.spec_from_file_location("log_agent_event", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_hook_config_uses_versioned_vscode_compatible_events() -> None:
    config_path = (
        REPOSITORY_ROOT / ".github" / "hooks" / "dogfooding-observability.json"
    )

    config = json.loads(config_path.read_text(encoding="utf-8"))

    assert config["version"] == 1
    assert set(config["hooks"]) == {"PostToolUse", "SubagentStop"}


def test_post_tool_use_records_only_sanitized_metadata() -> None:
    module = load_logger_module()
    payload = {
        "timestamp": "2026-08-05T10:00:00Z",
        "session_id": "session-1",
        "hook_event_name": "PostToolUse",
        "tool_name": "runTerminalCommand",
        "tool_input": {"command": "secret"},
        "tool_response": "secret output",
    }

    event = module.event_from(payload)

    assert event == {
        "timestamp": "2026-08-05T10:00:00Z",
        "event": "PostToolUse",
        "session_id": "session-1",
        "tool_name": "runTerminalCommand",
    }


def test_subagent_stop_records_agent_identity_without_response() -> None:
    module = load_logger_module()
    payload = {
        "timestamp": "2026-08-05T10:00:00Z",
        "session_id": "session-1",
        "hook_event_name": "SubagentStop",
        "agent_id": "agent-1",
        "agent_type": "review-quality",
        "agent_name": "Review Quality",
        "stop_reason": "end_turn",
        "last_assistant_message": "sensitive response",
    }

    event = module.event_from(payload)

    assert event == {
        "timestamp": "2026-08-05T10:00:00Z",
        "event": "SubagentStop",
        "session_id": "session-1",
        "agent_id": "agent-1",
        "agent_type": "review-quality",
        "agent_name": "Review Quality",
        "stop_reason": "end_turn",
    }


def test_unsupported_event_is_ignored() -> None:
    module = load_logger_module()

    assert module.event_from({"hook_event_name": "PreToolUse"}) is None
