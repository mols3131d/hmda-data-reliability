"""Repository Tach rules reject forbidden runtime imports without a full allowlist."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.component
REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def project(tmp_path: Path) -> Path:
    shutil.copyfile(REPO_ROOT / "tach.toml", tmp_path / "tach.toml")
    shutil.copytree(
        REPO_ROOT / "src",
        tmp_path / "src",
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    return tmp_path


def check(project: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["tach", "check"], cwd=project, text=True, capture_output=True, check=False
    )


@pytest.mark.parametrize(
    ("source", "target"),
    [
        ("reliability", "review_ai"),
        ("reliability", "runtime_ai"),
        ("runtime_ai", "review_ai"),
        ("runtime_ai", "reliability"),
    ],
)
def test_forbidden_runtime_import_fails(
    project: Path, source: str, target: str
) -> None:
    probe = project / "src/hmda_reliability" / source / "boundary_probe.py"
    probe.write_text(f"import hmda_reliability.{target}\n", encoding="utf-8")
    result = check(project)
    assert result.returncode != 0
    assert "boundary_probe.py" in result.stdout + result.stderr
    assert f"hmda_reliability.{target}" in result.stdout + result.stderr


def test_type_only_import_stays_outside_runtime_graph(project: Path) -> None:
    probe = project / "src/hmda_reliability/reliability/boundary_probe.py"
    probe.write_text(
        "from typing import TYPE_CHECKING\n"
        "if TYPE_CHECKING:\n"
        "    import hmda_reliability.review_ai\n",
        encoding="utf-8",
    )
    result = check(project)
    assert result.returncode == 0, result.stdout + result.stderr


def test_advisory_and_unrestricted_root_imports_remain_allowed(project: Path) -> None:
    root = project / "src/hmda_reliability"
    (root / "review_ai/boundary_probe.py").write_text(
        "import hmda_reliability.reliability\nimport hmda_reliability.runtime_ai\n",
        encoding="utf-8",
    )
    (root / "boundary_probe.py").write_text(
        "import hmda_reliability.review_ai\n", encoding="utf-8"
    )
    result = check(project)
    assert result.returncode == 0, result.stdout + result.stderr


def test_unowned_source_cannot_silently_use_implicit_root(project: Path) -> None:
    (project / "src/unowned.py").write_text(
        "import hmda_reliability.review_ai\n", encoding="utf-8"
    )
    result = check(project)
    assert result.returncode != 0
    assert "root" in (result.stdout + result.stderr).lower()
