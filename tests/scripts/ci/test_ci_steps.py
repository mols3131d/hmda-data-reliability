"""CI step contracts with real Git changes and isolated external executables."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.scripts.ci.helpers import commit_change, git, run_step, tool_calls

pytestmark = pytest.mark.component


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
        ["rumdl", "fmt", "docs/changed.md"],
        ["rumdl", "check", "docs/changed.md"],
    ]


def test_inbox_changes_do_not_run_formatter(
    repo: Path, tool_env: dict[str, str]
) -> None:
    commit_change(repo, {"inbox/note.md": "# Note\n"})

    proc = run_step(
        "markdown.sh", repo, tool_env, FORMAT_OUTPUT="Broken link diagnostic"
    )

    assert proc.returncode == 0
    assert proc.stdout == ""
    assert tool_calls(tool_env) == []


def test_formatting_diff_is_nonblocking_and_reported(
    repo: Path, tool_env: dict[str, str]
) -> None:
    commit_change(repo, {"note.md": "# Note\n"})

    proc = run_step("markdown.sh", repo, tool_env, FORMAT_FILE="note.md")

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


@pytest.mark.parametrize("script", ["markdown.sh", "python.sh"])
@pytest.mark.parametrize("revision", ["missing-base", "--quiet", "--stat"])
@pytest.mark.parametrize("position", [0, 1])
def test_invalid_revision_fails_before_tools(
    repo: Path, tool_env: dict[str, str], script: str, revision: str, position: int
) -> None:
    revisions = ["HEAD", "HEAD"]
    revisions[position] = revision
    proc = run_step(script, repo, tool_env, *revisions)

    assert proc.returncode != 0
    assert tool_calls(tool_env) == []


@pytest.mark.parametrize("revision", ["HEAD", "refs/heads/comparison"])
def test_valid_empty_comparison_is_noop(
    repo: Path, tool_env: dict[str, str], revision: str
) -> None:
    git(repo, "branch", "comparison", "HEAD")
    head = git(repo, "rev-parse", "HEAD")
    proc = run_step("markdown.sh", repo, tool_env, revision, head)

    assert proc.returncode == 0, proc.stderr
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
    commit_change(
        repo,
        {
            "deleted.py": None,
            "changed file.py": "value = 1\n",
            "inbox/note.py": "invalid\n",
        },
    )

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
