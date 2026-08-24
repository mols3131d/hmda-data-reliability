#!/usr/bin/env python3
"""Run Rulesync and validate repository-local compatibility projections."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CLAUDE_RULES_DIR = REPO_ROOT / ".claude" / "rules"
AGENTSMD_BRIDGE_PREFIX = "agentsmd-"

_ACTIONS: dict[str, tuple[str, ...]] = {
    "preview": ("generate", "--dry-run"),
    "generate": ("generate",),
    "check": ("generate", "--check"),
    "doctor": ("doctor", "--strict"),
}


def _npx_command(args: Sequence[str]) -> list[str]:
    executable = shutil.which("npx.cmd") if os.name == "nt" else shutil.which("npx")
    if executable is None:
        executable = shutil.which("npx")
    if executable is None:
        raise RuntimeError("npx is required to run Rulesync.")
    return [executable, "--yes", "rulesync@latest", *args]


def _run(args: Sequence[str], *, cwd: Path = REPO_ROOT) -> int:
    command = _npx_command(args)
    if os.name == "nt":
        command_line = subprocess.list2cmdline(command)
        return subprocess.run(
            ["cmd.exe", "/d", "/s", "/c", command_line],
            cwd=cwd,
            check=False,
        ).returncode
    return subprocess.run(command, cwd=cwd, check=False).returncode


def _agent_instruction_paths() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError("git ls-files failed while discovering AGENTS.md files.")

    return sorted(
        Path(line)
        for line in result.stdout.splitlines()
        if line and Path(line).name == "AGENTS.md"
    )


def _agentsmd_bridge_outputs() -> dict[Path, str]:
    with tempfile.TemporaryDirectory(prefix="rulesync-agentsmd-") as temp_dir:
        temp_root = Path(temp_dir)
        for relative_path in _agent_instruction_paths():
            source = REPO_ROOT / relative_path
            target = temp_root / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)

        returncode = _run(
            ("convert", "--from", "agentsmd", "--to", "claudecode", "--features", "rules"),
            cwd=temp_root,
        )
        if returncode != 0:
            raise RuntimeError("Rulesync AGENTS.md to Claude Code conversion failed.")

        expected: dict[Path, str] = {}
        root_rule = temp_root / "CLAUDE.md"
        if root_rule.is_file():
            expected[CLAUDE_RULES_DIR / f"{AGENTSMD_BRIDGE_PREFIX}root.md"] = (
                root_rule.read_text(encoding="utf-8")
            )

        generated_rules = temp_root / ".claude" / "rules"
        if generated_rules.is_dir():
            for rule_path in sorted(generated_rules.glob("*.md")):
                expected[
                    CLAUDE_RULES_DIR / f"{AGENTSMD_BRIDGE_PREFIX}{rule_path.name}"
                ] = rule_path.read_text(encoding="utf-8")

        return expected


def _existing_agentsmd_bridge_paths() -> set[Path]:
    if not CLAUDE_RULES_DIR.is_dir():
        return set()
    return set(CLAUDE_RULES_DIR.glob(f"{AGENTSMD_BRIDGE_PREFIX}*.md"))


def _check_agentsmd_bridge() -> int:
    expected = _agentsmd_bridge_outputs()
    actual_paths = _existing_agentsmd_bridge_paths()
    stale = sorted(actual_paths - expected.keys())
    mismatched = sorted(
        path
        for path, content in expected.items()
        if not path.is_file() or path.read_text(encoding="utf-8") != content
    )

    for path in stale:
        print(f"stale Claude AGENTS.md projection: {path.relative_to(REPO_ROOT)}")
    for path in mismatched:
        print(f"stale Claude AGENTS.md projection: {path.relative_to(REPO_ROOT)}")
    return 1 if stale or mismatched else 0


def _write_agentsmd_bridge() -> None:
    expected = _agentsmd_bridge_outputs()
    CLAUDE_RULES_DIR.mkdir(parents=True, exist_ok=True)
    for path in _existing_agentsmd_bridge_paths() - expected.keys():
        path.unlink()
    for path, content in expected.items():
        path.write_text(content, encoding="utf-8")


def _preview_agentsmd_bridge() -> int:
    expected = _agentsmd_bridge_outputs()
    actual_paths = _existing_agentsmd_bridge_paths()
    changed = sorted(
        path
        for path, content in expected.items()
        if not path.is_file() or path.read_text(encoding="utf-8") != content
    )
    stale = sorted(actual_paths - expected.keys())
    for path in changed:
        print(f"would update Claude AGENTS.md projection: {path.relative_to(REPO_ROOT)}")
    for path in stale:
        print(f"would remove Claude AGENTS.md projection: {path.relative_to(REPO_ROOT)}")
    return 0


def _validate() -> int:
    returncode = _run(_ACTIONS["doctor"])
    if returncode != 0:
        return returncode
    returncode = _run(_ACTIONS["check"])
    if returncode != 0:
        return returncode
    return _check_agentsmd_bridge()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run Rulesync using repository rulesync.jsonc and compatibility projections.",
    )
    parser.add_argument(
        "action",
        choices=(*_ACTIONS, "validate"),
        help=(
            "preview or generate projections, check drift, run doctor, "
            "or run doctor + projection checks"
        ),
    )
    args = parser.parse_args()

    try:
        if args.action == "validate":
            return _validate()

        returncode = _run(_ACTIONS[args.action])
        if returncode != 0:
            return returncode
        if args.action == "generate":
            _write_agentsmd_bridge()
            return 0
        if args.action == "check":
            return _check_agentsmd_bridge()
        if args.action == "preview":
            return _preview_agentsmd_bridge()
        return 0
    except RuntimeError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
