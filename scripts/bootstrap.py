#!/usr/bin/env python3
"""Bootstrap repository state for setup or a new work session."""

from __future__ import annotations

import argparse
import shutil
import sys
from collections.abc import Callable
from pathlib import Path

from _commands import run

REPO_ROOT = Path(__file__).resolve().parents[1]
AGENT_ASSETS_SCRIPT = REPO_ROOT / "scripts" / "agent_assets.py"

Step = tuple[str, Callable[[], int]]


def _sync_dependencies() -> int:
    if shutil.which("uv") is None:
        raise RuntimeError("uv is required to bootstrap this repository.")
    return run(["uv", "sync", "--locked"], cwd=REPO_ROOT)


def _install_hooks() -> int:
    return run(["uv", "run", "lefthook", "install"], cwd=REPO_ROOT)


def _install_agent_assets() -> int:
    return run(
        [sys.executable, str(AGENT_ASSETS_SCRIPT), "install"],
        cwd=REPO_ROOT,
    )


def _steps(action: str) -> list[Step]:
    steps: list[Step] = [("dependencies", _sync_dependencies)]
    if action == "setup":
        steps.append(("git hooks", _install_hooks))
    steps.append(("agent assets", _install_agent_assets))
    return steps


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Restore the repository state needed for local development."
    )
    parser.add_argument(
        "action",
        choices=("setup", "session"),
        help="setup once after clone, or refresh state at session start",
    )
    args = parser.parse_args()

    try:
        for label, step in _steps(args.action):
            print(f"==> {label}")
            returncode = step()
            if returncode != 0:
                return returncode
    except RuntimeError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
