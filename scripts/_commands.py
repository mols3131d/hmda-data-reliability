"""Small subprocess helpers shared by repository scripts.

Provides cross-platform execution helpers for invoking external tools (Node, npm,
and repository-local CLI utilities) with consistent semantics across POSIX and
Windows operating systems.

Key Invariants:
- On Windows, avoids invoking `npm.cmd` through shell wrappers; resolves `node.exe`
  and the sibling `npm-cli.js` directly to prevent cmd.exe quoting vulnerabilities.
- For local Node tools installed under `.local/tooling`, executes via
  `npm exec --offline` on Windows to correctly resolve locally scoped binaries
  without a global PATH requirement.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from collections.abc import Sequence
from pathlib import Path

_NPM_CLI_RELATIVE_PATH = Path("node_modules") / "npm" / "bin" / "npm-cli.js"


def run(command: Sequence[str], *, cwd: Path) -> int:
    """Run a command in the specified directory and return its exit code.

    Args:
        command: Command-line elements to execute as an argument vector.
        cwd: Working directory where the subprocess should run.

    Returns:
        The integer return code of the terminated process (non-zero indicates failure).
    """
    return subprocess.run(list(command), cwd=cwd, check=False).returncode


def _npm_command(executable: str, args: Sequence[str]) -> list[str]:
    """Avoid the Windows npm.cmd shell wrapper when invoking npm.

    On Windows, invoking `npm.cmd` via `subprocess.run(shell=False)` can fail
    or misparse complex arguments. When `executable` points to a Windows batch
    or cmd wrapper, this helper resolves the underlying `node.exe` binary and
    `npm-cli.js` script to launch npm directly as a native process.

    Args:
        executable: Path or name of the npm executable located by `shutil.which`.
        args: Sequence of CLI arguments to pass to npm.

    Returns:
        A list of command tokens suitable for direct execution without a shell.

    Raises:
        RuntimeError: If `node.exe` or `npm-cli.js` cannot be found adjacent to
            the resolved `npm.cmd` or on system PATH.
    """
    if os.name != "nt" or not executable.lower().endswith((".bat", ".cmd")):
        return [executable, *args]

    executable_path = Path(executable)
    node_path = executable_path.with_name("node.exe")
    if not node_path.is_file():
        node_executable = shutil.which("node.exe") or shutil.which("node")
        if node_executable is None:
            raise RuntimeError("node.exe is required to run npm on Windows.")
        node_path = Path(node_executable)

    npm_cli_path = executable_path.parent / _NPM_CLI_RELATIVE_PATH
    if not npm_cli_path.is_file():
        raise RuntimeError(
            "npm-cli.js was not found next to npm.cmd; reinstall Node.js/npm."
        )

    return [str(node_path), str(npm_cli_path), *args]


def run_npm(args: Sequence[str], *, cwd: Path) -> int:
    """Run npm consistently on POSIX and Windows.

    Resolves npm on system PATH, unwraps Windows cmd wrappers to native node
    execution where applicable, and runs the requested npm arguments in `cwd`.

    Args:
        args: Command-line arguments passed to npm
            (e.g. `("install", "--prefix", ...)`).
        cwd: Working directory for the npm process.

    Returns:
        The integer exit code of the npm process.

    Raises:
        RuntimeError: If npm is not installed or not discoverable on PATH.
    """
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
    """Run a package binary through npm without a project dependency.

    Invokes `npm exec --yes --package=<package> -- <binary> <args...>` to run
    on-demand tooling (such as OpenSpec or rulesync) in an isolated manner.

    Args:
        package: npm package specifier with optional version tag
            (e.g. `@biomejs/biome@2`).
        binary: Binary name within the package to invoke.
        args: Additional CLI arguments forwarded to the binary.
        cwd: Working directory where the binary is executed.

    Returns:
        The integer exit code of the executed binary.
    """
    return run_npm(
        ("exec", "--yes", f"--package={package}", "--", binary, *args),
        cwd=cwd,
    )


def local_node_tool_path(tool: str, *, cwd: Path) -> Path:
    """Return the repository-local npm binary path for a tool.

    Repository-local Node tools are installed under `.local/tooling/node_modules/.bin`.

    Args:
        tool: Name of the CLI tool (e.g. `"biome"`, `"tombi"`).
        cwd: Repository root directory containing `.local/`.

    Returns:
        Path to the local executable file, including `.cmd` suffix on Windows.
    """
    suffix = ".cmd" if os.name == "nt" else ""
    return cwd / ".local" / "tooling" / "node_modules" / ".bin" / f"{tool}{suffix}"


def run_local_node_tool(tool: str, args: Sequence[str], *, cwd: Path) -> int:
    """Run a repository-local Node tool installed by bootstrap.

    Checks that the tool is installed in `.local/tooling/`. On Windows, delegates
    to `npm exec --offline --prefix ...` to ensure clean resolution; on POSIX,
    executes the binary directly.

    Args:
        tool: Name of the CLI tool (e.g. `"biome"`, `"tombi"`).
        args: Arguments forwarded to the local CLI tool.
        cwd: Repository root directory.

    Returns:
        The integer exit code of the executed tool.

    Raises:
        RuntimeError: If the tool is not installed under `.local/tooling`.
    """
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
