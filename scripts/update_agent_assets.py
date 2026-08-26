#!/usr/bin/env python3
"""Update repository-managed Agent Assets."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
RULESYNC_SCRIPT = REPO_ROOT / "scripts" / "rulesync.py"
SKILLS_LOCK = REPO_ROOT / "skills-lock.json"


def _run(command: Sequence[str]) -> int:
    return subprocess.run(command, cwd=REPO_ROOT, check=False).returncode


def _npx_command(args: Sequence[str]) -> list[str]:
    executable = shutil.which("npx.cmd") if os.name == "nt" else shutil.which("npx")
    if executable is None:
        executable = shutil.which("npx")
    if executable is None:
        raise RuntimeError("npx is required to update Agent Skills.")
    return [executable, "--yes", "skills@latest", *args]


def _run_npx(args: Sequence[str]) -> int:
    command = _npx_command(args)
    if os.name == "nt":
        command_line = subprocess.list2cmdline(command)
        return subprocess.run(
            ["cmd.exe", "/d", "/s", "/c", command_line],
            cwd=REPO_ROOT,
            check=False,
        ).returncode
    return _run(command)


def _update_rulesync() -> int:
    return _run([sys.executable, str(RULESYNC_SCRIPT), "update"])


def _update_skills() -> int:
    if not SKILLS_LOCK.is_file():
        print("skills-lock.json not found; skipping Skills CLI update.")
        return 0
    return _run_npx(("update", "--project", "--yes"))


def main() -> int:
    try:
        returncode = _update_rulesync()
        if returncode != 0:
            return returncode
        return _update_skills()
    except RuntimeError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
