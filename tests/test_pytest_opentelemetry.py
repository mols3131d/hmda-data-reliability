"""pytest-opentelemetry plugin boundary 테스트."""

from __future__ import annotations

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
