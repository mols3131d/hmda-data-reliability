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


def _run_windows_command(command: Sequence[str], *, cwd: Path) -> int:
    command_line = subprocess.list2cmdline(list(command))
    return subprocess.run(
        ["cmd.exe", "/d", "/s", "/c", command_line],
        cwd=cwd,
        check=False,
    ).returncode


def run_npx(package: str, args: Sequence[str], *, cwd: Path) -> int:
    """Run an npx package consistently on POSIX and Windows."""
    executable = shutil.which("npx.cmd") if os.name == "nt" else shutil.which("npx")
    if executable is None:
        executable = shutil.which("npx")
    if executable is None:
        raise RuntimeError(f"npx is required to run {package}.")

    command = [executable, "--yes", package, *args]
    if os.name == "nt":
        return _run_windows_command(command, cwd=cwd)
    return run(command, cwd=cwd)


def run_npm(args: Sequence[str], *, cwd: Path) -> int:
    """Run npm consistently on POSIX and Windows."""
    executable = shutil.which("npm.cmd") if os.name == "nt" else shutil.which("npm")
    if executable is None:
        executable = shutil.which("npm")
    if executable is None:
        raise RuntimeError("npm is required to install repository Node tooling.")

    command = [executable, *args]
    if os.name == "nt":
        return _run_windows_command(command, cwd=cwd)
    return run(command, cwd=cwd)


def local_node_tool_path(tool: str, *, cwd: Path) -> Path:
    """Return the repository-local npm binary path for a tool."""
    suffix = ".cmd" if os.name == "nt" else ""
    return cwd / ".local" / "tooling" / "node_modules" / ".bin" / f"{tool}{suffix}"


def run_local_node_tool(tool: str, args: Sequence[str], *, cwd: Path) -> int:
    """Run a repository-local Node tool installed by bootstrap."""
    executable = local_node_tool_path(tool, cwd=cwd)
    if not executable.is_file():
        raise RuntimeError(
            f"{tool} is not installed; run `python scripts/bootstrap.py setup`."
        )

    command = [str(executable), *args]
    if os.name == "nt":
        return _run_windows_command(command, cwd=cwd)
    return run(command, cwd=cwd)
