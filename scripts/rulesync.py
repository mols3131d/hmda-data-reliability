#!/usr/bin/env python3
"""Run the latest Rulesync against repository-local rule assets."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from collections.abc import Sequence

_ACTIONS: dict[str, tuple[str, ...]] = {
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


def _run(args: Sequence[str]) -> int:
    command = _npx_command(args)
    if os.name == "nt":
        command_line = subprocess.list2cmdline(command)
        return subprocess.run(
            ["cmd.exe", "/d", "/s", "/c", command_line],
            check=False,
        ).returncode
    return subprocess.run(command, check=False).returncode


def _validate() -> int:
    for action in ("doctor", "check"):
        returncode = _run(_ACTIONS[action])
        if returncode != 0:
            return returncode
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the latest Rulesync using repository rulesync.jsonc.",
    )
    parser.add_argument(
        "action",
        choices=(*_ACTIONS, "validate"),
        help=(
            "generate projections, check drift, run doctor, "
            "or run doctor + check"
        ),
    )
    args = parser.parse_args()

    try:
        if args.action == "validate":
            return _validate()
        return _run(_ACTIONS[args.action])
    except RuntimeError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
