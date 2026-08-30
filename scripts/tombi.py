#!/usr/bin/env python3
"""Run the repository-local Tombi CLI."""

from __future__ import annotations

import sys
from pathlib import Path

from _commands import run_local_node_tool

REPO_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    return run_local_node_tool("tombi", sys.argv[1:], cwd=REPO_ROOT)


if __name__ == "__main__":
    raise SystemExit(main())
