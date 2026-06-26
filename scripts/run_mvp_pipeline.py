"""MVP pipeline 실행 스크립트."""

# ruff: noqa: E402, I001

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from project_pivot.pipeline.cli import main


if __name__ == "__main__":
    raise SystemExit(main(["run", *sys.argv[1:]]))
