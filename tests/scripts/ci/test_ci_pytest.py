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
            {"FULL_TESTS": "true", "FULL_UNIT": "true"},
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
    proc = run_step("pytest.sh", repo, env, **(selection | boundary_state))

    assert proc.returncode == 0, proc.stderr
    calls = tool_calls(tool_env)
    assert len(calls) == 1
    assert calls[0][10:] == [*excluded, *expected]


def test_pytest_failure_propagates(repo: Path, tool_env: dict[str, str]) -> None:
    proc = run_step(
        "pytest.sh", repo, tool_env, TARGETS="tests/one", FAIL_COMMAND="uv run"
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
        "pytest.sh",
        repo,
        tool_env,
        **selection,
        BOUNDARIES_CHECKED="true",
        FAIL_COMMAND="uv run",
    )

    assert proc.returncode == 17
    assert len(tool_calls(tool_env)) == 1


@pytest.mark.parametrize("boundaries_checked", ["false", "true"])
@pytest.mark.parametrize(
    "targets",
    [
        "tests/scripts/ci",
        "tests/scripts/ci/test_ci_classifier.py tests/scripts/ci/test_ci_steps.py",
    ],
)
def test_full_unit_also_runs_selected_ci_component_contracts(
    repo: Path, tool_env: dict[str, str], targets: str, boundaries_checked: str
) -> None:
    proc = run_step(
        "pytest.sh",
        repo,
        tool_env,
        FULL_UNIT="true",
        TARGETS=targets,
        CI_TARGETS=targets,
        BOUNDARIES_CHECKED=boundaries_checked,
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


def test_full_unit_ci_followup_failure_propagates(
    repo: Path, tool_env: dict[str, str]
) -> None:
    proc = run_step(
        "pytest.sh",
        repo,
        tool_env,
        FULL_UNIT="true",
        CI_TARGETS="tests/scripts/ci",
        BOUNDARIES_CHECKED="true",
        FAIL_COMMAND=(
            "uv run --no-sync pytest -q -p no:sugar --color=no --tb=short -ra "
            '-m "not unit and not memory and not stress"'
        ),
    )

    assert proc.returncode == 17
    assert len(tool_calls(tool_env)) == 2


@pytest.mark.parametrize(
    ("paths", "full_tests", "expected"),
    [
        (
            ["uv.lock", "openspec/specs/unmapped-ci-dedup/spec.md"],
            "true",
            [
                [
                    "--ignore=tests/review_ai/test_dependency_boundaries.py",
                    "-n",
                    "auto",
                    "-m",
                    "not memory and not stress",
                ],
            ],
        ),
        (
            ["uv.lock"],
            "false",
            [["-n", "auto", "-m", "unit and not memory and not stress"]],
        ),
        (
            ["uv.lock", "scripts/ci/pytest.sh"],
            "false",
            [
                ["-n", "auto", "-m", "unit and not memory and not stress"],
                ["-m", "not unit and not memory and not stress", "tests/scripts/ci"],
            ],
        ),
    ],
    ids=["dependency-and-unmapped-spec", "dependency-only", "dependency-and-ci"],
)
def test_dependency_selection_preserves_full_suite_and_unit_followup(
    repo: Path,
    tool_env: dict[str, str],
    paths: list[str],
    full_tests: str,
    expected: list[list[str]],
) -> None:
    scope = run_classifier(paths)

    assert scope["tests"] == "true"
    assert scope["tach"] == "true"
    assert scope["runtime_smoke"] == "true"
    assert scope["full_unit"] == "true"
    assert scope["full_tests"] == full_tests

    proc = run_step(
        "pytest.sh",
        repo,
        tool_env,
        FULL_TESTS=scope["full_tests"],
        FULL_UNIT=scope["full_unit"],
        TARGETS=scope["targets"],
        CI_TARGETS=scope["ci_targets"],
        BOUNDARIES_CHECKED="true",
    )

    assert proc.returncode == 0, proc.stderr
    assert [call[10:] for call in tool_calls(tool_env)] == expected


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
