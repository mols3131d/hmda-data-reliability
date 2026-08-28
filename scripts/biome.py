#!/usr/bin/env python3
"""Run the repository-pinned Biome CLI."""

from __future__ import annotations

import sys
from pathlib import Path

from _commands import run_npx

REPO_ROOT = Path(__file__).resolve().parents[1]
BIOME_PACKAGE = "@biomejs/biome@2.5.10"


def main() -> int:
    return run_npx(BIOME_PACKAGE, sys.argv[1:], cwd=REPO_ROOT)


if __name__ == "__main__":
    raise SystemExit(main())
