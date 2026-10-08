from __future__ import annotations

from pathlib import Path

import pytest

from tests.scripts.ci.helpers import run_classifier, run_step, tool_calls

pytestmark = pytest.mark.component

PYTEST_COMMAND = [
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
            {"FULL_TESTS": "true", "TARGETS": "ignored"},
            ["-n", "auto", "-m", "not memory and not stress"],
        ),
    ],
)
def test_pytest_selection_preserves_markers_and_parallel_threshold(
    repo: Path,
    tool_env: dict[str, str],
    selection: dict[str, str],
    expected: list[str],
) -> None:
    proc = run_step("pytest", repo, tool_env, **selection)

    assert proc.returncode == 0, proc.stderr
    assert tool_calls(tool_env) == [[*PYTEST_COMMAND, *expected]]


@pytest.mark.parametrize("targets", ["", " \t\n"])
@pytest.mark.parametrize("boundary_checked", ["false", "true"])
def test_pytest_missing_selection_fails_before_tools(
    repo: Path, tool_env: dict[str, str], targets: str, boundary_checked: str
) -> None:
    proc = run_step(
        "pytest", repo, tool_env, TARGETS=targets, BOUNDARIES_CHECKED=boundary_checked
    )

    assert proc.returncode == 1
    assert "not assigned a validation target" in proc.stderr
    assert tool_calls(tool_env) == []


@pytest.mark.parametrize(
    ("boundary_state", "excluded"),
    [
        ({}, []),
        ({"BOUNDARIES_CHECKED": "false"}, []),
        (
            {"BOUNDARIES_CHECKED": "true"},
            ["--ignore=tests/review_ai/test_dependency_boundaries.py"],
        ),
    ],
    ids=["unconfirmed", "not-checked", "checked"],
)
@pytest.mark.parametrize(
    ("selection", "expected"),
    [
        (
            {"TARGETS": "tests/runtime_ai tests/review_ai"},
            [
                "-m",
                "not memory and not stress",
                "tests/runtime_ai",
                "tests/review_ai",
            ],
        ),
        (
            {"TARGETS": "tests/reliability tests/review_ai tests/data_operations"},
            [
                "-n",
                "auto",
                "-m",
                "not memory and not stress",
                "tests/reliability",
                "tests/review_ai",
                "tests/data_operations",
            ],
        ),
        (
            {"FULL_TESTS": "true"},
            ["-n", "auto", "-m", "not memory and not stress"],
        ),
    ],
    ids=["scoped", "parallel-scoped", "full-tests"],
)
def test_pytest_excludes_guard_only_after_boundaries_succeed(
    repo: Path,
    tool_env: dict[str, str],
    boundary_state: dict[str, str],
    excluded: list[str],
    selection: dict[str, str],
    expected: list[str],
) -> None:
    env = {key: value for key, value in tool_env.items() if key != "BOUNDARIES_CHECKED"}
    proc = run_step("pytest", repo, env, **(selection | boundary_state))

    assert proc.returncode == 0, proc.stderr
    assert tool_calls(tool_env) == [[*PYTEST_COMMAND, *excluded, *expected]]


def test_pytest_failure_propagates(repo: Path, tool_env: dict[str, str]) -> None:
    proc = run_step(
        "pytest", repo, tool_env, TARGETS="tests/one", FAIL_COMMAND="uv run"
    )

    assert proc.returncode == 17


@pytest.mark.parametrize(
    "selection",
    [{"TARGETS": "tests/review_ai"}, {"FULL_TESTS": "true"}],
    ids=["scoped", "full-tests"],
)
def test_boundary_success_does_not_hide_selected_test_failure(
    repo: Path, tool_env: dict[str, str], selection: dict[str, str]
) -> None:
    proc = run_step(
        "pytest",
        repo,
        tool_env,
        **selection,
        BOUNDARIES_CHECKED="true",
        FAIL_COMMAND="uv run",
    )

    assert proc.returncode == 17
    assert len(tool_calls(tool_env)) == 1


@pytest.mark.parametrize(
    "paths",
    [
        ["uv.lock", "openspec/specs/unmapped-ci-dedup/spec.md"],
        ["uv.lock"],
        ["uv.lock", "scripts/ci/run_checks.py"],
        ["uv.lock", "tests/data_platform/test_artifacts.py"],
        ["uv.lock", "tests/scripts/ci/test_ci_classifier_openspec.py"],
        ["uv.lock", "tests/scripts/ci/test_ci_classifier_python.py"],
    ],
)
def test_broad_selection_preserves_all_non_resource_tests_in_one_run(
    repo: Path,
    tool_env: dict[str, str],
    paths: list[str],
) -> None:
    scope = run_classifier(paths)

    assert scope["tests"] == "true"
    assert scope["tach"] == "true"
    assert scope["full_tests"] == "true"

    proc = run_step(
        "pytest",
        repo,
        tool_env,
        FULL_TESTS=scope["full_tests"],
        TARGETS=scope["targets"],
        BOUNDARIES_CHECKED="true",
    )

    assert proc.returncode == 0, proc.stderr
    assert tool_calls(tool_env) == [
        [
            *PYTEST_COMMAND,
            "--ignore=tests/review_ai/test_dependency_boundaries.py",
            "-n",
            "auto",
            "-m",
            "not memory and not stress",
        ]
    ]
