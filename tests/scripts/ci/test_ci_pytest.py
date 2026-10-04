from __future__ import annotations

from pathlib import Path

import pytest

from tests.scripts.ci.helpers import run_classifier, run_step, tool_calls

pytestmark = pytest.mark.component


@pytest.mark.parametrize(
    ("selection", "expected"),
    [
        ({"TARGETS": "tests/one"}, ["-m", "not memory and not stress", "tests/one"]),
        (
            {"TARGETS": "tests/one tests/two tests/three"},
            [
                "-n",
                "auto",
                "-m",
                "not memory and not stress",
                "tests/one",
                "tests/two",
                "tests/three",
            ],
        ),
        (
            {"FULL_UNIT": "true"},
            ["-n", "auto", "-m", "unit and not memory and not stress"],
        ),
        (
            {"FULL_TESTS": "true", "FULL_UNIT": "true", "TARGETS": "ignored"},
            ["-n", "auto", "-m", "not memory and not stress"],
        ),
        ({}, []),
    ],
)
def test_pytest_selection_preserves_markers_and_parallel_threshold(
    repo: Path,
    tool_env: dict[str, str],
    selection: dict[str, str],
    expected: list[str],
) -> None:
    proc = run_step("pytest.sh", repo, tool_env, **selection)

    assert proc.returncode == 0, proc.stderr
    prefix = [
        "uv",
        "run",
        "--no-sync",
        "pytest",
        "-q",
        "-p",
        "no:sugar",
        "--color=no",
        "--tb=short",
        "-ra",
    ]
    assert tool_calls(tool_env) == ([prefix + expected] if expected else [])


def test_pytest_failure_propagates(repo: Path, tool_env: dict[str, str]) -> None:
    proc = run_step(
        "pytest.sh", repo, tool_env, TARGETS="tests/one", FAIL_COMMAND="uv run"
    )

    assert proc.returncode == 17


@pytest.mark.parametrize(
    "targets",
    [
        "tests/scripts/ci",
        "tests/scripts/ci/test_ci_classifier.py tests/scripts/ci/test_ci_steps.py",
    ],
)
def test_full_unit_also_runs_selected_ci_component_contracts(
    repo: Path, tool_env: dict[str, str], targets: str
) -> None:
    proc = run_step(
        "pytest.sh",
        repo,
        tool_env,
        FULL_UNIT="true",
        TARGETS=targets,
        CI_TARGETS=targets,
    )

    assert proc.returncode == 0, proc.stderr
    calls = tool_calls(tool_env)
    assert len(calls) == 2
    assert calls[0][-4:] == ["-n", "auto", "-m", "unit and not memory and not stress"]
    assert calls[1][10:] == [
        "-m",
        "not unit and not memory and not stress",
        *targets.split(),
    ]


def test_full_unit_failure_does_not_run_ci_followup(
    repo: Path, tool_env: dict[str, str]
) -> None:
    proc = run_step(
        "pytest.sh",
        repo,
        tool_env,
        FULL_UNIT="true",
        CI_TARGETS="tests/scripts/ci/test_ci_steps.py",
        FAIL_COMMAND="uv run",
    )

    assert proc.returncode == 17
    assert len(tool_calls(tool_env)) == 1


@pytest.mark.parametrize(
    "path",
    [
        "tests/scripts/ci/test_ci_classifier_openspec.py",
        "tests/scripts/ci/test_ci_classifier_python.py",
    ],
)
def test_dependency_and_unit_only_ci_test_run_no_followup(
    repo: Path, tool_env: dict[str, str], path: str
) -> None:
    scope = run_classifier(["uv.lock", path])

    proc = run_step(
        "pytest.sh",
        repo,
        tool_env,
        FULL_UNIT=scope["full_unit"],
        TARGETS=scope["targets"],
        CI_TARGETS=scope["ci_targets"],
    )

    assert proc.returncode == 0, proc.stderr
    calls = tool_calls(tool_env)
    assert len(calls) == 1
    assert calls[0][-4:] == ["-n", "auto", "-m", "unit and not memory and not stress"]
