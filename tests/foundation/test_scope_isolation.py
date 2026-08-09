"""PR Scope & Ownership Isolation regression test."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.component

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DISALLOWED_PR_PATHS = {
    "scripts/wsl-status.sh",
}


def test_pr_scope_does_not_contain_disallowed_unrelated_files() -> None:
    """PR 변경 및 working tree에 무관한 외부 파일이 포함되지 않아야 한다."""
    # Check final combined diff against origin/main (excluding deleted files)
    diff_proc = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=d", "origin/main"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if diff_proc.returncode != 0:
        msg = f"git diff failed (code {diff_proc.returncode}). Skipping test."
        pytest.skip(msg)

    changed_files = set(diff_proc.stdout.splitlines())

    disallowed_found = DISALLOWED_PR_PATHS.intersection(changed_files)
    msg = (
        "Disallowed unrelated files found in PR scope/working tree: "
        f"{disallowed_found}. Separate these changes into their respective PRs."
    )
    assert not disallowed_found, msg
