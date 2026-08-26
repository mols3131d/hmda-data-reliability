#!/usr/bin/env python3
"""Install or update repository-managed Agent Assets."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from _commands import run, run_npx

REPO_ROOT = Path(__file__).resolve().parents[1]
RULESYNC_SCRIPT = REPO_ROOT / "scripts" / "rulesync.py"
ROUTE_SCRIPT = REPO_ROOT / "scripts" / "generate_agent_routes.py"
SKILLS_LOCK = REPO_ROOT / "skills-lock.json"

_SKILLS_ACTIONS: dict[str, tuple[str, ...]] = {
    "install": ("experimental_install",),
    "update": ("update", "--project", "--yes"),
}


def _run_script(path: Path, *args: str) -> int:
    return run([sys.executable, str(path), *args], cwd=REPO_ROOT)


def _run_skills(action: str) -> int:
    if not SKILLS_LOCK.is_file():
        print("skills-lock.json not found; skipping Skills CLI.")
        return 0
    return run_npx("skills@latest", _SKILLS_ACTIONS[action], cwd=REPO_ROOT)


def _sync(action: str) -> int:
    rulesync_code = _run_script(RULESYNC_SCRIPT, action)
    if rulesync_code != 0:
        return rulesync_code

    skills_code = _run_skills(action)
    routes_code = _run_script(ROUTE_SCRIPT)
    return skills_code or routes_code


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Restore locked Agent Assets or update their managed sources."
    )
    parser.add_argument(
        "action",
        choices=tuple(_SKILLS_ACTIONS),
        help="install locked assets or update managed sources",
    )
    args = parser.parse_args()

    try:
        return _sync(args.action)
    except RuntimeError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
