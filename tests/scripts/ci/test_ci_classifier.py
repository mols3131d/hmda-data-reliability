"""Deterministic regression tests for CI change classification logic."""

from __future__ import annotations

import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

from tests.scripts.ci.helpers import (
    CLASSIFIER_SCRIPT,
    REPO_ROOT,
    commit_change,
    run_classifier,
    run_markdown_paths,
)


@pytest.mark.component
@pytest.mark.parametrize(
    ("path", "selected"),
    [
        (".github/workflows/ci-lite.yml", True),
        (".github/workflows/deleted.yaml", True),
        (".github/workflows/future.yaml", True),
        ("action.yml", True),
        ("action.yaml", True),
        (".github/actions/example/action.yml", True),
        ("nested/local/action.yaml", True),
        ("tools/deleted/action.yaml", True),
        ("scripts/ci/classify_changes.py", False),
        (".github/workflows/classify_changes.sh", False),
        ("src/hmda_reliability/example.py", False),
        ("README.md", False),
        ("inbox/example/action.yml", False),
        ("tools/action.yaml.txt", False),
    ],
)
def test_actions_definitions_select_linters_even_when_deleted(
    path: str, selected: bool
) -> None:
    scope = run_classifier([path])
    for flag in ("zizmor", "actionlint"):
        assert scope[flag] == str(selected).lower(), flag


@pytest.mark.component
@pytest.mark.parametrize("input_kind", ["readme", "module", "resource"])
def test_packaging_inputs_select_build(input_kind: str) -> None:
    with (REPO_ROOT / "pyproject.toml").open("rb") as source:
        config = tomllib.load(source)
    if input_kind == "readme":
        path = config["project"]["readme"]
    else:
        backend = config["tool"]["uv"]["build-backend"]
        module = backend["module-name"].replace(".", "/")
        filename = "__init__.py" if input_kind == "module" else "data/probe.bin"
        path = f"{backend.get('module-root', 'src')}/{module}/{filename}"

    assert run_classifier([path])["build"] == "true", path


@pytest.mark.component
def test_git_path_line_breaks_fail_before_actions_outputs(repo: Path) -> None:
    commit_change(repo, {"tests/test_probe\npython=false\ntests=false\nunused=.py": ""})
    output = repo / "scope-output"
    proc = subprocess.run(
        [sys.executable, str(CLASSIFIER_SCRIPT), str(output)],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 1
    assert "unsupported line breaks" in proc.stderr
    assert not output.exists()


@pytest.mark.component
@pytest.mark.parametrize(
    "path",
    [
        "tests/scripts/ci/test_ci_classifier.py",
        "tests/scripts/ci/test_new_contract.py",
    ],
)
def test_script_test_modify(path: str) -> None:
    """CI 테스트 변경은 파일별 매핑 없이 CI 계약 suite를 선택한다."""
    out = run_classifier([path])
    assert out["tests"] == "true"
    assert out["full_tests"] == "false"
    assert out["targets"].split() == ["tests/scripts/ci"]
    assert out["python"] == "true"
    assert out["full_type"] == "false"


@pytest.mark.component
@pytest.mark.parametrize(
    "path",
    [
        ".github/workflows/ci-lite.yml",
        "scripts/ci/classify_changes.py",
        "scripts/ci/future-helper.py",
    ],
)
def test_ci_changes_select_contract_tests_without_domain_validation(path: str) -> None:
    out = run_classifier([path])

    assert out["targets"].split() == ["tests/scripts/ci"]
    assert out["tests"] == "true"
    assert out["python"] == ("true" if path.endswith(".py") else "false")
    for flag in ("tach", "full_tests", "full_type"):
        assert out[flag] == "false", flag


@pytest.mark.component
@pytest.mark.parametrize(
    "path",
    [
        "scripts/ci/run_checks.py",
        "tests/scripts/ci/test_ci_classifier.py",
        "tests/scripts/ci/helpers.py",
    ],
)
def test_ci_and_dependency_changes_preserve_component_contract_targets(
    path: str,
) -> None:
    out = run_classifier(["uv.lock", path])

    assert out["full_tests"] == "true"
    assert out["tach"] == "true"
    assert out["targets"].split() == ["tests/scripts/ci"]
    assert "ci_targets" not in out
    assert "full_unit" not in out


@pytest.mark.component
@pytest.mark.parametrize(
    "path",
    [
        "tests/scripts/__init__.py",
        "tests/scripts/ci/__init__.py",
        "tests/scripts/ci/conftest.py",
        "tests/scripts/ci/helpers.py",
    ],
)
def test_ci_support_changes_select_all_contracts(path: str) -> None:
    out = run_classifier([path])

    assert out["targets"].split() == [
        "tests/scripts" if path == "tests/scripts/__init__.py" else "tests/scripts/ci"
    ]
    assert out["tests"] == "true"
    assert out["python"] == "true"
    for flag in ("tach", "full_tests", "full_type"):
        assert out[flag] == "false", flag


@pytest.mark.component
def test_deleted_ci_test_still_selects_remaining_contracts() -> None:
    out = run_classifier(["tests/scripts/ci/test_nonexistent_deleted.py"])

    assert out["tests"] == "true"
    assert out["targets"] == "tests/scripts/ci"
    assert out["full_tests"] == "false"
    assert out["full_type"] == "false"


@pytest.mark.component
@pytest.mark.parametrize("directory", ["scripts/ci", "data_platform"])
def test_missing_test_directory_broadens_to_full_validation(
    repo: Path, directory: str
) -> None:
    out = run_classifier([f"tests/{directory}/test_deleted.py"], repo_root=repo)

    assert out["tests"] == out["full_tests"] == "true"
    assert out["python"] == out["full_type"] == "true"
    assert out["targets"] == ""


@pytest.mark.component
@pytest.mark.parametrize("args", [[], ["--markdown-paths"]])
def test_git_comparison_failure_is_not_success(tmp_path: Path, args: list[str]) -> None:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    proc = subprocess.run(
        [sys.executable, str(CLASSIFIER_SCRIPT), *args],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode != 0
    assert "tests=false" not in proc.stdout


@pytest.mark.component
def test_root_test_delete() -> None:
    """루트 테스트 변경은 남아 있는 전체 suite를 검사한다."""
    out = run_classifier(["tests/test_nonexistent_deleted.py"])
    assert out["tests"] == "true"
    assert out["full_tests"] == "true"
    assert out["targets"].strip() == ""
    assert out["python"] == "true"
    assert out["full_type"] == "true"
    assert out["type_targets"].strip() == ""


@pytest.mark.component
def test_script_test_rename() -> None:
    """테스트 rename은 이전과 신규 디렉터리의 계약을 모두 선택한다."""
    path = "tests/scripts/ci/test_ci_classifier.py"
    out = run_classifier(["tests/scripts/test_ci_classifier.py", path])
    assert out["tests"] == "true"
    assert out["full_tests"] == "false"
    assert out["targets"].split() == ["tests/scripts", "tests/scripts/ci"]
    assert out["full_type"] == "false"


@pytest.mark.component
def test_script_test_modify_targets_script_suite() -> None:
    """scripts 전용 테스트 수정은 scripts 디렉터리 계약을 선택한다."""
    path = "tests/scripts/test_commands.py"
    out = run_classifier([path])
    assert out["tests"] == "true"
    assert out["full_tests"] == "false"
    assert out["targets"].strip() == "tests/scripts"
    assert out["python"] == "true"
    assert out["full_type"] == "false"


@pytest.mark.component
@pytest.mark.parametrize(
    "path",
    [
        "README.md",
        "docs/development/ci/README.md",
    ],
)
def test_changed_markdown_paths_are_selected(path: str) -> None:
    """현재 change set의 Markdown만 lightweight 검증 대상으로 선택한다."""
    out = run_classifier([path])
    assert out["markdown"] == "true"
    assert run_markdown_paths([path]) == [path]


@pytest.mark.component
def test_markdown_path_selection_stays_within_changed_scope() -> None:
    """Mixed Markdown에서도 입력된 changed path만 workflow에 전달한다."""
    paths = [
        "inbox/2026-09-04/07-12-guide-orchestration-sandbox-dag-testing.md",
        "docs/development/ci/README.md",
        "inbox/AGENTS.md",
    ]
    assert run_markdown_paths(paths) == ["docs/development/ci/README.md"]


@pytest.mark.component
@pytest.mark.parametrize("suffix", ["md", "json", "jsonc", "toml", "py", "yml"])
def test_inbox_only_changes_select_no_validation(repo: Path, suffix: str) -> None:
    path = f"inbox/nested/note.{suffix}"
    target = repo / path
    target.parent.mkdir(parents=True)
    target.write_text("fixture\n")
    out = run_classifier([path], repo_root=repo)
    assert all(value == "false" or not value for value in out.values())


@pytest.mark.component
def test_inbox_deleted_and_renamed_paths_do_not_hide_other_changes() -> None:
    out = run_classifier(
        ["inbox/deleted.py", "inbox/renamed.json", "scripts/ci/markdown.py"]
    )
    assert out == run_classifier(["scripts/ci/markdown.py"])


@pytest.mark.component
@pytest.mark.parametrize(
    "route_path",
    [
        ".agents/route/skills.jsonl",
        ".agents/route/rules.jsonl",
        "rulesync.jsonc",
        "rulesync.lock",
        "skills-lock.json",
        ".rulesync/rules/markdown.md",
        ".rulesync/skills/mols-loops/SKILL.md",
    ],
)
def test_route_only_change_isolates_heavy_execution(route_path: str) -> None:
    """라우트 관련 변경 시 라우트 검증만 활성화되고 무거운 단계는 제외된다."""
    out = run_classifier([route_path])
    assert out["routes"] == "true"
    assert out["tests"] == "false"
    assert out["python"] == "false"
    assert out["full_tests"] == "false"
    assert out["full_type"] == "false"
    assert out["targets"].strip() == ""
    assert out["type_targets"].strip() == ""


@pytest.mark.component
def test_workflow_change_targets_classifier_test() -> None:
    """CI 워크플로 파일 변경 시 classifier 자체의 회귀 테스트가 실행된다."""
    out = run_classifier([".github/workflows/ci-lite.yml"])
    assert out["tests"] == "true"
    assert "tests/scripts/ci" in out["targets"].split()
