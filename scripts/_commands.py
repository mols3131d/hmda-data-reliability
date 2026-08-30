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


def _npm_command(executable: str, args: Sequence[str]) -> list[str]:
    """Avoid the Windows npm.cmd shell wrapper when invoking npm."""
    if os.name != "nt" or not executable.lower().endswith((".bat", ".cmd")):
        return [executable, *args]

    executable_path = Path(executable)
    node_path = executable_path.with_name("node.exe")
    if not node_path.is_file():
        node_executable = shutil.which("node.exe") or shutil.which("node")
        if node_executable is None:
            raise RuntimeError("node.exe is required to run npm on Windows.")
        node_path = Path(node_executable)

    npm_cli_path = (
        executable_path.parent / "node_modules" / "npm" / "bin" / "npm-cli.js"
    )
    if not npm_cli_path.is_file():
        raise RuntimeError(
            "npm-cli.js was not found next to npm.cmd; reinstall Node.js/npm."
        )

    return [str(node_path), str(npm_cli_path), *args]


def run_npm(args: Sequence[str], *, cwd: Path) -> int:
    """Run npm consistently on POSIX and Windows."""
    executable = shutil.which("npm.cmd") if os.name == "nt" else shutil.which("npm")
    if executable is None:
        executable = shutil.which("npm")
    if executable is None:
        raise RuntimeError("npm is required to run repository Node tooling.")

    return run(_npm_command(executable, args), cwd=cwd)


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

    if os.name == "nt":
        return run_npm(
            (
                "exec",
                "--offline",
                "--prefix",
                str(cwd / ".local" / "tooling"),
                "--",
                tool,
                *args,
            ),
            cwd=cwd,
        )
    return run([str(executable), *args], cwd=cwd)
