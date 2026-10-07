from __future__ import annotations

import re

import pytest
import yaml

from tests.scripts.ci.helpers import REPO_ROOT, run_classifier


@pytest.mark.component
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
        if name == "Set up Python":
            assert "if" not in steps[name]
            continue
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


@pytest.mark.component
@pytest.mark.parametrize(
    "path", ["README.md", "dbt/models/example.sql", "lefthook.yml"]
)
def test_unrelated_changes_do_not_select_architecture(path: str) -> None:
    assert run_classifier([path])["tach"] == "false"


@pytest.mark.component
@pytest.mark.parametrize(
    "script_path",
    [
        "scripts/agent_routes/__main__.py",
        "scripts/agent_assets.py",
        "scripts/new_helper.py",
        "scripts/renamed_entrypoint.py",
    ],
)
def test_scripts_select_full_validation_without_name_exceptions(
    script_path: str,
) -> None:
    """CI 밖 script는 이름에 관계없이 전체 실행 검사를 선택한다."""
    out = run_classifier([script_path])
    assert (
        out["tests"] == out["full_tests"] == out["python"] == out["full_type"] == "true"
    )
    assert out["targets"] == out["type_targets"] == ""


@pytest.mark.component
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
def test_route_bundle_changes_select_routes_and_full_tests(path: str) -> None:
    out = run_classifier([path])
    assert out["routes"] == "true"
    assert out["python"] == "true"
    assert out["targets"] == ""
    assert out["full_tests"] == "true"
    assert out["full_type"] == "true"


@pytest.mark.component
def test_shared_commands_selects_full_validation() -> None:
    """공용 helper의 consumer 목록을 유지하지 않고 전체 검사를 선택한다."""
    out = run_classifier(["scripts/_commands.py"])
    assert out["tests"] == "true"
    assert out["full_tests"] == "true"
    assert out["full_type"] == "true"
    assert out["targets"] == ""


@pytest.mark.component
def test_bootstrap_selects_full_validation_without_node_tooling() -> None:
    out = run_classifier(["scripts/bootstrap.py"])
    assert out["tests"] == "true"
    assert out["full_tests"] == "true"
    assert out["full_type"] == "true"
    assert out["targets"] == ""
    assert out["json"] == out["toml"] == "false"


@pytest.mark.component
@pytest.mark.parametrize("script_path", ["scripts/biome.py", "scripts/tombi.py"])
def test_node_tool_wrapper_selects_script_contracts(script_path: str) -> None:
    """Biome/Tombi wrapper 수정은 실제 CLI forwarding contract를 검증한다."""
    out = run_classifier([script_path])
    assert out["tests"] == "true"
    assert out["full_tests"] == "true"
    assert out["full_type"] == "true"
    assert out["targets"] == ""
    assert out["json"] == out["toml"] == "false"


@pytest.mark.component
def test_new_script_needs_no_mapping_entry() -> None:
    """새 script도 이름 등록 없이 전체 실행·type 검사를 선택한다."""
    out = run_classifier(["scripts/unmapped_new_script.py"])
    assert out["tests"] == "true"
    assert out["full_tests"] == "true"
    assert out["full_type"] == "true"
    assert out["targets"] == ""


@pytest.mark.component
@pytest.mark.parametrize(
    "domain",
    [
        "data_platform",
        "hmda_data",
        "data_operations",
        "reliability",
        "review_ai",
        "runtime_ai",
        "orchestration",
        "new_domain",
    ],
)
def test_source_domains_need_no_manual_reverse_dependency_table(domain: str) -> None:
    out = run_classifier([f"src/hmda_reliability/{domain}/module.py"])
    assert out["python"] == out["full_tests"] == out["full_type"] == "true"


@pytest.mark.component
def test_shared_source_triggers_full_type_fallback() -> None:
    """Shared source는 project-wide type check로 fallback한다."""
    out = run_classifier(["src/hmda_reliability/shared/example.py"])
    assert out["python"] == "true"
    assert out["full_tests"] == "true"
    assert out["full_type"] == "true"


@pytest.mark.component
def test_runtime_config_triggers_full_type_fallback() -> None:
    """Python runtime config 변경은 project-wide type check로 fallback한다."""
    out = run_classifier(["pyproject.toml"])
    assert out["python"] == "true"
    assert out["full_tests"] == "true"
    assert out["full_type"] == "true"


@pytest.mark.component
def test_unknown_python_path_triggers_full_type_fallback() -> None:
    """분류되지 않은 Python path는 type validation을 silent skip하지 않는다."""
    out = run_classifier(["tools/example.py"])
    assert out["python"] == "true"
    assert out["full_type"] == "true"


@pytest.mark.component
@pytest.mark.parametrize(
    "dependency_path", [".python-version", "pyproject.toml", "uv.lock"]
)
def test_dependency_changes_cover_runtime_in_full_suite(
    dependency_path: str,
) -> None:
    """Dependency 변경은 dbt/Airflow를 포함한 전체 non-resource 검사를 선택한다."""
    out = run_classifier([dependency_path])

    assert out["python"] == "true"
    assert out["tests"] == "true"
    assert out["full_tests"] == "true"
    assert out["full_type"] == "true"
    assert out["tach"] == "true"


@pytest.mark.component
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


@pytest.mark.component
def test_tach_only_change_runs_dependency_setup_without_python_suite() -> None:
    """tach.toml 단독 변경도 dependency setup과 Tach check를 활성화한다."""
    out = run_classifier(["tach.toml"])

    assert out["tach"] == "true"
    assert out["toml"] == "true"
    assert out["python"] == "false"
    assert out["tests"] == "false"
