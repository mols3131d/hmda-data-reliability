"""Small subprocess helpers shared by repository scripts."""

from __future__ import annotations

import os
import shutil
import subprocess
from collections.abc import Sequence
from pathlib import Path


def run(
    command: Sequence[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
) -> int:
    """Run a command and return its exit code."""
    return subprocess.run(list(command), cwd=cwd, env=env, check=False).returncode


def _resolve_github_token() -> str | None:
    """Get GitHub token from environment or gh CLI if available."""
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        return token
    gh = shutil.which("gh")
    if gh:
        try:
            proc = subprocess.run(
                [gh, "auth", "token"],
                capture_output=True,
                text=True,
                check=False,
            )
            if proc.returncode == 0:
                token = proc.stdout.strip()
                if token:
                    return token
        except OSError:
            pass
    return None


def run_npx(package: str, args: Sequence[str], *, cwd: Path) -> int:
    """Run an npx package consistently on POSIX and Windows."""
    executable = shutil.which("npx.cmd") if os.name == "nt" else shutil.which("npx")
    if executable is None:
        executable = shutil.which("npx")
    if executable is None:
        raise RuntimeError(f"npx is required to run {package}.")

    env = os.environ.copy()
    github_token = _resolve_github_token()
    if github_token and "GITHUB_TOKEN" not in env:
        env["GITHUB_TOKEN"] = github_token

    command = [executable, "--yes", package, *args]
    if os.name == "nt":
        command_line = subprocess.list2cmdline(command)
        return subprocess.run(
            ["cmd.exe", "/d", "/s", "/c", command_line],
            cwd=cwd,
            env=env,
            check=False,
        ).returncode
    return run(command, cwd=cwd, env=env)
