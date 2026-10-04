from __future__ import annotations

import re

import pytest
import yaml

from tests.scripts.ci.helpers import REPO_ROOT, run_classifier


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
        "tests/scripts/test_tach.py",
        "tests/scripts/test_tach_config.py",
        "tests/review_ai/test_dependency_boundaries.py",
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
@pytest.mark.parametrize(
    ("script_path", "expected_target"),
    [
        (
            "scripts/agent_routes/__main__.py",
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
@pytest.mark.parametrize(
    "path",
    [
        "scripts/agent_routes/__init__.py",
        "scripts/agent_routes/__main__.py",
        "scripts/agent_routes/metadata.py",
        "scripts/agent_routes/sources.py",
        "scripts/agent_routes/indexes.py",
    ],
)
def test_route_bundle_changes_select_routes_and_focused_tests(path: str) -> None:
    out = run_classifier([path])
    assert out["routes"] == "true"
    assert out["python"] == "true"
    assert out["targets"].split() == ["tests/scripts/test_generate_agent_routes.py"]
    assert out["full_unit"] == "false"
    assert out["full_type"] == "false"
    assert "scripts/agent_routes" in out["type_targets"].split()


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
