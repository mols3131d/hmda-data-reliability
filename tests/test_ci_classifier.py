"""Deterministic regression tests for CI change classification logic."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
CLASSIFIER_SCRIPT = REPO_ROOT / ".github" / "workflows" / "classify_changes.sh"


def run_classifier(paths: list[str]) -> dict[str, str]:
    """Execute the classifier script against the provided paths via stdin."""
    proc = subprocess.run(
        ["bash", str(CLASSIFIER_SCRIPT), "--stdin"],
        input="\n".join(paths) + "\n",
        capture_output=True,
        text=True,
        check=True,
        cwd=REPO_ROOT,
    )
    result: dict[str, str] = {}
    for line in proc.stdout.splitlines():
        if "=" in line:
            key, val = line.split("=", 1)
            result[key.strip()] = val.strip()
    return result


@pytest.mark.unit
def test_root_test_modify() -> None:
    """존재하는 루트 테스트 파일 수정 시 해당 테스트만 targets에 추가된다."""
    out = run_classifier(["tests/test_commands.py"])
    assert out["tests"] == "true"
    assert out["full_unit"] == "false"
    assert out["targets"].strip() == "tests/test_commands.py"
    assert out["python"] == "true"
    assert out["full_type"] == "false"


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
def test_root_test_rename() -> None:
    """루트 테스트 이름 변경 시 존재하는 신규 파일만 targets에 추가된다."""
    out = run_classifier(["tests/test_nonexistent_old.py", "tests/test_commands.py"])
    assert out["tests"] == "true"
    assert out["full_unit"] == "false"
    assert out["targets"].strip() == "tests/test_commands.py"
    assert out["full_type"] == "false"


@pytest.mark.unit
@pytest.mark.parametrize(
    ("script_path", "expected_target"),
    [
        ("scripts/generate_agent_routes.py", "tests/test_generate_agent_routes.py"),
        ("scripts/agent_assets.py", "tests/test_agent_assets.py"),
        ("scripts/_commands.py", "tests/test_commands.py"),
        ("scripts/bootstrap.py", "tests/test_commands.py"),
        ("scripts/biome.py", "tests/test_commands.py"),
        ("scripts/tombi.py", "tests/test_commands.py"),
        ("scripts/generate_docs_indexes.py", "tests/test_generate_docs_indexes.py"),
        ("scripts/log_agent_event.py", "tests/test_log_agent_event.py"),
        ("scripts/run_actual_source.py", "tests/hmda_data/eda/test_eda_evidence.py"),
        ("scripts/run_agentic_review_live.py", "tests/review_ai/test_live_harness.py"),
    ],
)
def test_explicitly_mapped_scripts(script_path: str, expected_target: str) -> None:
    """명시적으로 매핑된 운영 스크립트는 대응 테스트까지 검증한다."""
    out = run_classifier([script_path])
    assert out["tests"] == "true"
    assert out["full_unit"] == "false"
    assert out["targets"].strip() == expected_target
    assert out["full_type"] == "false"
    assert expected_target in out["type_targets"]


@pytest.mark.unit
def test_unmapped_script_triggers_full_fallback() -> None:
    """미매핑 scripts/*.py 수정은 unit과 type 검증을 모두 넓힌다."""
    out = run_classifier(["scripts/unmapped_new_script.py"])
    assert out["tests"] == "true"
    assert out["full_unit"] == "true"
    assert out["full_type"] == "true"
    assert out["targets"].strip() == ""


@pytest.mark.unit
def test_source_domain_type_targets_include_reverse_consumers() -> None:
    """Domain source 수정은 own 및 reverse consumer의 source와 test를 type-check한다."""
    out = run_classifier(
        ["src/hmda_reliability/reliability/recovery/executor.py"]
    )

    assert out["python"] == "true"
    assert out["full_type"] == "false"

    type_targets = set(out["type_targets"].split())
    assert type_targets == {
        "src/hmda_reliability/reliability",
        "tests/reliability",
        "src/hmda_reliability/review_ai",
        "tests/review_ai",
        "src/hmda_reliability/data_operations",
        "tests/data_operations",
        "src/hmda_reliability/orchestration",
        "tests/orchestration",
    }


@pytest.mark.unit
def test_shared_source_triggers_full_type_fallback() -> None:
    """Shared source는 project-wide type check로 fallback한다."""
    out = run_classifier(["src/hmda_reliability/shared/example.py"])
    assert out["python"] == "true"
    assert out["full_unit"] == "true"
    assert out["full_type"] == "true"


@pytest.mark.unit
def test_runtime_config_triggers_full_type_fallback() -> None:
    """Python runtime config 변경은 project-wide type check로 fallback한다."""
    out = run_classifier(["pyproject.toml"])
    assert out["python"] == "true"
    assert out["full_unit"] == "true"
    assert out["full_type"] == "true"


@pytest.mark.unit
def test_unknown_python_path_triggers_full_type_fallback() -> None:
    """분류되지 않은 Python path는 type validation을 silent skip하지 않는다."""
    out = run_classifier(["tools/example.py"])
    assert out["python"] == "true"
    assert out["full_type"] == "true"


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
        ".rulesync/skills/mols-rpi/SKILL.md",
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
    assert "tests/test_ci_classifier.py" in out["targets"]
