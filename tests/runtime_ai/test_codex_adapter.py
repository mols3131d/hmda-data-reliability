import json
from collections import deque
from pathlib import Path
from typing import Any

import pytest

from hmda_reliability.runtime_ai import codex
from hmda_reliability.runtime_ai.codex import (
    CodexAdapter,
    CodexSettings,
    decode_codex_response,
)
from hmda_reliability.runtime_ai.codex_isolation import PreflightError
from hmda_reliability.runtime_ai.codex_rpc import RpcRejected
from hmda_reliability.runtime_ai.contracts import ChatMessage
from hmda_reliability.runtime_ai.provider import ProviderUnavailableError

pytestmark = pytest.mark.unit
_MESSAGES = (ChatMessage(role="user", content="synthetic context"),)
_VALID = '{"content":"done","tool_calls":[]}'


def final(thread: str, turn: str, content: str = _VALID) -> dict[str, Any]:
    return {
        "method": "turn/completed",
        "params": {
            "threadId": thread,
            "turn": {
                "id": turn,
                "status": "completed",
                "items": [
                    {
                        "id": "i",
                        "type": "agentMessage",
                        "phase": "final_answer",
                        "text": content,
                    }
                ],
            },
        },
    }


class Server:
    def __init__(self, replies: list[Any], events: list[Any]):
        self.replies = deque(replies)
        self.events = deque(events)
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.next_id = 1

    def rpc(
        self, method: str, params: dict[str, Any], deadline: float, **kwargs: Any
    ) -> Any:
        self.calls.append((method, params))
        self.next_id += 1
        value = self.replies.popleft()
        if isinstance(value, Exception):
            raise value
        return value

    def read(self, deadline: float) -> Any:
        value = self.events.popleft()
        if isinstance(value, Exception):
            raise value
        return value


def adapter(monkeypatch: pytest.MonkeyPatch, server: Server) -> CodexAdapter:
    threads = iter(("thread-1", "thread-2"))
    active = CodexAdapter(CodexSettings())
    monkeypatch.setattr(active, "_session", lambda _: (server, Path("/tmp")))
    monkeypatch.setattr(codex, "start_thread", lambda *args: (next(threads), "model-a"))
    return active


def test_retries_only_the_explicit_overload_with_a_fresh_thread(
    monkeypatch: pytest.MonkeyPatch,
):
    server = Server(
        [RpcRejected(-32001), {"turn": {"id": "t2"}}],
        [
            final("thread-1", "t1", "wrong"),
            final("thread-2", "wrong", "wrong"),
            final("thread-2", "t2"),
            final("thread-2", "t2", "duplicate"),
        ],
    )
    raw = adapter(monkeypatch, server).invoke_for_turn("inv-test", 4, _MESSAGES)
    assert raw.content == _VALID and raw.attempt_count == 2
    attempt = raw.response_metadata.codex_attempt
    assert (
        attempt.logical_turn,
        attempt.thread_id,
        attempt.turn_id,
        attempt.rejected_requests,
    ) == (4, "thread-2", "t2", (1,))
    assert [params["threadId"] for _, params in server.calls] == [
        "thread-1",
        "thread-2",
    ]
    assert decode_codex_response(raw).content == "done"
    assert len(server.events) == 1


def test_disconnect_during_start_is_ambiguous_and_never_retried(
    monkeypatch: pytest.MonkeyPatch,
):
    server = Server([EOFError()], [])
    with pytest.raises(ProviderUnavailableError) as error:
        adapter(monkeypatch, server).invoke_for_turn("inv-test", 0, _MESSAGES)
    assert error.value.failure_code == "codex_acceptance_unknown"
    assert error.value.attempt_count == 1 and len(server.calls) == 1
    assert not error.value.response_metadata.codex_attempt.terminated


@pytest.mark.parametrize("terminal", [True, False])
def test_interrupt_and_actual_termination_are_separate(
    monkeypatch: pytest.MonkeyPatch, terminal: bool
):
    server = Server(
        [{"turn": {"id": "t1"}}, {}],
        [TimeoutError(), final("thread-1", "t1") if terminal else TimeoutError()],
    )
    active = adapter(monkeypatch, server)
    if terminal:
        response = active.invoke_for_turn("inv-test", 0, _MESSAGES)
        assert response.content == _VALID
        meta = response.response_metadata
    else:
        with pytest.raises(ProviderUnavailableError) as failure:
            active.invoke_for_turn("inv-test", 0, _MESSAGES)
        meta = failure.value.response_metadata
    attempt = meta.codex_attempt
    assert attempt.interrupt_requested and attempt.interrupt_acknowledged
    assert attempt.terminated == terminal
    assert server.calls[-1] == (
        "turn/interrupt",
        {"threadId": "thread-1", "turnId": "t1"},
    )


@pytest.mark.parametrize(
    "code", ["codex_isolation_unverified", "codex_subscription_required"]
)
def test_preflight_failure_sends_no_model_input(
    monkeypatch: pytest.MonkeyPatch, code: str
):
    active = CodexAdapter(CodexSettings())

    def fail(_deadline: float):
        raise PreflightError(code)

    monkeypatch.setattr(active, "_session", fail)
    with pytest.raises(ProviderUnavailableError) as failure:
        active.invoke_for_turn("inv-test", 0, _MESSAGES)
    assert failure.value.attempt_count == 0 and failure.value.failure_code == code


def test_input_budget_includes_the_envelope_schema_and_actual_conversation():
    supplied = json.loads(CodexAdapter.input_bytes(_MESSAGES, None))
    assert "tool_calls" in supplied["outputSchema"]["required"]
    assert json.loads(supplied["input"][0]["text"]) == {
        "messages": [{"role": "user", "content": "synthetic context"}],
        "tools": [],
    }


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        ("free", "codex_subscription_required"),
        ("api_key", "codex_subscription_required"),
        ("unknown_plan", "codex_subscription_required"),
        ("new_plan", "codex_subscription_required"),
        ("metered", "codex_subscription_required"),
        ("hybrid", "codex_subscription_required"),
        ("extra_files", "codex_isolation_unverified"),
        ("command_worked", "codex_isolation_unverified"),
        ("control_failed", "codex_isolation_unverified"),
        ("unknown_failure", "codex_isolation_unverified"),
        ("mcp", "codex_isolation_unverified"),
        ("hook", "codex_isolation_unverified"),
        ("plugin", "codex_isolation_unverified"),
    ],
)
def test_effective_account_and_execution_controls_are_verified_before_the_turn(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, mutation: str, expected: str
):
    from hmda_reliability.runtime_ai import codex_isolation as isolation

    class FakeServer:
        def __init__(self, *args):
            self.calls: list[str] = []

        def rpc(self, method, params, deadline):
            self.calls.append(method)
            if method == "initialize":
                return {}
            if method == "config/read":
                filesystem = {":root": "deny"}
                if mutation == "extra_files":
                    filesystem["/extra"] = "read"
                return {
                    "config": {
                        "permissions": {
                            isolation.PROFILE: {
                                "filesystem": filesystem,
                                "network": {"enabled": False},
                            }
                        },
                        "default_permissions": isolation.PROFILE,
                        "approval_policy": "never",
                        "web_search": "disabled",
                        "forced_login_method": "chatgpt",
                        "chatgpt_base_url": "https://chatgpt.com/backend-api",
                        "model_provider": "openai",
                        "features": {
                            **dict.fromkeys(isolation._DISABLED, False),
                            "skip_host_skill_discovery": True,
                        },
                    }
                }
            if method == "mcpServerStatus/list":
                return {"data": [1] if mutation == "mcp" else []}
            if method == "hooks/list":
                return {
                    "data": [
                        {
                            "cwd": params["cwds"][0],
                            "hooks": [1] if mutation == "hook" else [],
                            "errors": [],
                        }
                    ]
                }
            if method == "plugin/installed":
                return {
                    "marketplaces": [{"plugins": [{"enabled": mutation == "plugin"}]}],
                    "marketplaceLoadErrors": [],
                }
            if method == "command/exec":
                if "sandboxPolicy" in params:
                    return {"exitCode": int(mutation == "control_failed"), "stderr": ""}
                return {
                    "exitCode": int(mutation != "command_worked"),
                    "stderr": "bus error"
                    if mutation == "unknown_failure"
                    else "Permission denied",
                }
            if method == "account/read":
                return {
                    "account": {
                        "type": "apiKey" if mutation == "api_key" else "chatgpt",
                        "planType": {
                            "free": "free",
                            "unknown_plan": "unknown",
                            "new_plan": "new_future_tier",
                            "metered": "enterprise_cbp_usage_based",
                            "hybrid": "enterprise_cbp_automation",
                        }.get(mutation, "pro"),
                    }
                }
            raise AssertionError(method)

        def send(self, *args):
            pass

        def close(self):
            pass

    fake = FakeServer()
    monkeypatch.setattr(codex, "AppServer", lambda *args: fake)
    with pytest.raises(ProviderUnavailableError) as failure:
        CodexAdapter(CodexSettings()).invoke(_MESSAGES)
    assert failure.value.failure_code == expected
    assert failure.value.attempt_count == 0 and "turn/start" not in fake.calls


def test_disconnect_after_confirmed_rejection_has_no_new_ambiguous_turn(monkeypatch):
    server = Server([RpcRejected(-32001)], [])
    active = adapter(monkeypatch, server)
    starts = iter((("thread-1", "model-a"), EOFError()))

    def start(*args):
        outcome = next(starts)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    monkeypatch.setattr(codex, "start_thread", start)
    with pytest.raises(ProviderUnavailableError) as failure:
        active.invoke_for_turn("inv-test", 0, _MESSAGES)
    assert failure.value.failure_code == "codex_thread_unavailable"
    assert failure.value.attempt_count == 1
    assert failure.value.response_metadata.codex_attempt.rejected_requests == (1,)
    assert [method for method, _ in server.calls] == ["turn/start"]


@pytest.mark.parametrize(
    "data",
    [
        b'{"text":"' + b"x" * (2 * 1024 * 1024) + b'"}\n',
        b'{"a":' + b"[" * 4000 + b"0" + b"]" * 4000 + b"}\n",
    ],
    ids=["oversize-complete-frame", "overdeep-json"],
)
def test_transport_rejects_invalid_complete_frames_without_parsing_unbounded_data(
    tmp_path, data
):
    import sys
    import time

    from hmda_reliability.runtime_ai.codex_rpc import AppServer

    server = AppServer([sys.executable, "-c", "pass"], tmp_path)
    try:
        server.buffer.extend(data)
        with pytest.raises(ValueError):
            server.read(time.monotonic() + 1)
    finally:
        server.close()
