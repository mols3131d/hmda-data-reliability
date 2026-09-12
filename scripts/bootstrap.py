#!/usr/bin/env python3
"""Bootstrap repository state for setup, sessions, or tooling updates.

Orchestrates initialization and refresh of developer and CI dependencies:
- `setup`: Run once after clone to configure virtualenv dependencies, Git hooks,
  agent assets, local Node tools (Biome, Tombi), and OpenSpec.
- `session`: Fast idempotent restoration of Python dependencies, agent assets,
  and local Node tools needed to start an interactive or CI coding session.
- `update`: Refresh external tooling sources (agent assets, OpenSpec latest,
  and Node tools in `.local/tooling`).

Failure Semantics:
- Steps execute sequentially in declared order.
- If any step fails (returns non-zero), execution halts immediately and returns
  that exit code.
- If a prerequisite (like `uv`) is missing, raises `RuntimeError` caught by `main`
  and exits with code 2.
"""

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
    """Sync locked Python dependencies via uv.

    Raises:
        RuntimeError: If uv is not available on PATH.
    """
    if shutil.which("uv") is None:
        raise RuntimeError("uv is required to bootstrap this repository.")
    return run(["uv", "sync", "--locked"], cwd=REPO_ROOT)


def _install_hooks() -> int:
    """Install repository Git hooks managed by lefthook."""
    return run(["uv", "run", "--no-sync", "lefthook", "install"], cwd=REPO_ROOT)


def _sync_agent_assets(action: str) -> int:
    """Synchronize agent skills, rules, and prompts via agent_assets.py script."""
    return run(
        [sys.executable, str(AGENT_ASSETS_SCRIPT), action],
        cwd=REPO_ROOT,
    )


def _sync_openspec() -> int:
    """Update OpenSpec schemas and tooling using npm exec."""
    return run_npm_exec(OPENSPEC_PACKAGE, "openspec", ("update",), cwd=REPO_ROOT)


def _install_node_tools() -> int:
    """Install local Node-based linters and formatters into .local/tooling."""
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
    """Ensure required Node tools exist locally, installing only if missing."""
    if all(
        local_node_tool_path(tool, cwd=REPO_ROOT).is_file() for tool in NODE_TOOL_NAMES
    ):
        return 0
    return _install_node_tools()


def _steps(action: str) -> list[Step]:
    """Assemble the ordered sequence of named steps for a given action.

    Args:
        action: One of 'setup', 'session', or 'update'.

    Returns:
        List of (label, step_callable) pairs executed in sequence.
    """
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
    """CLI entrypoint for repository bootstrapping."""
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
