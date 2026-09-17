"""Executable checks for the repository Tach configuration."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
TACH_CONFIG = REPO_ROOT / "tach.toml"


@pytest.mark.component
def test_tach_configuration_covers_source_and_only_forbids_canonical_edges() -> None:
    """Configuration keeps source coverage explicit and policy scope minimal."""
    config = tomllib.loads(TACH_CONFIG.read_text(encoding="utf-8"))
    modules = {module["path"]: module for module in config["modules"]}
    expected_modules = {
        "hmda_reliability",
        *{
            f"hmda_reliability.{path.name}"
            for path in (REPO_ROOT / "src" / "hmda_reliability").iterdir()
            if path.is_dir() and not path.name.startswith((".", "_"))
        },
    }

    assert config["source_roots"] == ["src"]
    assert config["root_module"] == "forbid"
    assert config["ignore_type_checking_imports"] is True
    assert set(modules) == expected_modules
    assert "forbid_circular_dependencies" not in config
    assert all("depends_on" not in module for module in modules.values())
    assert modules["hmda_reliability.reliability"]["cannot_depend_on"] == [
        "hmda_reliability.review_ai",
        "hmda_reliability.runtime_ai",
    ]
    assert modules["hmda_reliability.runtime_ai"]["cannot_depend_on"] == [
        "hmda_reliability.reliability",
        "hmda_reliability.review_ai",
    ]


@pytest.mark.component
def test_tach_rejects_forbidden_runtime_dependency(tmp_path: Path) -> None:
    """A representative forbidden import fails the real Tach check."""
    project_root = tmp_path / "tach-project"
    shutil.copytree(REPO_ROOT / "src", project_root / "src")
    shutil.copy2(TACH_CONFIG, project_root / "tach.toml")
    negative_control = (
        project_root
        / "src"
        / "hmda_reliability"
        / "reliability"
        / "_tach_negative_control.py"
    )
    negative_control.write_text(
        "from hmda_reliability import review_ai\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "-m", "tach", "check"],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    output = result.stdout + result.stderr
    assert "hmda_reliability.reliability" in output
    assert "hmda_reliability.review_ai" in output
