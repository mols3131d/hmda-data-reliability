"""CI step contracts with real Git changes and isolated external executables."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

from scripts.ci.changed_files import collect_changed_files, entrypoint
from tests.scripts.ci.helpers import (
    commit_change,
    git,
    run_classifier,
    run_step,
    tool_calls,
)

pytestmark = pytest.mark.component


def test_actual_zizmor_collects_ignored_inputs_and_excludes_mixed_inbox(
    repo: Path,
) -> None:
    uvx = shutil.which("uvx")
    if uvx is None:
        pytest.skip("Actual audit requires uvx and cached zizmor@1.30.1")
    environment = {
        key: value
        for key, value in os.environ.items()
        if key not in {"UV_ENV_FILE", "GH_TOKEN", "GITHUB_TOKEN", "ZIZMOR_GITHUB_TOKEN"}
    } | {"UV_OFFLINE": "true", "ZIZMOR_VERSION": "1.30.1"}
    if cache := environment.get("UV_CACHE_DIR"):
        environment["UV_CACHE_DIR"] = str(Path(cache).resolve())
    version = subprocess.run(
        [uvx, "zizmor@1.30.1", "--version"],
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    if version.returncode and "network was disabled" in version.stderr.lower():
        pytest.skip("Actual audit requires zizmor@1.30.1 cached by the audit step")
    assert version.returncode == 0, version.stderr
    assert version.stdout.strip() == "zizmor 1.30.1"
    workflow = (
        "name: Check\non: push\npermissions:\n  contents: read\n"
        "jobs:\n  check:\n    runs-on: ubuntu-latest\n"
        "    steps:\n      - run: echo ok\n"
    )
    unsafe_action = (
        "name: Probe\ndescription: Input probe\nruns:\n  using: composite\n"
        "  steps:\n    - uses: actions/checkout@v6.0.2\n"
        "      with:\n        persist-credentials: false\n"
    )
    commit_change(
        repo,
        {
            ".github/workflows/check.yml": workflow,
            "tools/with spaces/action.yml": unsafe_action,
            "inbox/probe/action.yml": "runs: [invalid\n",
        },
    )
    commit_change(repo, {".gitignore": "tools/\n"})

    unsafe = run_step("zizmor", repo, environment)

    assert unsafe.returncode == 14, unsafe.stdout + unsafe.stderr
    assert "unpinned-uses" in unsafe.stdout
    assert "tools/with spaces/action.yml" in unsafe.stdout
    safe_action = unsafe_action.replace(
        "actions/checkout@v6.0.2",
        "actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd",
    )
    commit_change(repo, {"tools/with spaces/action.yml": safe_action})

    safe = run_step("zizmor", repo, environment)

    assert safe.returncode == 0, safe.stdout + safe.stderr
    assert "inbox/probe" not in safe.stdout + safe.stderr


@pytest.mark.parametrize("failure", ["", "uvx"])
def test_zizmor_audits_tracked_ignored_definitions_without_inbox(
    repo: Path, tool_env: dict[str, str], failure: str
) -> None:
    commit_change(
        repo,
        {
            ".github/workflows/check.yaml": "fixture\n",
            "action.yml": "fixture\n",
            "tools/with spaces/action.yaml": "fixture\n",
            "inbox/example/action.yml": "fixture\n",
            "notes.yaml": "fixture\n",
        },
    )
    commit_change(repo, {".gitignore": ".github/workflows/\naction.yml\naction.yaml\n"})
    untracked = repo / "untracked/action.yml"
    untracked.parent.mkdir()
    untracked.write_text("fixture\n", encoding="utf-8")
    binary_dir = Path(tool_env["PATH"].split(":", 1)[0])
    (binary_dir / "uvx").symlink_to(binary_dir / "uv")
    scope = run_classifier(
        [".github/workflows/check.yaml", "inbox/example/action.yml"], repo_root=repo
    )
    assert scope["zizmor"] == "true"

    proc = run_step(
        "zizmor", repo, tool_env, ZIZMOR_VERSION="1.30.1", FAIL_COMMAND=failure
    )

    assert proc.returncode == (17 if failure else 0), proc.stderr
    assert tool_calls(tool_env) == [
        [
            "uvx",
            "zizmor@1.30.1",
            "--offline",
            "--strict-collection",
            "--collect=workflows,actions",
            "--persona=regular",
            "--no-config",
            "--format=github",
            "./.github/workflows/check.yaml",
            "./action.yml",
            "./tools/with spaces/action.yaml",
        ]
    ]


@pytest.mark.parametrize("git_available", [True, False])
def test_zizmor_fails_without_tracked_inputs(
    repo: Path, tool_env: dict[str, str], git_available: bool
) -> None:
    root = repo if git_available else repo.parent
    if not git_available:
        git(root, "init", "-qb", "empty")
        (root / ".git").rename(root / "broken-git")
    proc = run_step("zizmor", root, tool_env, GIT_CEILING_DIRECTORIES=str(root.parent))

    assert proc.returncode == (1 if git_available else 128), proc.stderr
    assert tool_calls(tool_env) == []


@pytest.mark.parametrize(
    "target",
    ["scripts/renamed_entrypoint.py", "openspec/specs/new-capability/spec.md"],
)
def test_unregistered_names_select_full_suite_and_preserve_spec_structure(
    repo: Path, tool_env: dict[str, str], target: str
) -> None:
    commit_change(repo, {target: "fixture\n"})
    (repo / "openspec/changes").mkdir(parents=True, exist_ok=True)
    scope = run_classifier([target], repo_root=repo)

    assert scope["tests"] == scope["full_tests"] == "true"
    assert scope["python"] == scope["full_type"] == "true"
    assert scope["targets"] == ""
    if target.startswith("openspec/"):
        assert scope["openspec_bulk"] == "false"
        assert scope["openspec_spec_targets"] == "new-capability"
    proc = run_step(
        "pytest",
        repo,
        tool_env,
        FULL_TESTS=scope["full_tests"],
        TARGETS=scope["targets"],
    )

    assert proc.returncode == 0, proc.stderr
    calls = tool_calls(tool_env)
    assert len(calls) == 1
    assert calls[0][calls[0].index("-n") :] == [
        "-n",
        "auto",
        "-m",
        "not memory and not stress",
    ]


@pytest.mark.parametrize("separator", [" ", "\t"])
def test_ascii_whitespace_directory_uses_full_suite_without_split_targets(
    repo: Path, tool_env: dict[str, str], separator: str
) -> None:
    target = f"tests/data_platform{separator}scripts/test_probe.py"
    commit_change(repo, {target: "assert False\n"})
    scope = run_classifier([target], repo_root=repo)

    assert scope["full_tests"] == scope["python"] == scope["full_type"] == "true"
    assert scope["targets"] == ""
    proc = run_step(
        "pytest",
        repo,
        tool_env,
        FULL_TESTS=scope["full_tests"],
        TARGETS=scope["targets"],
    )

    assert proc.returncode == 0, proc.stderr
    calls = tool_calls(tool_env)
    assert len(calls) == 1
    assert calls[0][calls[0].index("-n") :] == [
        "-n",
        "auto",
        "-m",
        "not memory and not stress",
    ]


def test_selected_unicode_space_path_remains_one_argument(
    repo: Path, tool_env: dict[str, str]
) -> None:
    target = (
        "tests/scripts/ci/test_ci_pytest.py\u00a0"
        "tests/scripts/ci/test_ci_classifier_python.py"
    )
    commit_change(repo, {target: "assert False\n"})
    scope = run_classifier([target], repo_root=repo)

    proc = run_step(
        "pytest",
        repo,
        tool_env,
        TARGETS=target,
    )

    assert proc.returncode == 0, proc.stderr
    assert scope["targets"] == "tests/scripts/ci"
    call = tool_calls(tool_env)[-1]
    assert call[-1] == target
    assert "tests/scripts/ci/test_ci_pytest.py" not in call
    assert "tests/scripts/ci/test_ci_classifier_python.py" not in call


@pytest.mark.parametrize("code", [17, -15])
def test_entrypoint_preserves_shell_failure_status(code: int) -> None:
    def fail() -> None:
        raise subprocess.CalledProcessError(code, ["tool"])

    with pytest.raises(SystemExit) as error:
        entrypoint(fail)

    assert error.value.code == (17 if code == 17 else 143)


@pytest.mark.parametrize(
    ("failure", "code"), [(FileNotFoundError, 127), (PermissionError, 126)]
)
def test_entrypoint_reports_tool_execution_errors(
    failure: type[OSError], code: int, capsys: pytest.CaptureFixture[str]
) -> None:
    def fail() -> None:
        raise failure("tool unavailable")

    with pytest.raises(SystemExit) as error:
        entrypoint(fail)
    assert error.value.code == code
    assert "tool unavailable" in capsys.readouterr().err


def test_changed_files_preserves_git_paths(repo: Path) -> None:
    commit_change(repo, {"deleted.md": "# Delete\n"})
    commit_change(
        repo,
        {
            "deleted.md": None,
            'docs/quote"name.md': "# Quote\n",
            "docs/tab\tname.md": "# Tab\n",
            "inbox/note.md": "# Excluded\n",
        },
    )

    assert collect_changed_files(patterns=("*.md",), cwd=repo) == [
        'docs/quote"name.md',
        "docs/tab\tname.md",
    ]


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

    proc = run_step("markdown", repo, tool_env)

    assert proc.returncode == 0, proc.stderr
    assert tool_calls(tool_env) == [
        ["rumdl", "fmt", "docs/changed.md"],
        ["rumdl", "check", "docs/changed.md"],
    ]


def test_inbox_changes_do_not_run_formatter(
    repo: Path, tool_env: dict[str, str]
) -> None:
    commit_change(repo, {"inbox/note.md": "# Note\n"})

    proc = run_step("markdown", repo, tool_env, FORMAT_OUTPUT="Broken link diagnostic")

    assert proc.returncode == 0
    assert proc.stdout == ""
    assert tool_calls(tool_env) == []


def test_formatting_diff_is_nonblocking_and_reported(
    repo: Path, tool_env: dict[str, str]
) -> None:
    commit_change(repo, {"note.md": "# Note\n"})

    proc = run_step("markdown", repo, tool_env, FORMAT_FILE="note.md")

    assert proc.returncode == 0, proc.stderr
    assert "non-blocking" in proc.stdout
    assert "+Formatted" in Path(tool_env["GITHUB_STEP_SUMMARY"]).read_text()


@pytest.mark.parametrize("command", ["rumdl fmt", "rumdl check"])
def test_markdown_required_command_failure_propagates(
    repo: Path, tool_env: dict[str, str], command: str
) -> None:
    commit_change(repo, {"docs/changed.md": "# Changed\n"})

    proc = run_step("markdown", repo, tool_env, FAIL_COMMAND=command)

    assert proc.returncode == 17


def test_deleted_markdown_is_noop(repo: Path, tool_env: dict[str, str]) -> None:
    commit_change(repo, {"deleted.md": "# Delete\n"})
    commit_change(repo, {"deleted.md": None})

    proc = run_step("markdown", repo, tool_env)

    assert proc.returncode == 0, proc.stderr
    assert tool_calls(tool_env) == []


@pytest.mark.parametrize("revision", ["missing-base", "--quiet", "--stat"])
@pytest.mark.parametrize("position", [0, 1])
def test_invalid_revision_fails_before_tools(
    repo: Path, tool_env: dict[str, str], revision: str, position: int
) -> None:
    revisions = ["HEAD", "HEAD"]
    revisions[position] = revision
    with pytest.raises(subprocess.CalledProcessError):
        collect_changed_files(*revisions, cwd=repo)
    assert tool_calls(tool_env) == []


@pytest.mark.parametrize("revision", ["HEAD", "refs/heads/comparison"])
def test_valid_empty_comparison_is_noop(
    repo: Path, tool_env: dict[str, str], revision: str
) -> None:
    git(repo, "branch", "comparison", "HEAD")
    head = git(repo, "rev-parse", "HEAD")
    assert collect_changed_files(revision, head, cwd=repo) == []
    assert tool_calls(tool_env) == []


@pytest.mark.parametrize("check", ["markdown", "python", "json", "toml"])
def test_check_cli_rejects_revision_arguments(
    repo: Path, tool_env: dict[str, str], check: str
) -> None:
    proc = run_step(check, repo, tool_env, "HEAD", "HEAD")
    assert proc.returncode == 2
    assert tool_calls(tool_env) == []


def test_toml_without_changed_files_is_noop(
    repo: Path, tool_env: dict[str, str]
) -> None:
    commit_change(repo, {"scripts/tombi.py": "fixture\n"})
    proc = run_step("toml", repo, tool_env)
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
    proc = run_step("openspec", repo, tool_env, **selection)

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
    proc = run_step("openspec", repo, tool_env)

    assert proc.returncode == 1
    assert "not assigned a validation target" in proc.stderr
    assert tool_calls(tool_env) == []


def test_openspec_failure_stops_later_targets(
    repo: Path, tool_env: dict[str, str]
) -> None:
    proc = run_step(
        "openspec",
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

    proc = run_step("python", repo, tool_env, TYPE_TARGETS="src/domain tests/domain")

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

    proc = run_step("python", repo, tool_env, FULL_TYPE="true", TYPE_TARGETS="ignored")

    assert proc.returncode == 0, proc.stderr
    assert tool_calls(tool_env) == [
        ["uv", "run", "--no-sync", "ty", "check", "--exclude", "inbox/**"]
    ]


@pytest.mark.parametrize("command", ["ruff check", "ruff format", "ty check"])
def test_python_command_failure_propagates(
    repo: Path, tool_env: dict[str, str], command: str
) -> None:
    commit_change(repo, {"changed.py": "value = 1\n"})

    proc = run_step(
        "python", repo, tool_env, FAIL_COMMAND=f"uv run --no-sync {command}"
    )

    assert proc.returncode == 17
