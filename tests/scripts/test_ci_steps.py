"""CI step contracts with real Git changes and isolated external executables."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
CI_SCRIPTS = REPO_ROOT / "scripts/ci"
pytestmark = pytest.mark.component


@pytest.fixture
def workflow_steps() -> dict[str, dict[str, object]]:
    workflow = yaml.safe_load(
        (REPO_ROOT / ".github/workflows/ci-lite.yml").read_text(encoding="utf-8")
    )
    return {step["name"]: step for step in workflow["jobs"]["check"]["steps"]}


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, check=True
    ).stdout.strip()


def commit_change(repo: Path, files: dict[str, str | None]) -> None:
    for name, content in files.items():
        path = repo / name
        if content is None:
            path.unlink()
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "-c", "commit.gpgsign=false", "commit", "-qm", "test change")


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    git(root, "init", "-qb", "main")
    git(root, "config", "user.email", "ci-test@example.invalid")
    git(root, "config", "user.name", "CI Test")
    git(root, "-c", "commit.gpgsign=false", "commit", "--allow-empty", "-qm", "base")
    return root


@pytest.fixture
def tool_env(tmp_path: Path) -> dict[str, str]:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake_tool = (
        f"#!{sys.executable}\n"
        + """import json
import os
import shlex
import sys
from pathlib import Path

name = Path(sys.argv[0]).name
args = [name, *sys.argv[1:]]
with Path(os.environ["CI_LOG"]).open("a", encoding="utf-8") as log:
    log.write(json.dumps(args) + "\\n")
if args[:2] == ["rumdl", "fmt"]:
    print(os.environ.get("FORMAT_OUTPUT", ""))
    if os.environ.get("FORMAT_FILE"):
        with Path(os.environ["FORMAT_FILE"]).open("a", encoding="utf-8") as doc:
            doc.write("\\nFormatted\\n")
failure = shlex.split(os.environ.get("FAIL_COMMAND", ""))
if failure and args[:len(failure)] == failure:
    sys.exit(17)
"""
    )
    for name in ("rumdl", "uv", "npm", "python", "python3"):
        path = bin_dir / name
        path.write_text(fake_tool, encoding="utf-8")
        path.chmod(0o755)
    return os.environ | {
        "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
        "CI_LOG": str(tmp_path / "calls.jsonl"),
        "GITHUB_STEP_SUMMARY": str(tmp_path / "summary.md"),
        "FULL_TESTS": "false",
        "FULL_UNIT": "false",
        "TARGETS": "",
        "CI_TARGETS": "",
        "FULL_TYPE": "false",
        "TYPE_TARGETS": "",
        "BULK": "false",
        "ARCHIVED": "false",
        "SPEC_TARGETS": "",
        "CHANGE_TARGETS": "",
        "FORMAT_OUTPUT": "",
        "FORMAT_FILE": "",
        "FAIL_COMMAND": "",
    }


def run_step(
    name: str,
    repo: Path,
    env: dict[str, str],
    *args: str,
    **overrides: str,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(CI_SCRIPTS / name), *args],
        cwd=repo,
        env=env | overrides,
        capture_output=True,
        text=True,
        check=False,
    )


def tool_calls(env: dict[str, str]) -> list[list[str]]:
    log = Path(env["CI_LOG"])
    return (
        [json.loads(line) for line in log.read_text().splitlines()]
        if log.exists()
        else []
    )


def test_markdown_lints_only_changed_docs(repo: Path, tool_env: dict[str, str]) -> None:
    commit_change(repo, {"docs/untouched.md": "# Keep\n", "deleted.md": "# Delete\n"})
    commit_change(
        repo,
        {
            "docs/changed.md": "# Changed\n",
            "inbox/note with spaces.md": "# Note\n",
            "deleted.md": None,
        },
    )

    proc = run_step("markdown.sh", repo, tool_env)

    assert proc.returncode == 0, proc.stderr
    assert tool_calls(tool_env) == [
        ["rumdl", "fmt", "docs/changed.md", "inbox/note with spaces.md"],
        ["rumdl", "check", "docs/changed.md"],
    ]


def test_inbox_format_diagnostics_are_informational(
    repo: Path, tool_env: dict[str, str]
) -> None:
    commit_change(repo, {"inbox/note.md": "# Note\n"})

    proc = run_step(
        "markdown.sh", repo, tool_env, FORMAT_OUTPUT="Broken link diagnostic"
    )

    assert proc.returncode == 0
    assert "informational" in proc.stdout
    assert "Broken link diagnostic" in proc.stdout
    assert tool_calls(tool_env) == [["rumdl", "fmt", "inbox/note.md"]]


def test_formatting_diff_is_nonblocking_and_reported(
    repo: Path, tool_env: dict[str, str]
) -> None:
    commit_change(repo, {"inbox/note.md": "# Note\n"})

    proc = run_step("markdown.sh", repo, tool_env, FORMAT_FILE="inbox/note.md")

    assert proc.returncode == 0, proc.stderr
    assert "non-blocking" in proc.stdout
    assert "+Formatted" in Path(tool_env["GITHUB_STEP_SUMMARY"]).read_text()


@pytest.mark.parametrize("command", ["rumdl fmt", "rumdl check"])
def test_markdown_required_command_failure_propagates(
    repo: Path, tool_env: dict[str, str], command: str
) -> None:
    commit_change(repo, {"docs/changed.md": "# Changed\n"})

    proc = run_step("markdown.sh", repo, tool_env, FAIL_COMMAND=command)

    assert proc.returncode == 17


def test_deleted_markdown_is_noop(repo: Path, tool_env: dict[str, str]) -> None:
    commit_change(repo, {"deleted.md": "# Delete\n"})
    commit_change(repo, {"deleted.md": None})

    proc = run_step("markdown.sh", repo, tool_env)

    assert proc.returncode == 0, proc.stderr
    assert tool_calls(tool_env) == []


def test_invalid_revision_fails_before_tools(
    repo: Path, tool_env: dict[str, str]
) -> None:
    proc = run_step("markdown.sh", repo, tool_env, "missing-base", "HEAD")

    assert proc.returncode != 0
    assert tool_calls(tool_env) == []


@pytest.mark.parametrize(
    ("selection", "expected"),
    [
        ({"BULK": "true", "ARCHIVED": "true"}, [["--all", "--strict"]]),
        (
            {"SPEC_TARGETS": "spec-one spec-two", "CHANGE_TARGETS": "change-one"},
            [
                ["spec-one", "--type", "spec", "--strict"],
                ["spec-two", "--type", "spec", "--strict"],
                ["change-one", "--type", "change", "--strict"],
            ],
        ),
        ({"ARCHIVED": "true"}, [["--archived"]]),
        (
            {"CHANGE_TARGETS": "change-one", "ARCHIVED": "true"},
            [["change-one", "--type", "change", "--strict"], ["--archived"]],
        ),
    ],
)
def test_openspec_target_modes(
    repo: Path,
    tool_env: dict[str, str],
    selection: dict[str, str],
    expected: list[list[str]],
) -> None:
    proc = run_step("openspec.sh", repo, tool_env, **selection)

    assert proc.returncode == 0, proc.stderr
    prefix = [
        "npm",
        "exec",
        "--yes",
        "--package",
        "@fission-ai/openspec@1.12.0",
        "--",
        "openspec",
        "validate",
    ]
    assert tool_calls(tool_env) == [prefix + args for args in expected]


def test_openspec_missing_target_fails(repo: Path, tool_env: dict[str, str]) -> None:
    proc = run_step("openspec.sh", repo, tool_env)

    assert proc.returncode == 1
    assert "not assigned a validation target" in proc.stderr
    assert tool_calls(tool_env) == []


def test_openspec_failure_stops_later_targets(
    repo: Path, tool_env: dict[str, str]
) -> None:
    proc = run_step(
        "openspec.sh",
        repo,
        tool_env,
        SPEC_TARGETS="spec-one spec-two",
        FAIL_COMMAND="npm exec",
    )

    assert proc.returncode == 17
    assert len(tool_calls(tool_env)) == 1


def test_python_scoped_types_include_changed_files(
    repo: Path, tool_env: dict[str, str]
) -> None:
    commit_change(repo, {"deleted.py": "old = True\n", "unchanged.py": "keep = True\n"})
    commit_change(repo, {"deleted.py": None, "changed file.py": "value = 1\n"})

    proc = run_step("python.sh", repo, tool_env, TYPE_TARGETS="src/domain tests/domain")

    assert proc.returncode == 0, proc.stderr
    assert tool_calls(tool_env) == [
        ["uv", "run", "--no-sync", "ruff", "check", "changed file.py"],
        ["uv", "run", "--no-sync", "ruff", "format", "--check", "changed file.py"],
        [
            "uv",
            "run",
            "--no-sync",
            "ty",
            "check",
            "src/domain",
            "tests/domain",
            "changed file.py",
        ],
    ]


def test_python_dependency_only_full_type_check(
    repo: Path, tool_env: dict[str, str]
) -> None:
    commit_change(repo, {"pyproject.toml": "[project]\n"})

    proc = run_step(
        "python.sh", repo, tool_env, FULL_TYPE="true", TYPE_TARGETS="ignored"
    )

    assert proc.returncode == 0, proc.stderr
    assert tool_calls(tool_env) == [["uv", "run", "--no-sync", "ty", "check"]]


@pytest.mark.parametrize("command", ["ruff check", "ruff format", "ty check"])
def test_python_command_failure_propagates(
    repo: Path, tool_env: dict[str, str], command: str
) -> None:
    commit_change(repo, {"changed.py": "value = 1\n"})

    proc = run_step(
        "python.sh", repo, tool_env, FAIL_COMMAND=f"uv run --no-sync {command}"
    )

    assert proc.returncode == 17


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


def test_full_unit_also_runs_selected_ci_component_contracts(
    repo: Path, tool_env: dict[str, str]
) -> None:
    proc = run_step(
        "pytest.sh",
        repo,
        tool_env,
        FULL_UNIT="true",
        TARGETS="tests/scripts/test_ci_classifier.py tests/scripts/test_ci_steps.py",
        CI_TARGETS="tests/scripts/test_ci_classifier.py tests/scripts/test_ci_steps.py",
    )

    assert proc.returncode == 0, proc.stderr
    calls = tool_calls(tool_env)
    assert len(calls) == 2
    assert calls[0][-4:] == ["-n", "auto", "-m", "unit and not memory and not stress"]
    assert calls[1][-4:] == [
        "-m",
        "not unit and not memory and not stress",
        "tests/scripts/test_ci_classifier.py",
        "tests/scripts/test_ci_steps.py",
    ]


def test_full_unit_failure_does_not_run_ci_followup(
    repo: Path, tool_env: dict[str, str]
) -> None:
    proc = run_step(
        "pytest.sh",
        repo,
        tool_env,
        FULL_UNIT="true",
        CI_TARGETS="tests/scripts/test_ci_steps.py",
        FAIL_COMMAND="uv run",
    )

    assert proc.returncode == 17
    assert len(tool_calls(tool_env)) == 1


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
    assert set(scope["ci_targets"].split()) == {
        "tests/scripts/test_ci_classifier.py",
        "tests/scripts/test_ci_steps.py",
    }


def test_workflow_passes_ci_component_targets(
    workflow_steps: dict[str, dict[str, object]],
) -> None:
    assert workflow_steps["Run selected tests"]["env"] == {
        "FULL_TESTS": "${{ steps.scope.outputs.full_tests }}",
        "FULL_UNIT": "${{ steps.scope.outputs.full_unit }}",
        "TARGETS": "${{ steps.scope.outputs.targets }}",
        "CI_TARGETS": "${{ steps.scope.outputs.ci_targets }}",
    }


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
            "Validate changed Inbox artifacts",
            "inbox/changed note.md",
            [
                [
                    "python3",
                    "scripts/validate_inbox_artifacts.py",
                    "inbox/changed note.md",
                ]
            ],
        ),
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
    commit_change(repo, {filename: "fixture\n", "unrelated.md": None})

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
        "Validate changed Inbox artifacts",
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
