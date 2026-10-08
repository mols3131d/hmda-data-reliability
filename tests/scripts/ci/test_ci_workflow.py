from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

from tests.scripts.ci.helpers import (
    CI_SCRIPTS,
    REPO_ROOT,
    commit_change,
    run_classifier,
    tool_calls,
)

pytestmark = pytest.mark.component


def test_action_only_changes_prepare_isolated_zizmor(
    workflow_steps: dict[str, dict[str, object]],
) -> None:
    scope = run_classifier([".github/actions/deleted/action.yaml"])
    setup = str(workflow_steps["Set up uv"]["if"])
    selectors = []
    for clause in setup.split(" || "):
        match = re.fullmatch(r"steps\.scope\.outputs\.(\w+) == 'true'", clause)
        assert match is not None, clause
        selectors.append(match.group(1))
    assert any(scope[key] == "true" for key in selectors)
    assert scope["zizmor"] == "true"
    assert scope["tests"] == scope["python"] == scope["tach"] == "false"
    assert workflow_steps["Sync dependencies"]["if"] == (
        "steps.scope.outputs.tests == 'true' || "
        "steps.scope.outputs.python == 'true' || "
        "steps.scope.outputs.tach == 'true'"
    )
    audit = workflow_steps["Audit GitHub Actions with zizmor"]
    assert audit["if"] == "steps.scope.outputs.zizmor == 'true'"
    assert list(workflow_steps).index("Set up uv") < list(workflow_steps).index(
        "Audit GitHub Actions with zizmor"
    )
    assert audit["env"] == {"ZIZMOR_VERSION": "1.30.1"}
    assert not audit.get("continue-on-error", False)


@pytest.mark.parametrize("failure", ["", "uvx"])
def test_zizmor_workflow_command_preserves_flags_and_failure(
    repo: Path,
    tool_env: dict[str, str],
    workflow_steps: dict[str, dict[str, object]],
    failure: str,
) -> None:
    commit_change(repo, {"action.yml": "fixture\n"})
    (repo / "scripts").symlink_to(REPO_ROOT / "scripts", target_is_directory=True)
    binary_dir = Path(tool_env["PATH"].split(":", 1)[0])
    (binary_dir / "uvx").symlink_to(binary_dir / "uv")
    step = workflow_steps["Audit GitHub Actions with zizmor"]
    assert step["run"] == "python3 scripts/ci/run_checks.py zizmor"
    step_env = step["env"]
    assert isinstance(step_env, dict)
    proc = subprocess.run(
        ["bash", "-e", "-c", str(step["run"])],
        cwd=repo,
        env=tool_env | step_env | {"FAIL_COMMAND": failure},
        capture_output=True,
        text=True,
        check=False,
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
            "./action.yml",
        ]
    ]


def test_checkout_and_python_actions_are_sha_pinned(
    workflow_steps: dict[str, dict[str, object]],
) -> None:
    assert workflow_steps["Checkout prospective merge"]["uses"] == (
        "actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd"
    )
    checkout_options = workflow_steps["Checkout prospective merge"]["with"]
    assert isinstance(checkout_options, dict)
    assert checkout_options["persist-credentials"] is False
    assert workflow_steps["Set up Python"]["uses"] == (
        "actions/setup-python@a309ff8b426b58ec0e2a45f0f869d46889d02405"
    )


@pytest.mark.parametrize("path", ["rulesync.lock", ".rulesync/rules/markdown.md"])
def test_route_changes_select_isolated_workflow_steps(
    path: str, workflow_steps: dict[str, dict[str, object]]
) -> None:
    scope = run_classifier([path])
    for name, expected in (
        ("Set up uv", True),
        ("Sync dependencies", False),
        ("Validate Python", False),
        ("Run selected tests", False),
        ("Validate chatbot routes", True),
    ):
        condition = workflow_steps[name]["if"]
        assert isinstance(condition, str), name
        selectors = []
        for clause in condition.split(" || "):
            match = re.fullmatch(r"steps\.scope\.outputs\.(\w+) == 'true'", clause)
            assert match is not None, clause
            selectors.append(match.group(1))
        assert any(scope[key] == "true" for key in selectors) is expected, name


@pytest.mark.parametrize(
    "script", ["scripts/biome.py", "scripts/tombi.py", "scripts/bootstrap.py"]
)
@pytest.mark.parametrize("changed_data", [None, "changed.json", "changed.toml"])
def test_wrapper_changes_select_node_tooling_only_for_changed_data(
    repo: Path,
    script: str,
    changed_data: str | None,
    workflow_steps: dict[str, dict[str, object]],
) -> None:
    paths = [script]
    if changed_data:
        (repo / changed_data).write_text("fixture\n", encoding="utf-8")
        paths.append(changed_data)
    scope = run_classifier(paths, repo_root=repo)

    assert scope["tests"] == scope["full_tests"] == "true"
    assert scope["python"] == scope["full_type"] == "true"
    assert scope["json"] == str(changed_data == "changed.json").lower()
    assert scope["toml"] == str(changed_data == "changed.toml").lower()
    assert workflow_steps["Install structured-data tooling"]["if"] == (
        "steps.scope.outputs.json == 'true' || steps.scope.outputs.toml == 'true'"
    )
    for name, selector in (
        ("Validate changed JSON", "json"),
        ("Validate changed TOML", "toml"),
    ):
        assert workflow_steps[name]["if"] == f"steps.scope.outputs.{selector} == 'true'"


@pytest.mark.parametrize(
    ("path", "build", "lock"),
    [
        ("scripts/ci/changed_files.py", False, False),
        ("tests/scripts/ci/test_ci_steps.py", False, False),
        ("src/hmda_reliability/logger.py", True, False),
        ("src/hmda_reliability/configs/default.yaml", True, False),
        ("pyproject.toml", True, True),
        ("uv.lock", True, True),
        (".python-version", True, True),
        ("README.md", True, False),
        ("LICENSE", True, False),
        ("inbox/note.py", False, False),
    ],
)
def test_package_and_lock_selection(
    path: str,
    build: bool,
    lock: bool,
    workflow_steps: dict[str, dict[str, object]],
) -> None:
    scope = run_classifier([path])
    assert scope["build"] == str(build).lower()
    assert scope["lock"] == str(lock).lower()
    assert workflow_steps["Verify package build"]["if"] == (
        "steps.scope.outputs.build == 'true'"
    )
    assert workflow_steps["Verify dependency lock"]["if"] == (
        "steps.scope.outputs.lock == 'true'"
    )
    if build:
        setup_condition = workflow_steps["Set up uv"]["if"]
        assert isinstance(setup_condition, str)
        assert "steps.scope.outputs.build == 'true'" in setup_condition


@pytest.mark.parametrize(
    ("json_selected", "toml_selected", "packages"),
    [
        ("true", "false", ["@biomejs/biome@2"]),
        ("false", "true", ["tombi@1"]),
        ("true", "true", ["@biomejs/biome@2", "tombi@1"]),
        ("false", "false", []),
    ],
)
@pytest.mark.parametrize("failure", ["", "npm install"])
def test_workflow_installs_only_selected_tools(
    repo: Path,
    tool_env: dict[str, str],
    workflow_steps: dict[str, dict[str, object]],
    json_selected: str,
    toml_selected: str,
    packages: list[str],
    failure: str,
) -> None:
    (repo / "scripts").symlink_to(REPO_ROOT / "scripts", target_is_directory=True)
    step = workflow_steps["Install structured-data tooling"]
    assert step["env"] == {
        "JSON": "${{ steps.scope.outputs.json }}",
        "TOML": "${{ steps.scope.outputs.toml }}",
    }
    assert step["if"] == (
        "steps.scope.outputs.json == 'true' || steps.scope.outputs.toml == 'true'"
    )
    proc = subprocess.run(
        ["bash", "-c", str(step["run"])],
        cwd=repo,
        env=tool_env
        | {"JSON": json_selected, "TOML": toml_selected, "FAIL_COMMAND": failure},
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == (17 if failure and packages else 0), proc.stderr
    assert tool_calls(tool_env) == (
        [
            [
                "npm",
                "install",
                "--prefix",
                ".local/tooling",
                "--no-save",
                "--package-lock=false",
                *packages,
            ]
        ]
        if packages
        else []
    )


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
    assert step["run"] == 'python3 scripts/ci/classify_changes.py "$GITHUB_OUTPUT"'
    assert "if" not in workflow_steps["Set up Python"]
    assert list(workflow_steps).index("Set up Python") < list(workflow_steps).index(
        "Classify changes"
    )
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
    assert scope["targets"].split() == ["tests/scripts/ci"]


def test_renamed_build_input_still_selects_package_build(
    repo: Path, tool_env: dict[str, str], workflow_steps: dict[str, dict[str, object]]
) -> None:
    commit_change(repo, {"README.md": "# Package readme\n"})
    (repo / "README.md").rename(repo / "PROJECT.md")
    commit_change(repo, {})
    (repo / "scripts").symlink_to(REPO_ROOT / "scripts", target_is_directory=True)
    output = repo / "scope-output"
    proc = subprocess.run(
        ["bash", "-c", str(workflow_steps["Classify changes"]["run"])],
        cwd=repo,
        env=tool_env | {"GITHUB_OUTPUT": str(output)},
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    scope = dict(line.split("=", 1) for line in output.read_text().splitlines())
    assert scope["build"] == "true"
    assert scope["lock"] == "false"


def test_workflow_passes_only_full_or_scoped_test_selection(
    workflow_steps: dict[str, dict[str, object]],
) -> None:
    assert workflow_steps["Run selected tests"]["env"] == {
        "FULL_TESTS": "${{ steps.scope.outputs.full_tests }}",
        "TARGETS": "${{ steps.scope.outputs.targets }}",
        "BOUNDARIES_CHECKED": "${{ steps.boundaries.outcome == 'success' }}",
    }


def test_workflow_deduplicates_only_successful_prior_checks(
    workflow_steps: dict[str, dict[str, object]],
) -> None:
    boundary = workflow_steps["Check Python dependency boundaries"]
    selected = workflow_steps["Run selected tests"]
    names = list(workflow_steps)

    assert boundary["id"] == "boundaries"
    assert selected["id"] == "selected_tests"
    assert names.index("Check Python dependency boundaries") < names.index(
        "Run selected tests"
    )
    assert "Run dependency runtime smoke" not in workflow_steps
    for step in (boundary, selected):
        assert step.get("continue-on-error", False) is False


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
    ("step_name", "check", "selector"),
    [
        ("Format changed Markdown and validate docs", "markdown", "markdown"),
        ("Validate OpenSpec", "openspec", "openspec"),
        ("Validate Python", "python", "python"),
        ("Run selected tests", "pytest", "tests"),
    ],
)
def test_workflow_calls_selected_script(
    workflow_steps: dict[str, dict[str, object]],
    step_name: str,
    check: str,
    selector: str,
) -> None:
    step = workflow_steps[step_name]

    assert step["run"] == f"python3 scripts/ci/run_checks.py {check}"
    assert step["if"] == f"steps.scope.outputs.{selector} == 'true'"
    assert (CI_SCRIPTS / "run_checks.py").is_file()


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


def test_workflow_validates_actions_with_pinned_actionlint(
    workflow_steps: dict[str, dict[str, object]],
) -> None:
    step = workflow_steps["Validate GitHub Actions with actionlint"]
    assert step["if"] == "steps.scope.outputs.actionlint == 'true'"
    assert step["run"].strip() == (
        'docker run --rm -v "$GITHUB_WORKSPACE:/repo:ro" -w /repo '
        "rhysd/actionlint:1.7.12@sha256:b1934ee5f1c509618f2508e6eb47ee0d3520686341fec936f3b79331f9315667 -color"
    )
    assert "env" not in step
    assert list(workflow_steps).index("Classify changes") < list(workflow_steps).index(
        "Validate GitHub Actions with actionlint"
    )
