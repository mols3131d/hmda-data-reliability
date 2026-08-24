"""Dogfooding observability hook payload contract 테스트."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest

pytestmark = pytest.mark.component
REPOSITORY_ROOT = Path(__file__).parents[1]


def load_logger_module() -> ModuleType:
    script_path = REPOSITORY_ROOT / "scripts" / "log_agent_event.py"
    spec = importlib.util.spec_from_file_location("log_agent_event", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_hook_config_uses_supported_vscode_events() -> None:
    config_path = (
        REPOSITORY_ROOT / ".github" / "hooks" / "dogfooding-observability.json"
    )

    config = json.loads(config_path.read_text(encoding="utf-8"))

    assert config["version"] == 1
    assert set(config["hooks"]) == {
        "PostToolUse",
        "Stop",
        "SubagentStart",
        "SubagentStop",
    }
    assert all(
        hook["cwd"] == "." for hooks in config["hooks"].values() for hook in hooks
    )


def test_env_example_defines_common_artifact_root() -> None:
    env_example = (REPOSITORY_ROOT / ".env.example").read_text(encoding="utf-8")

    assert "HMDA_RELIABILITY_ARTIFACTS_DIR=./.local/artifacts" in env_example


def test_artifact_log_path_uses_default_root() -> None:
    module = load_logger_module()

    assert module.artifact_log_path({}) == (
        REPOSITORY_ROOT / ".local" / "artifacts" / "agent-events.jsonl"
    )


def test_artifact_log_path_uses_configured_root(tmp_path: Path) -> None:
    module = load_logger_module()

    relative = module.artifact_log_path(
        {"HMDA_RELIABILITY_ARTIFACTS_DIR": "var/artifacts"}
    )
    absolute = module.artifact_log_path({"HMDA_RELIABILITY_ARTIFACTS_DIR": str(tmp_path)})

    assert relative == REPOSITORY_ROOT / "var" / "artifacts" / "agent-events.jsonl"
    assert absolute == tmp_path / "agent-events.jsonl"


def test_load_local_environment_reads_optional_dotenv(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = load_logger_module()
    monkeypatch.setattr(module, "REPOSITORY_ROOT", tmp_path)
    monkeypatch.delenv("HMDA_RELIABILITY_ARTIFACTS_DIR", raising=False)
    (tmp_path / ".env").write_text(
        "HMDA_RELIABILITY_ARTIFACTS_DIR=.custom/artifacts\n",
        encoding="utf-8",
    )

    module.load_local_environment()

    assert module.artifact_log_path() == (
        tmp_path / ".custom" / "artifacts" / "agent-events.jsonl"
    )


def test_post_tool_use_records_status_and_correlation_id() -> None:
    module = load_logger_module()
    payload = {
        "timestamp": "2026-08-05T10:00:00Z",
        "session_id": "session-1",
        "hook_event_name": "PostToolUse",
        "tool_name": "runTerminalCommand",
        "tool_use_id": "tool-1",
        "tool_input": {"command": "secret"},
        "tool_response": "secret output",
    }

    event = module.event_from(payload)

    assert event == {
        "timestamp": "2026-08-05T10:00:00Z",
        "event": "PostToolUse",
        "status": "success",
        "session_id": "session-1",
        "tool_name": "runTerminalCommand",
        "tool_use_id": "tool-1",
    }


def test_subagent_lifecycle_can_be_correlated_by_agent_id() -> None:
    module = load_logger_module()
    common = {
        "session_id": "session-1",
        "agent_id": "agent-1",
        "agent_type": "review-quality",
    }

    started = module.event_from(
        {
            **common,
            "timestamp": "2026-08-05T10:00:00Z",
            "hook_event_name": "SubagentStart",
        }
    )
    completed = module.event_from(
        {
            **common,
            "timestamp": "2026-08-05T10:00:03Z",
            "hook_event_name": "SubagentStop",
            "stop_hook_active": False,
            "last_assistant_message": "sensitive response",
        }
    )

    assert started == {
        "timestamp": "2026-08-05T10:00:00Z",
        "event": "SubagentStart",
        "status": "started",
        **common,
    }
    assert completed == {
        "timestamp": "2026-08-05T10:00:03Z",
        "event": "SubagentStop",
        "status": "completed",
        **common,
        "stop_hook_active": False,
    }


def test_stop_records_execution_boundary() -> None:
    module = load_logger_module()

    event = module.event_from(
        {
            "timestamp": "2026-08-05T10:00:05Z",
            "session_id": "session-1",
            "hook_event_name": "Stop",
            "stop_hook_active": False,
        }
    )

    assert event == {
        "timestamp": "2026-08-05T10:00:05Z",
        "event": "Stop",
        "status": "stopped",
        "session_id": "session-1",
        "stop_hook_active": False,
    }


def test_unsupported_event_is_ignored() -> None:
    module = load_logger_module()

    assert module.event_from({"hook_event_name": "PreToolUse"}) is None
