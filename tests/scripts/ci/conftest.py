from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
import yaml

from tests.scripts.ci.helpers import REPO_ROOT, git


@pytest.fixture
def workflow_steps() -> dict[str, dict[str, object]]:
    workflow = yaml.safe_load(
        (REPO_ROOT / ".github/workflows/ci-lite.yml").read_text(encoding="utf-8")
    )
    return {step["name"]: step for step in workflow["jobs"]["check"]["steps"]}


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    git(root, "init", "-qb", "main")
    git(root, "config", "user.email", "ci-test@example.invalid")
    git(root, "config", "user.name", "CI Test")
    git(root, "-c", "commit.gpgsign=false", "commit", "--allow-empty", "-qm", "base")
    return root


@pytest.fixture
def tool_env(tmp_path: Path) -> dict[str, str]:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake_tool = (
        f"#!{sys.executable}\n"
        + """import json
import os
import shlex
import sys
from pathlib import Path

name = Path(sys.argv[0]).name
if name == "python3" and len(sys.argv) > 1 and sys.argv[1].startswith("scripts/ci/"):
    os.execv(sys.executable, [sys.executable, *sys.argv[1:]])
args = [name, *sys.argv[1:]]
with Path(os.environ["CI_LOG"]).open("a", encoding="utf-8") as log:
    log.write(json.dumps(args) + "\\n")
if args[:2] == ["rumdl", "fmt"]:
    print(os.environ.get("FORMAT_OUTPUT", ""))
    if os.environ.get("FORMAT_FILE"):
        with Path(os.environ["FORMAT_FILE"]).open("a", encoding="utf-8") as doc:
            doc.write("\\nFormatted\\n")
failure = shlex.split(os.environ.get("FAIL_COMMAND", ""))
if failure and args[:len(failure)] == failure:
    sys.exit(17)
"""
    )
    for name in ("rumdl", "uv", "npm", "python", "python3"):
        path = bin_dir / name
        path.write_text(fake_tool, encoding="utf-8")
        path.chmod(0o755)
    return os.environ | {
        "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
        "CI_LOG": str(tmp_path / "calls.jsonl"),
        "GITHUB_STEP_SUMMARY": str(tmp_path / "summary.md"),
        "FULL_TESTS": "false",
        "FULL_UNIT": "false",
        "TARGETS": "",
        "CI_TARGETS": "",
        "BOUNDARIES_CHECKED": "false",
        "FULL_TYPE": "false",
        "TYPE_TARGETS": "",
        "BULK": "false",
        "ARCHIVED": "false",
        "SPEC_TARGETS": "",
        "CHANGE_TARGETS": "",
        "FORMAT_OUTPUT": "",
        "FORMAT_FILE": "",
        "FAIL_COMMAND": "",
    }


@pytest.fixture
def openspec_repo(tmp_path: Path) -> Path:
    """Active Change inventory is test-owned, independent of repository archives."""
    for relative in (
        "openspec/specs/orchestration-pipeline/spec.md",
        "openspec/specs/reliability-data-contracts/spec.md",
        "openspec/changes/orchestration-quality-gate/proposal.md",
        "openspec/changes/orchestration-quality-gate/specs/orchestration-pipeline/spec.md",
    ):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# Classifier fixture\n", encoding="utf-8")
    return tmp_path
