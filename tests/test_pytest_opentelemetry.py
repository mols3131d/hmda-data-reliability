"""pytest-opentelemetry plugin boundary 테스트."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.component
pytest_plugins = ("pytester",)


def test_pytest_opentelemetry_registers_public_options(
    pytester: pytest.Pytester,
) -> None:
    """plugin이 trace export와 parent option을 등록한다."""

    result = pytester.runpytest_subprocess("--help")

    result.stdout.fnmatch_lines(
        [
            "*--export-traces*",
            "*--trace-parent=TRACE_PARENT*",
            "*--trace-per-test*",
        ]
    )


def test_pytest_opentelemetry_exports_span_contract(
    pytester: pytest.Pytester,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """console exporter에서 fixture, test, run span contract를 확인한다."""

    monkeypatch.setenv("OTEL_TRACES_EXPORTER", "console")
    pytester.makepyfile(
        """
        import pytest

        @pytest.fixture
        def resource():
            return "ready"

        def test_traced(resource):
            assert resource == "ready"
        """
    )

    result = pytester.runpytest_subprocess(
        "-n",
        "0",
        "--export-traces",
        "-p",
        "no:sugar",
        "-q",
    )

    result.assert_outcomes(passed=1)
    result.stdout.fnmatch_lines(
        [
            '*"pytest.fixture_scope": "function"*',
            '*"pytest.nodeid": *::test_traced*',
            '*"pytest.span_type": "test"*',
            '*"pytest.span_type": "run"*',
        ]
    )


def test_pytest_opentelemetry_runs_with_xdist(
    pytester: pytest.Pytester,
) -> None:
    """plugin을 로드한 채 xdist worker에서 테스트를 실행할 수 있다."""

    pytester.makepyfile(
        """
        def test_traced():
            assert True
        """
    )

    result = pytester.runpytest_subprocess(
        "-n",
        "2",
        "-p",
        "no:sugar",
        "-q",
    )

    result.assert_outcomes(passed=1)


@pytest.mark.parametrize("provider_preinstalled", [False, True])
def test_explicit_otlp_export_preserves_offline_ai_guard(
    pytester: pytest.Pytester,
    monkeypatch: pytest.MonkeyPatch,
    provider_preinstalled: bool,
) -> None:
    monkeypatch.setenv("OTEL_TRACES_EXPORTER", "otlp_proto_http")
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", "http://127.0.0.1:4318")
    monkeypatch.setenv("OTEL_BSP_SCHEDULE_DELAY", "10")
    guard = Path(__file__).with_name("conftest.py").read_text(encoding="utf-8")
    pytester.makeconftest(
        guard
        + """
from socket import AI_NUMERICHOST, getaddrinfo
from threading import Event
from queue import Queue

import requests

ai_test_started = Event()
collector_result = Queue()

def collector_post(self, url, **kwargs):
    assert ai_test_started.wait(timeout=10)
    try:
        getaddrinfo('127.0.0.1', 4318, flags=AI_NUMERICHOST)
    except OSError as error:
        collector_result.put(str(error))
    else:
        collector_result.put('exported')
    response = requests.Response()
    response.status_code = 200
    return response

requests.Session.post = collector_post

@pytest.fixture
def collector():
    return ai_test_started, collector_result
"""
    )
    ai_suite = pytester.path / "runtime_ai"
    ai_suite.mkdir()
    sample = ai_suite / "test_sample.py"
    sample.write_text(
        """
from concurrent.futures import ThreadPoolExecutor
from socket import AI_NUMERICHOST, getaddrinfo

import pytest

def test_export_trace(collector):
    started, result = collector
    started.set()
    assert result.get(timeout=10) == 'exported'

def test_block_ai_connection():
    with ThreadPoolExecutor(max_workers=1) as executor:
        lookup = executor.submit(getaddrinfo, '127.0.0.1', 9, flags=AI_NUMERICHOST)
        with pytest.raises(OSError, match='AI tests must use offline transports'):
            lookup.result(timeout=10)
    print('AI worker network blocked')
""",
        encoding="utf-8",
    )

    args = ("--export-traces", "-n", "0", "-qs", str(sample))
    if provider_preinstalled:
        runner = pytester.makepyfile(
            runner="""
            import sys

            import pytest
            from opentelemetry import trace
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
                OTLPSpanExporter,
            )
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import BatchSpanProcessor

            provider = TracerProvider()
            provider.add_span_processor(BatchSpanProcessor(
                OTLPSpanExporter(endpoint='http://127.0.0.1:43181/v1/traces'),
            ))
            trace.set_tracer_provider(provider)
            raise SystemExit(pytest.main(sys.argv[1:]))
            """
        )
        result = pytester.run(sys.executable, str(runner), *args)
        result.assert_outcomes(failed=2)
        result.stdout.fnmatch_lines(["*test_export_trace - AssertionError*"])
    else:
        result = pytester.runpytest_subprocess(*args)
        result.assert_outcomes(passed=1, failed=1)

    result.stdout.fnmatch_lines(
        ["*AI worker network blocked*", "*AI test attempted to resolve or connect*"]
    )
