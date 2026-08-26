"""Small subprocess helpers shared by repository scripts."""

from __future__ import annotations

import os
import shutil
import subprocess
from collections.abc import Sequence
from pathlib import Path


def run(command: Sequence[str], *, cwd: Path) -> int:
    """Run a command and return its exit code."""
    return subprocess.run(list(command), cwd=cwd, check=False).returncode


def run_npx(package: str, args: Sequence[str], *, cwd: Path) -> int:
    """Run an npx package consistently on POSIX and Windows."""
    executable = shutil.which("npx.cmd") if os.name == "nt" else shutil.which("npx")
    if executable is None:
        executable = shutil.which("npx")
    if executable is None:
        raise RuntimeError(f"npx is required to run {package}.")

    command = [executable, "--yes", package, *args]
    if os.name == "nt":
        command_line = subprocess.list2cmdline(command)
        return subprocess.run(
            ["cmd.exe", "/d", "/s", "/c", command_line],
            cwd=cwd,
            check=False,
        ).returncode
    return run(command, cwd=cwd)
