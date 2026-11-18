"""Check that direct AI test runs fail even when a client handles a socket error."""

from pathlib import Path

import pytest

pytest_plugins = ("pytester",)


@pytest.mark.component
@pytest.mark.parametrize(
    ("domain", "phase", "operation", "outcomes"),
    [
        ("reliability_ai", "setup", "getaddrinfo", {"errors": 1}),
        ("reliability_ai", "call", "connect", {"failed": 1}),
        ("runtime_ai", "call_skip", "gethostbyname", {"failed": 1}),
        ("runtime_ai", "call_xfail", "getaddrinfo", {"failed": 1}),
        ("runtime_ai", "teardown", "getaddrinfo", {"passed": 1, "errors": 1}),
        ("other", "call", "getaddrinfo", {"passed": 1}),
        ("runtime_ai", "call", "unix_connect", {"passed": 1}),
    ],
)
def test_network_policy_applies_to_ai_test_phases(
    pytester: pytest.Pytester,
    domain: str,
    phase: str,
    operation: str,
    outcomes: dict[str, int],
) -> None:
    pytester.makeconftest(
        Path(__file__).with_name("conftest.py").read_text(encoding="utf-8")
    )
    pytester.makeini("[pytest]\nmarkers = unit: isolated test")
    test_dir = pytester.path / domain
    test_dir.mkdir()
    test_file = test_dir / "test_client.py"
    test_file.write_text(
        f"""
import socket
import sys
from socket import getaddrinfo, gethostbyname
from types import SimpleNamespace

import pytest


def try_network():
    try:
        if {operation!r} == 'getaddrinfo':
            getaddrinfo('127.0.0.1', 9, flags=socket.AI_NUMERICHOST)
        elif {operation!r} == 'gethostbyname':
            gethostbyname('127.0.0.1')
        elif {operation!r} == 'unix_connect':
            sys.audit('socket.connect', SimpleNamespace(family=socket.AF_UNIX), 'local')
        else:
            sys.audit(
                'socket.connect',
                SimpleNamespace(family=socket.AF_INET),
                ('127.0.0.1', 9),
            )
    except OSError:
        pass


@pytest.fixture(scope='module')
def client():
    if {phase!r} == 'setup':
        try_network()
    yield
    if {phase!r} == 'teardown':
        try_network()


@pytest.mark.unit
@pytest.mark.xfail({phase!r} == 'call_xfail', reason='unrelated expected failure')
def test_client(client):
    if {phase!r}.startswith('call'):
        try_network()
    if {phase!r} == 'call_skip':
        pytest.skip('client unavailable')
""",
        encoding="utf-8",
    )

    result = pytester.runpytest_subprocess(
        f"{test_file}::test_client", "-m", "unit", "-q"
    )

    result.assert_outcomes(**outcomes)
    if outcomes == {"passed": 1}:
        assert result.ret == pytest.ExitCode.OK
    else:
        assert result.ret == pytest.ExitCode.TESTS_FAILED
        result.stdout.fnmatch_lines(["*AI test attempted to resolve or connect*"])
