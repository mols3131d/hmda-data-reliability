"""Evidence provenance and repository dirty status verification tests."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from scripts.run_actual_source import EvidenceProvenanceError, _repository_revision

pytestmark = pytest.mark.component


def test_repository_revision_returns_exact_head_when_clean(tmp_path: Path) -> None:
    """Clean repository에서 _repository_revision은 HEAD revision만 반환한다."""
    subprocess.run(["git", "init"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True
    )

    (tmp_path / "file.txt").write_text("hello", encoding="utf-8")
    subprocess.run(["git", "add", "file.txt"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=tmp_path, check=True)

    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    rev = _repository_revision(tmp_path)
    assert rev == head
    assert "-dirty" not in rev


@pytest.mark.parametrize(
    "setup_action",
    [
        "unstaged",
        "staged",
        "untracked",
    ],
)
def test_repository_revision_raises_on_dirty_tree(
    tmp_path: Path, setup_action: str
) -> None:
    """git status --porcelain 기준 변경이 있으면 EvidenceProvenanceError를 던진다."""
    subprocess.run(["git", "init"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True
    )

    tracked_file = tmp_path / "tracked.txt"
    tracked_file.write_text("v1", encoding="utf-8")
    subprocess.run(["git", "add", "tracked.txt"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=tmp_path, check=True)

    if setup_action == "unstaged":
        tracked_file.write_text("v2", encoding="utf-8")
    elif setup_action == "staged":
        tracked_file.write_text("v2", encoding="utf-8")
        subprocess.run(["git", "add", "tracked.txt"], cwd=tmp_path, check=True)
    elif setup_action == "untracked":
        (tmp_path / "new_untracked.txt").write_text("untracked", encoding="utf-8")

    with pytest.raises(EvidenceProvenanceError, match="dirty"):
        _repository_revision(tmp_path)
