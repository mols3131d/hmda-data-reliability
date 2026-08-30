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


def run_npm(args: Sequence[str], *, cwd: Path) -> int:
    """Run npm consistently on POSIX and Windows."""
    executable = shutil.which("npm.cmd") if os.name == "nt" else shutil.which("npm")
    if executable is None:
        executable = shutil.which("npm")
    if executable is None:
        raise RuntimeError("npm is required to run repository Node tooling.")

    return run([executable, *args], cwd=cwd)


def run_npm_exec(
    package: str,
    binary: str,
    args: Sequence[str],
    *,
    cwd: Path,
) -> int:
    """Run a package binary through npm without a project dependency."""
    return run_npm(
        ("exec", "--yes", f"--package={package}", "--", binary, *args),
        cwd=cwd,
    )


def local_node_tool_path(tool: str, *, cwd: Path) -> Path:
    """Return the repository-local npm binary path for a tool."""
    suffix = ".cmd" if os.name == "nt" else ""
    return cwd / ".local" / "tooling" / "node_modules" / ".bin" / f"{tool}{suffix}"


def run_local_node_tool(tool: str, args: Sequence[str], *, cwd: Path) -> int:
    """Run a repository-local Node tool installed by bootstrap."""
    executable = local_node_tool_path(tool, cwd=cwd)
    if not executable.is_file():
        raise RuntimeError(
            f"{tool} is not installed; run "
            "`uv run --no-sync python scripts/bootstrap.py setup`."
        )

    return run([str(executable), *args], cwd=cwd)
