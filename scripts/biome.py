#!/usr/bin/env python3
"""Run the repository-local Biome CLI.

Thin wrapper forwarding command-line arguments to repository-local Biome binary
in `.local/tooling/node_modules/.bin/biome` via `run_local_node_tool`.
Maintains consistent execution across POSIX and Windows (using offline npm exec).
"""

from __future__ import annotations

import sys
from pathlib import Path

from _commands import run_local_node_tool

REPO_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    """Execute repository-local Biome CLI with all forwarded command-line arguments.

    Returns:
        The exit code of the underlying Biome command.
    """
    return run_local_node_tool("biome", sys.argv[1:], cwd=REPO_ROOT)


if __name__ == "__main__":
    raise SystemExit(main())
