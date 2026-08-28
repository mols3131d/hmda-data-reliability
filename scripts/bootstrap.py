#!/usr/bin/env python3
"""Bootstrap repository state for setup, sessions, or tooling updates."""

from __future__ import annotations

import argparse
import shutil
import sys
from collections.abc import Callable
from pathlib import Path

from _commands import run, run_npx

REPO_ROOT = Path(__file__).resolve().parents[1]
AGENT_ASSETS_SCRIPT = REPO_ROOT / "scripts" / "agent_assets.py"
BIOME_SCRIPT = REPO_ROOT / "scripts" / "biome.py"
OPENSPEC_PACKAGE = "@fission-ai/openspec@latest"

Step = tuple[str, Callable[[], int]]


def _sync_dependencies() -> int:
    if shutil.which("uv") is None:
        raise RuntimeError("uv is required to bootstrap this repository.")
    return run(["uv", "sync", "--locked"], cwd=REPO_ROOT)


def _install_hooks() -> int:
    return run(["uv", "run", "lefthook", "install"], cwd=REPO_ROOT)


def _sync_agent_assets(action: str) -> int:
    return run(
        [sys.executable, str(AGENT_ASSETS_SCRIPT), action],
        cwd=REPO_ROOT,
    )


def _sync_openspec() -> int:
    return run_npx(OPENSPEC_PACKAGE, ("update",), cwd=REPO_ROOT)


def _check_biome() -> int:
    return run([sys.executable, str(BIOME_SCRIPT), "--version"], cwd=REPO_ROOT)


def _steps(action: str) -> list[Step]:
    if action == "update":
        return [
            ("agent assets", lambda: _sync_agent_assets("update")),
            ("openspec", _sync_openspec),
        ]

    steps: list[Step] = [("dependencies", _sync_dependencies)]
    if action == "setup":
        steps.append(("git hooks", _install_hooks))
    steps.append(("agent assets", lambda: _sync_agent_assets("install")))
    if action == "setup":
        steps.extend(
            [
                ("openspec", _sync_openspec),
                ("biome", _check_biome),
            ]
        )
    return steps


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Restore or update repository tooling state."
    )
    parser.add_argument(
        "action",
        choices=("setup", "session", "update"),
        help=(
            "setup once after clone, restore locked session state, "
            "or update external agent tooling"
        ),
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
