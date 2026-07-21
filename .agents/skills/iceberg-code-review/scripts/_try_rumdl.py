#!/usr/bin/env python3
"""Format markdown files with rumdl if available."""

import logging
import shlex
import subprocess
import sys
from pathlib import Path

from _shared import load_config


def _get_rumdl_exec() -> str | None:
    return load_config().get("RUMDL_EXEC")


def try_format_with_rumdl(file_path: Path) -> None:
    """Format the given file using rumdl if it is installed."""
    rumdl_exec = _get_rumdl_exec()
    if not rumdl_exec:
        return

    cmd = shlex.split(rumdl_exec) + ["fmt", str(file_path)]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        logging.getLogger(__name__).warning(
            "rumdl formatting failed for %s: %s", file_path, exc.stderr.strip()
        )
    except OSError as exc:
        logging.getLogger(__name__).warning(
            "Failed to execute rumdl for %s: %s", file_path, exc
        )


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    files = sys.argv[1:]
    if not files:
        logging.info("No files provided.")
        return 0

    for f in files:
        path = Path(f)
        if path.is_file() and path.suffix == ".md":
            try_format_with_rumdl(path)

    return 0


if __name__ == "__main__":
    sys.exit(main())
