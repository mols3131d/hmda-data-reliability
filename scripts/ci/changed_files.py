"""Git path collection and subprocess failure handling shared by CI entrypoints."""

from __future__ import annotations

import os
import re
import subprocess
import sys
from collections.abc import Callable, Sequence
from pathlib import Path


def environment_targets(name: str) -> list[str]:
    return re.findall(r"[^ \t\n]+", os.environ.get(name, ""))


def changed_paths(
    base: str = "HEAD^1",
    head: str = "HEAD",
    patterns: Sequence[str] = (),
    *,
    cwd: Path | None = None,
) -> list[str]:
    revisions = []
    for revision in (base, head):
        resolved = subprocess.run(
            [
                "git",
                "rev-parse",
                "--verify",
                "--end-of-options",
                f"{revision}^{{commit}}",
            ],
            cwd=cwd,
            stdout=subprocess.PIPE,
            text=True,
            check=True,
        ).stdout.strip()
        revisions.append(resolved)
    output = subprocess.run(
        [
            "git",
            "diff",
            "--no-renames",
            "--name-only",
            "-z",
            *revisions,
            "--",
            *patterns,
        ],
        cwd=cwd,
        stdout=subprocess.PIPE,
        check=True,
    ).stdout
    return [os.fsdecode(path) for path in output.split(b"\0") if path]


def collect_changed_files(
    base: str = "HEAD^1",
    head: str = "HEAD",
    patterns: Sequence[str] = (),
    *,
    cwd: Path | None = None,
) -> list[str]:
    root = cwd or Path.cwd()
    return [
        path
        for path in changed_paths(base, head, patterns, cwd=cwd)
        if not path.startswith("inbox/") and (root / path).is_file()
    ]


def run(command: Sequence[str], *, capture: bool = False) -> str:
    result = subprocess.run(
        command,
        check=True,
        text=True,
        stdout=subprocess.PIPE if capture else None,
    )
    return result.stdout if capture else ""


def entrypoint(main: Callable[[], None]) -> None:
    try:
        main()
    except subprocess.CalledProcessError as error:
        code = error.returncode
        raise SystemExit(code if code >= 0 else 128 - code) from error
    except FileNotFoundError as error:
        print(error, file=sys.stderr)
        raise SystemExit(127) from error
    except PermissionError as error:
        print(error, file=sys.stderr)
        raise SystemExit(126) from error
