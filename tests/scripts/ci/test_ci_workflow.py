from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from tests.scripts.ci.helpers import CI_SCRIPTS, REPO_ROOT, commit_change, tool_calls

pytestmark = pytest.mark.component


def test_workflow_classifier_writes_scope_outputs(
    repo: Path,
    tool_env: dict[str, str],
    workflow_steps: dict[str, dict[str, object]],
) -> None:
    (repo / "scripts").symlink_to(REPO_ROOT / "scripts", target_is_directory=True)
    commit_change(repo, {".github/workflows/ci-lite.yml": "fixture\n"})
    output = repo / "scope-output"
    step = workflow_steps["Classify changes"]

    assert step["id"] == "scope"
    assert step["run"] == 'bash scripts/ci/classify_changes.sh "$GITHUB_OUTPUT"'
    proc = subprocess.run(
        ["bash", "-c", str(step["run"])],
        cwd=repo,
        env=tool_env | {"GITHUB_OUTPUT": str(output)},
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    assert proc.stdout == ""
    scope = dict(line.split("=", 1) for line in output.read_text().splitlines())
    assert scope["tests"] == "true"
    assert scope["tach"] == "false"
    assert scope["ci_targets"].split() == ["tests/scripts/ci"]


def test_workflow_passes_ci_component_targets(
    workflow_steps: dict[str, dict[str, object]],
) -> None:
    assert workflow_steps["Run selected tests"]["env"] == {
        "FULL_TESTS": "${{ steps.scope.outputs.full_tests }}",
        "FULL_UNIT": "${{ steps.scope.outputs.full_unit }}",
        "TARGETS": "${{ steps.scope.outputs.targets }}",
        "CI_TARGETS": "${{ steps.scope.outputs.ci_targets }}",
        "BOUNDARIES_CHECKED": "${{ steps.boundaries.outcome == 'success' }}",
    }


def test_workflow_deduplicates_only_successful_prior_checks(
    workflow_steps: dict[str, dict[str, object]],
) -> None:
    boundary = workflow_steps["Check Python dependency boundaries"]
    selected = workflow_steps["Run selected tests"]
    smoke = workflow_steps["Run dependency runtime smoke"]
    names = list(workflow_steps)

    assert boundary["id"] == "boundaries"
    assert selected["id"] == "selected_tests"
    assert (
        names.index("Check Python dependency boundaries")
        < names.index("Run selected tests")
        < names.index("Run dependency runtime smoke")
    )
    assert smoke["if"] == (
        "steps.scope.outputs.runtime_smoke == 'true' && "
        "!(steps.scope.outputs.full_tests == 'true' && "
        "steps.selected_tests.outcome == 'success')"
    )
    for step in (boundary, selected, smoke):
        assert step.get("continue-on-error", False) is False


@pytest.mark.parametrize("fail_command", ["", "uv run --no-sync pytest"])
def test_workflow_runtime_smoke_preserves_targets_and_failure(
    repo: Path,
    tool_env: dict[str, str],
    workflow_steps: dict[str, dict[str, object]],
    fail_command: str,
) -> None:
    step = workflow_steps["Run dependency runtime smoke"]
    proc = subprocess.run(
        ["bash", "-c", str(step["run"])],
        cwd=repo,
        env=tool_env | {"FAIL_COMMAND": fail_command},
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == (17 if fail_command else 0)
    assert tool_calls(tool_env) == [
        [
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
            "-m",
            "not memory and not stress",
            "tests/dbt/test_analytics_foundation.py",
            "tests/orchestration/test_airflow_dag.py",
        ]
    ]


def test_workflow_tach_step_runs_required_checks(
    repo: Path,
    tool_env: dict[str, str],
    workflow_steps: dict[str, dict[str, object]],
) -> None:
    step = workflow_steps["Check Python dependency boundaries"]
    assert step["if"] == "steps.scope.outputs.tach == 'true'"

    proc = subprocess.run(
        ["bash", "-c", str(step["run"])],
        cwd=repo,
        env=tool_env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    assert tool_calls(tool_env) == [
        ["uv", "run", "--no-sync", "tach", "check"],
        [
            "uv",
            "run",
            "--no-sync",
            "pytest",
            "-q",
            "-p",
            "no:sugar",
            "--tb=short",
            "tests/scripts/test_tach.py",
            "tests/scripts/test_tach_config.py",
            "tests/review_ai/test_dependency_boundaries.py",
        ],
    ]


@pytest.mark.parametrize(
    ("command", "expected_call_count"),
    [
        ("uv run --no-sync tach check", 1),
        ("uv run --no-sync pytest", 2),
    ],
)
def test_workflow_tach_step_failure_propagates(
    repo: Path,
    tool_env: dict[str, str],
    workflow_steps: dict[str, dict[str, object]],
    command: str,
    expected_call_count: int,
) -> None:
    step = workflow_steps["Check Python dependency boundaries"]
    proc = subprocess.run(
        ["bash", "-c", str(step["run"])],
        cwd=repo,
        env=tool_env | {"FAIL_COMMAND": command},
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 17
    assert len(tool_calls(tool_env)) == expected_call_count


@pytest.mark.parametrize(
    ("step_name", "script", "selector"),
    [
        ("Format changed Markdown and validate docs", "markdown.sh", "markdown"),
        ("Validate OpenSpec", "openspec.sh", "openspec"),
        ("Validate Python", "python.sh", "python"),
        ("Run selected tests", "pytest.sh", "tests"),
    ],
)
def test_workflow_calls_selected_script(
    workflow_steps: dict[str, dict[str, object]],
    step_name: str,
    script: str,
    selector: str,
) -> None:
    step = workflow_steps[step_name]

    assert step["run"] == f"bash scripts/ci/{script}"
    assert step["if"] == f"steps.scope.outputs.{selector} == 'true'"
    assert (CI_SCRIPTS / script).is_file()


@pytest.mark.parametrize(
    ("step_name", "filename", "expected"),
    [
        (
            "Validate changed JSON",
            "changed.jsonc",
            [["python", "scripts/biome.py", "check", "changed.jsonc"]],
        ),
        (
            "Validate changed TOML",
            "changed.toml",
            [
                ["python", "scripts/tombi.py", "format", "--check", "changed.toml"],
                ["python", "scripts/tombi.py", "lint", "changed.toml"],
            ],
        ),
    ],
)
def test_workflow_simple_steps_collect_only_existing_changed_files(
    repo: Path,
    tool_env: dict[str, str],
    workflow_steps: dict[str, dict[str, object]],
    step_name: str,
    filename: str,
    expected: list[list[str]],
) -> None:
    (repo / "scripts").symlink_to(REPO_ROOT / "scripts", target_is_directory=True)
    commit_change(repo, {"unrelated.md": "# Keep\n"})
    commit_change(
        repo,
        {filename: "fixture\n", f"inbox/{filename}": "invalid\n", "unrelated.md": None},
    )

    proc = subprocess.run(
        ["bash", "-c", str(workflow_steps[step_name]["run"])],
        cwd=repo,
        env=tool_env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    assert tool_calls(tool_env) == expected


@pytest.mark.parametrize(
    "step_name",
    [
        "Validate changed JSON",
        "Validate changed TOML",
    ],
)
def test_workflow_simple_steps_fail_on_invalid_comparison(
    repo: Path,
    tool_env: dict[str, str],
    workflow_steps: dict[str, dict[str, object]],
    step_name: str,
) -> None:
    (repo / "scripts").symlink_to(REPO_ROOT / "scripts", target_is_directory=True)

    proc = subprocess.run(
        ["bash", "-c", str(workflow_steps[step_name]["run"])],
        cwd=repo,
        env=tool_env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode != 0
    assert tool_calls(tool_env) == []


def test_workflow_has_no_inbox_validator(
    workflow_steps: dict[str, dict[str, object]],
) -> None:
    assert "Validate changed Inbox artifacts" not in workflow_steps
