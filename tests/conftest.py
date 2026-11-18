"""Enforce offline execution for the Reliability AI and Runtime AI suites."""

from __future__ import annotations

import socket
import sys
from collections.abc import Generator
from pathlib import Path

import pytest

_TESTS = Path(__file__).parent
_OFFLINE_AI_SUITES = (_TESTS / "reliability_ai", _TESTS / "runtime_ai")
_DNS_EVENTS = frozenset(
    {
        "socket.getaddrinfo",
        "socket.gethostbyaddr",
        "socket.gethostbyname",
        "socket.gethostbyname_ex",
        "socket.getnameinfo",
    }
)
_NETWORK_ATTEMPTED = pytest.StashKey[bool]()
_active_ai_test: pytest.Item | None = None


def _reject_ai_network(event: str, args: tuple[object, ...]) -> None:
    item = _active_ai_test
    if item is None:
        return

    # Both connect() and connect_ex() emit socket.connect before connecting.
    if event in _DNS_EVENTS or (
        event == "socket.connect"
        and getattr(args[0], "family", None) in (socket.AF_INET, socket.AF_INET6)
    ):
        item.stash[_NETWORK_ATTEMPTED] = True
        raise OSError("AI tests must use offline transports")


# Audit hooks are process-wide. The item wrapper limits when this one blocks I/O.
sys.addaudithook(_reject_ai_network)


@pytest.hookimpl(wrapper=True, tryfirst=True)
def pytest_runtest_protocol(item: pytest.Item) -> Generator[None, bool, bool]:
    global _active_ai_test
    previous_item = _active_ai_test
    _active_ai_test = (
        item
        if any(item.path.is_relative_to(suite) for suite in _OFFLINE_AI_SUITES)
        else None
    )
    try:
        return (yield)
    finally:
        _active_ai_test = previous_item


@pytest.hookimpl(wrapper=True, tryfirst=True)
def pytest_runtest_makereport(
    item: pytest.Item,
) -> Generator[None, pytest.TestReport, pytest.TestReport]:
    report = yield
    if item.stash.get(_NETWORK_ATTEMPTED, False):
        item.stash[_NETWORK_ATTEMPTED] = False
        message = "AI test attempted to resolve or connect to a network endpoint"
        if report.failed:
            report.sections.append(("AI test network", message))
        else:
            # A client may swallow the OSError and the test may skip or xfail.
            report.outcome = "failed"
            report.longrepr = message
            report.__dict__.pop("wasxfail", None)
    return report
