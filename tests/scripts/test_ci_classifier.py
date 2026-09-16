"""Deterministic regression tests for CI change classification logic."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
CLASSIFIER_SCRIPT = REPO_ROOT / ".github" / "workflows" / "classify_changes.sh"


def run_classifier(paths: list[str], *, cwd: Path = REPO_ROOT) -> dict[str, str]:
    """Execute the classifier script against the provided paths via stdin."""
    proc = subprocess.run(
        ["bash", str(CLASSIFIER_SCRIPT), "--stdin"],
        input="\n".join(paths) + "\n",
        capture_output=True,
        text=True,
        check=True,
        cwd=cwd,
    )
    result: dict[str, str] = {}
    for line in proc.stdout.splitlines():
        if "=" in line:
            key, val = line.split("=", 1)
            result[key.strip()] = val.strip()
    return result


@pytest.fixture
def active_change_project(tmp_path: Path) -> Path:
    """실제 Change의 archive lifecycle과 독립적인 active pairing fixture."""
    (tmp_path / "openspec/specs/orchestration-pipeline").mkdir(parents=True)
    (
        tmp_path
        / "openspec/changes/orchestration-quality-gate/specs/orchestration-pipeline"
    ).mkdir(parents=True)
    return tmp_path


def run_markdown_paths(paths: list[str]) -> list[str]:
    """Return changed Markdown paths selected for validation."""
    proc = subprocess.run(
        ["bash", str(CLASSIFIER_SCRIPT), "--stdin", "--markdown-paths"],
        input="\n".join(paths) + "\n",
        capture_output=True,
        text=True,
        check=True,
        cwd=REPO_ROOT,
    )
    return proc.stdout.splitlines()


@pytest.mark.unit
def test_script_test_modify() -> None:
    """존재하는 scripts 테스트 파일 수정 시 해당 테스트만 targets에 추가된다."""
    path = "tests/scripts/test_ci_classifier.py"
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
        "tach.toml",
        "src/hmda_reliability/logger.py",
        "src/hmda_reliability/reliability/deleted.py",
        "src/new_package/module.py",
        ".python-version",
        "pyproject.toml",
        "uv.lock",
        ".github/workflows/ci-lite.yml",
        ".github/workflows/classify_changes.sh",
        "tests/scripts/test_tach.py",
        "tests/scripts/test_tach_config.py",
    ],
)
def test_architecture_changes_prepare_and_run_boundary_check(path: str) -> None:
    out = run_classifier([path])
    assert out["tach"] == "true"
    workflow = yaml.safe_load(
        (REPO_ROOT / ".github/workflows/ci-lite.yml").read_text(encoding="utf-8")
    )
    steps = {step["name"]: step for step in workflow["jobs"]["check"]["steps"]}
    for name in (
        "Set up Python",
        "Set up uv",
        "Sync dependencies",
        "Check Python dependency boundaries",
    ):
        # 실제 workflow의 OR selector를 확인해 setup 누락도 회귀로 잡는다.
        conditions = steps[name]["if"].split(" || ")
        keys = []
        for condition in conditions:
            match = re.fullmatch(r"steps\.scope\.outputs\.(\w+) == 'true'", condition)
            assert match is not None, condition
            keys.append(match.group(1))
        assert any(out[key] == "true" for key in keys), name
    assert "uv sync --locked" in steps["Sync dependencies"]["run"]
    assert (
        "uv run --no-sync tach check"
        in steps["Check Python dependency boundaries"]["run"]
    )


@pytest.mark.unit
@pytest.mark.parametrize(
    "path", ["README.md", "dbt/models/example.sql", "lefthook.yml"]
)
def test_unrelated_changes_do_not_select_architecture(path: str) -> None:
    assert run_classifier([path])["tach"] == "false"


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
    path = "tests/scripts/test_ci_classifier.py"
    out = run_classifier(["tests/test_nonexistent_old.py", path])
    assert out["tests"] == "true"
    assert out["full_unit"] == "false"
    assert out["targets"].strip() == path
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
        "docs/development/ci.md",
        "inbox/AGENTS.md",
        "inbox/_guidelines/research.md",
        "inbox/_templates/research.md",
        "inbox/README.md",
        "inbox/2026-09-04/07-12-guide-orchestration-sandbox-dag-testing.md",
    ],
)
def test_changed_markdown_paths_are_selected(path: str) -> None:
    """현재 change set의 Markdown만 lightweight 검증 대상으로 선택한다."""
    out = run_classifier([path])
    assert out["markdown"] == "true"
    assert out["inbox"] == str(path.startswith("inbox/")).lower()
    assert run_markdown_paths([path]) == [path]


@pytest.mark.unit
def test_markdown_path_selection_stays_within_changed_scope() -> None:
    """Mixed Markdown에서도 입력된 changed path만 workflow에 전달한다."""
    paths = [
        "inbox/2026-09-04/07-12-guide-orchestration-sandbox-dag-testing.md",
        "docs/development/ci.md",
        "inbox/AGENTS.md",
    ]
    assert run_markdown_paths(paths) == paths


@pytest.mark.unit
@pytest.mark.parametrize(
    ("script_path", "expected_target"),
    [
        (
            "scripts/generate_agent_routes.py",
            "tests/scripts/test_generate_agent_routes.py",
        ),
        ("scripts/agent_assets.py", "tests/scripts/test_agent_assets.py"),
        (
            "scripts/generate_docs_indexes.py",
            "tests/scripts/test_generate_docs_indexes.py",
        ),
        (
            "scripts/validate_inbox_artifacts.py",
            "tests/scripts/test_validate_inbox_artifacts.py",
        ),
        ("scripts/log_agent_event.py", "tests/scripts/test_log_agent_event.py"),
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
def test_shared_commands_expands_known_consumers() -> None:
    """공용 command helper는 wrapper consumer와 계약 테스트를 함께 검증한다."""
    out = run_classifier(["scripts/_commands.py"])
    assert out["tests"] == "true"
    assert out["full_unit"] == "false"
    assert out["full_type"] == "false"

    targets = set(out["targets"].split())
    assert targets == {
        "tests/scripts/test_commands.py",
        "tests/scripts/test_tool_wrappers.py",
        "tests/scripts/test_bootstrap.py",
        "tests/scripts/test_agent_assets.py",
    }

    type_targets = set(out["type_targets"].split())
    assert "scripts" in type_targets
    assert targets <= type_targets


@pytest.mark.unit
def test_bootstrap_maps_to_bootstrap_contract_test() -> None:
    """Bootstrap 수정은 bootstrap workflow contract test를 직접 실행한다."""
    out = run_classifier(["scripts/bootstrap.py"])
    assert out["tests"] == "true"
    assert out["full_unit"] == "false"
    assert out["full_type"] == "false"
    assert out["targets"].strip() == "tests/scripts/test_bootstrap.py"
    assert out["type_targets"].strip() == "tests/scripts/test_bootstrap.py"


@pytest.mark.unit
@pytest.mark.parametrize("script_path", ["scripts/biome.py", "scripts/tombi.py"])
def test_node_tool_wrapper_maps_to_forwarding_contract_test(script_path: str) -> None:
    """Biome/Tombi wrapper 수정은 실제 CLI forwarding contract를 검증한다."""
    out = run_classifier([script_path])
    assert out["tests"] == "true"
    assert out["full_unit"] == "false"
    assert out["full_type"] == "false"
    assert out["targets"].strip() == "tests/scripts/test_tool_wrappers.py"
    assert out["type_targets"].strip() == "tests/scripts/test_tool_wrappers.py"


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
    out = run_classifier(["src/hmda_reliability/reliability/recovery/executor.py"])

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
    assert "tests/scripts/test_ci_classifier.py" in out["targets"]


@pytest.mark.unit
@pytest.mark.parametrize(
    ("spec_path", "expected_targets"),
    [
        (
            "openspec/specs/data-platform-dbt-analytics/spec.md",
            {"tests/dbt"},
        ),
        (
            "openspec/specs/orchestration-pipeline/spec.md",
            {
                "tests/orchestration",
                "tests/data_operations/test_quality_gate.py",
                "tests/data_operations/test_dbt_runner.py",
                "tests/reliability/test_quality_gate.py",
            },
        ),
        (
            "openspec/specs/reliability-agentic-review/spec.md",
            {"tests/review_ai", "tests/runtime_ai"},
        ),
    ],
)
def test_canonical_openspec_changes_select_executable_targets(
    spec_path: str,
    expected_targets: set[str],
) -> None:
    """Canonical Spec 변경은 구조 검증과 대응 executable test를 함께 선택한다."""
    out = run_classifier([spec_path])

    assert out["openspec"] == "true"
    assert out["openspec_bulk"] == "false"
    assert out["tests"] == "true"
    assert out["full_tests"] == "false"
    assert set(out["targets"].split()) == expected_targets


@pytest.mark.unit
def test_unknown_canonical_openspec_change_fails_safe_to_full_tests() -> None:
    """알 수 없는 신규 Spec capability는 executable validation을 생략하지 않는다."""
    out = run_classifier(["openspec/specs/new-capability/spec.md"])

    assert out["openspec"] == "true"
    assert out["openspec_bulk"] == "true"
    assert out["tests"] == "true"
    assert out["full_tests"] == "true"
    assert out["full_unit"] == "true"
    assert out["full_type"] == "true"


@pytest.mark.unit
def test_active_openspec_change_uses_affected_validation_target(
    active_change_project: Path,
) -> None:
    """Active Change 변경은 해당 Change만 OpenSpec validation 대상으로 선택한다."""
    out = run_classifier(
        ["openspec/changes/orchestration-quality-gate/proposal.md"],
        cwd=active_change_project,
    )

    assert out["openspec"] == "true"
    assert out["openspec_bulk"] == "false"
    assert out["openspec_change_targets"].strip() == "orchestration-quality-gate"
    assert out["tests"] == "false"


@pytest.mark.unit
def test_archived_openspec_change_requests_archived_validation() -> None:
    """Archive 변경은 전체 active item 대신 archived validation을 선택한다."""
    out = run_classifier(
        [
            "openspec/changes/archive/2026-08-26-orchestration-pipeline-migrate-airflow/tasks.md"
        ]
    )

    assert out["openspec"] == "true"
    assert out["openspec_archived"] == "true"
    assert out["openspec_bulk"] == "false"
    assert out["openspec_change_targets"].strip() == ""
    assert out["tests"] == "false"


@pytest.mark.unit
def test_openspec_configuration_change_uses_bulk_validation() -> None:
    """OpenSpec configuration 변경은 bulk validation을 사용한다."""
    out = run_classifier(["openspec/config.yaml"])

    assert out["openspec"] == "true"
    assert out["openspec_bulk"] == "true"
    assert out["openspec_spec_targets"].strip() == ""
    assert out["openspec_change_targets"].strip() == ""


@pytest.mark.unit
@pytest.mark.parametrize(
    "dependency_path", [".python-version", "pyproject.toml", "uv.lock"]
)
def test_dependency_changes_request_runtime_boundary_smoke(
    dependency_path: str,
) -> None:
    """Dependency 변경은 unit/type과 함께 dbt/Airflow runtime smoke를 선택한다."""
    out = run_classifier([dependency_path])

    assert out["python"] == "true"
    assert out["tests"] == "true"
    assert out["runtime_smoke"] == "true"
    assert out["full_unit"] == "true"
    assert out["full_type"] == "true"
    assert out["tach"] == "true"


@pytest.mark.unit
@pytest.mark.parametrize(
    "path",
    [
        "tach.toml",
        "src/hmda_reliability/__init__.py",
        "src/hmda_reliability/reliability/evaluation/volume_drop.py",
    ],
)
def test_tach_boundary_changes_request_architecture_check(path: str) -> None:
    """Tach config와 모든 source-depth의 Python 변경은 boundary check를 선택한다."""
    out = run_classifier([path])

    assert out["tach"] == "true"


@pytest.mark.unit
def test_tach_only_change_runs_dependency_setup_without_python_suite() -> None:
    """tach.toml 단독 변경도 dependency setup과 Tach check를 활성화한다."""
    out = run_classifier(["tach.toml"])

    assert out["tach"] == "true"
    assert out["toml"] == "true"
    assert out["python"] == "false"
    assert out["tests"] == "false"


@pytest.mark.unit
def test_canonical_spec_selects_direct_active_change_validation(
    active_change_project: Path,
) -> None:
    """Canonical Spec 변경은 같은 capability의 active Change도 검증한다."""
    out = run_classifier(
        ["openspec/specs/orchestration-pipeline/spec.md"], cwd=active_change_project
    )

    assert out["openspec_spec_targets"].strip() == "orchestration-pipeline"
    assert out["openspec_change_targets"].strip() == "orchestration-quality-gate"


@pytest.mark.unit
def test_canonical_spec_without_active_delta_keeps_change_targets_empty() -> None:
    """직접 연결된 active Change가 없으면 affected Spec만 유지한다."""
    out = run_classifier(["openspec/specs/reliability-data-contracts/spec.md"])

    assert out["openspec_spec_targets"].strip() == "reliability-data-contracts"
    assert out["openspec_change_targets"].strip() == ""


@pytest.mark.unit
def test_mixed_canonical_spec_and_active_change_preserves_both_targets(
    active_change_project: Path,
) -> None:
    """같은 change set의 Spec와 active Change target을 모두 중복 없이 보존한다."""
    out = run_classifier(
        [
            "openspec/specs/orchestration-pipeline/spec.md",
            "openspec/changes/orchestration-quality-gate/proposal.md",
        ],
        cwd=active_change_project,
    )

    assert out["openspec_spec_targets"].strip() == "orchestration-pipeline"
    assert out["openspec_change_targets"].strip() == "orchestration-quality-gate"
