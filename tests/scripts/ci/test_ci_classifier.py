"""Deterministic regression tests for CI change classification logic."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from tests.scripts.ci.helpers import (
    CLASSIFIER_SCRIPT,
    run_classifier,
    run_markdown_paths,
)


@pytest.mark.unit
@pytest.mark.parametrize(
    ("path", "expected_ci_targets"),
    [
        (
            "tests/scripts/ci/test_ci_classifier.py",
            "tests/scripts/ci/test_ci_classifier.py",
        ),
        ("tests/scripts/ci/test_ci_classifier_openspec.py", ""),
        ("tests/scripts/ci/test_ci_classifier_python.py", ""),
        (
            "tests/scripts/ci/test_ci_steps.py",
            "tests/scripts/ci/test_ci_steps.py",
        ),
        (
            "tests/scripts/ci/test_ci_pytest.py",
            "tests/scripts/ci/test_ci_pytest.py",
        ),
        (
            "tests/scripts/ci/test_ci_workflow.py",
            "tests/scripts/ci/test_ci_workflow.py",
        ),
    ],
)
def test_script_test_modify(path: str, expected_ci_targets: str) -> None:
    """존재하는 scripts 테스트 파일 수정 시 해당 테스트만 targets에 추가된다."""
    out = run_classifier([path])
    assert out["tests"] == "true"
    assert out["full_unit"] == "false"
    assert out["targets"].strip() == path
    assert out["ci_targets"].strip() == expected_ci_targets
    assert out["python"] == "true"
    assert out["full_type"] == "false"


@pytest.mark.unit
@pytest.mark.parametrize(
    "path",
    [
        ".github/workflows/ci-lite.yml",
        "scripts/ci/classify_changes.sh",
        "scripts/ci/classify_openspec.sh",
        "scripts/ci/markdown.sh",
        "scripts/ci/changed_files.sh",
        "scripts/ci/future-helper.sh",
    ],
)
def test_ci_changes_select_contract_tests_without_domain_validation(path: str) -> None:
    out = run_classifier([path])

    assert out["targets"].split() == ["tests/scripts/ci"]
    assert set(out["ci_targets"].split()) == set(out["targets"].split())
    assert out["tests"] == "true"
    for flag in ("tach", "python", "runtime_smoke", "full_unit", "full_type"):
        assert out[flag] == "false", flag


@pytest.mark.unit
@pytest.mark.parametrize(
    ("path", "expected"),
    [
        (
            "scripts/ci/pytest.sh",
            {"tests/scripts/ci"},
        ),
        (
            "tests/scripts/ci/test_ci_classifier.py",
            {"tests/scripts/ci/test_ci_classifier.py"},
        ),
        (
            "tests/scripts/ci/test_ci_classifier_openspec.py",
            set(),
        ),
        (
            "tests/scripts/ci/test_ci_classifier_python.py",
            set(),
        ),
        (
            "tests/scripts/ci/test_ci_steps.py",
            {"tests/scripts/ci/test_ci_steps.py"},
        ),
        (
            "tests/scripts/ci/test_ci_pytest.py",
            {"tests/scripts/ci/test_ci_pytest.py"},
        ),
        (
            "tests/scripts/ci/test_ci_workflow.py",
            {"tests/scripts/ci/test_ci_workflow.py"},
        ),
        ("tests/scripts/ci/helpers.py", {"tests/scripts/ci"}),
    ],
)
def test_ci_and_dependency_changes_preserve_component_contract_targets(
    path: str, expected: set[str]
) -> None:
    out = run_classifier(["uv.lock", path])

    assert out["full_unit"] == "true"
    assert out["tach"] == "true"
    assert out["runtime_smoke"] == "true"
    assert set(out["ci_targets"].split()) == expected


@pytest.mark.unit
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

    assert out["targets"].split() == ["tests/scripts/ci"]
    assert out["ci_targets"].split() == ["tests/scripts/ci"]
    assert out["tests"] == "true"
    assert out["python"] == "true"
    for flag in ("tach", "runtime_smoke", "full_unit", "full_type"):
        assert out[flag] == "false", flag


@pytest.mark.unit
def test_deleted_ci_test_is_not_selected() -> None:
    out = run_classifier(["tests/scripts/ci/test_nonexistent_deleted.py"])

    assert out["tests"] == "false"
    assert out["targets"] == ""
    assert out["ci_targets"] == ""
    assert out["full_unit"] == "false"
    assert out["full_type"] == "false"


@pytest.mark.component
@pytest.mark.parametrize("args", [[], ["--markdown-paths"]])
def test_git_comparison_failure_is_not_success(tmp_path: Path, args: list[str]) -> None:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    proc = subprocess.run(
        ["bash", str(CLASSIFIER_SCRIPT), *args],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode != 0
    assert "tests=false" not in proc.stdout


@pytest.mark.unit
def test_root_test_delete() -> None:
    """삭제된 루트 테스트 파일은 디스크에 없으므로 targets에서 제외된다."""
    out = run_classifier(["tests/test_nonexistent_deleted.py"])
    assert out["tests"] == "false"
    assert out["full_unit"] == "false"
    assert out["targets"].strip() == ""
    assert out["python"] == "true"
    assert out["full_type"] == "false"
    assert out["type_targets"].strip() == ""


@pytest.mark.unit
def test_script_test_rename() -> None:
    """scripts 테스트 이름 변경 시 존재하는 신규 파일만 targets에 추가된다."""
    path = "tests/scripts/ci/test_ci_classifier.py"
    out = run_classifier(["tests/scripts/test_ci_classifier.py", path])
    assert out["tests"] == "true"
    assert out["full_unit"] == "false"
    assert out["targets"].strip() == path
    assert out["ci_targets"].strip() == path
    assert out["full_type"] == "false"


@pytest.mark.unit
def test_script_test_modify_targets_only_changed_test() -> None:
    """scripts 전용 테스트 수정은 해당 테스트만 실행 대상으로 선택한다."""
    path = "tests/scripts/test_commands.py"
    out = run_classifier([path])
    assert out["tests"] == "true"
    assert out["full_unit"] == "false"
    assert out["targets"].strip() == path
    assert out["python"] == "true"
    assert out["full_type"] == "false"


@pytest.mark.unit
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


@pytest.mark.unit
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


@pytest.mark.unit
def test_inbox_deleted_and_renamed_paths_do_not_hide_other_changes() -> None:
    out = run_classifier(
        ["inbox/deleted.py", "inbox/renamed.json", "scripts/ci/markdown.sh"]
    )
    assert out == run_classifier(["scripts/ci/markdown.sh"])


@pytest.mark.unit
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
    assert out["full_unit"] == "false"
    assert out["full_type"] == "false"
    assert out["targets"].strip() == ""
    assert out["type_targets"].strip() == ""

    # ci-lite.yml 스텝 실행 조건 대조 검증:
    step_sync_dependencies = (out["tests"] == "true") or (out["python"] == "true")
    step_validate_python = out["python"] == "true"
    step_run_tests = out["tests"] == "true"
    step_validate_routes = out["routes"] == "true"

    assert not step_sync_dependencies, "전체 의존성 동기화가 실행되면 안 됨"
    assert not step_validate_python, "Python 검증이 실행되면 안 됨"
    assert not step_run_tests, "단위 테스트가 실행되면 안 됨"
    assert step_validate_routes, "챗봇 라우트 격리 검증은 반드시 실행되어야 함"


@pytest.mark.unit
def test_workflow_change_targets_classifier_test() -> None:
    """CI 워크플로 파일 변경 시 classifier 자체의 회귀 테스트가 실행된다."""
    out = run_classifier([".github/workflows/ci-lite.yml"])
    assert out["tests"] == "true"
    assert "tests/scripts/ci" in out["targets"].split()
