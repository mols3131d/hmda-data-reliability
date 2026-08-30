#!/usr/bin/env python3
"""Bootstrap repository state for setup, sessions, or tooling updates."""

from __future__ import annotations

import argparse
import shutil
import sys
from collections.abc import Callable
from pathlib import Path

from _commands import local_node_tool_path, run, run_npm, run_npm_exec

REPO_ROOT = Path(__file__).resolve().parents[1]
AGENT_ASSETS_SCRIPT = REPO_ROOT / "scripts" / "agent_assets.py"
NODE_TOOL_PREFIX = REPO_ROOT / ".local" / "tooling"
NODE_TOOL_PACKAGES = ("@biomejs/biome@2", "tombi@1")
NODE_TOOL_NAMES = ("biome", "tombi")
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
    return run_npm_exec(OPENSPEC_PACKAGE, "openspec", ("update",), cwd=REPO_ROOT)


def _install_node_tools() -> int:
    NODE_TOOL_PREFIX.mkdir(parents=True, exist_ok=True)
    return run_npm(
        (
            "install",
            "--prefix",
            str(NODE_TOOL_PREFIX),
            "--no-save",
            "--package-lock=false",
            *NODE_TOOL_PACKAGES,
        ),
        cwd=REPO_ROOT,
    )


def _ensure_node_tools() -> int:
    if all(
        local_node_tool_path(tool, cwd=REPO_ROOT).is_file() for tool in NODE_TOOL_NAMES
    ):
        return 0
    return _install_node_tools()


def _steps(action: str) -> list[Step]:
    if action == "update":
        return [
            ("agent assets", lambda: _sync_agent_assets("update")),
            ("openspec", _sync_openspec),
            ("node tools", _install_node_tools),
        ]

    steps: list[Step] = [("dependencies", _sync_dependencies)]
    if action == "setup":
        steps.append(("git hooks", _install_hooks))
    steps.append(("agent assets", lambda: _sync_agent_assets("install")))
    steps.append(("node tools", _ensure_node_tools))
    if action == "setup":
        steps.append(("openspec", _sync_openspec))
    return steps


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Restore or update repository tooling state."
    )
    parser.add_argument(
        "action",
        choices=("setup", "session", "update"),
        help=(
            "setup once after clone, restore session dependencies and local tools, "
            "or refresh external tooling sources"
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
