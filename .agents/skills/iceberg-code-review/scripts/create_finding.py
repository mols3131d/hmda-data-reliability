#!/usr/bin/env python3
"""Generates a code review finding file from a template."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from _shared import ReviewFileCreationError, copy_template, validate_slug

LOGGER = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create code review finding file")
    parser.add_argument("--summary-file", required=True, type=Path)
    parser.add_argument("--domain", required=True)
    parser.add_argument("--finding", required=True)
    return parser.parse_args()


def create_finding(summary_file: Path, domain: str, finding: str) -> Path:
    for name, value in (("domain", domain), ("finding", finding)):
        validate_slug(name, value)

    if not summary_file.is_file():
        raise ReviewFileCreationError(f"SUMMARY_FILE_NOT_FOUND: {summary_file}")

    destination = summary_file.parent / f"{domain}-{finding}.md"
    return copy_template("{{domain}}-{{finding}}.md", destination)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = parse_args()

    try:
        destination = create_finding(args.summary_file, args.domain, args.finding)
    except ReviewFileCreationError as error:
        LOGGER.error("Fail: %s", error, extra={"reason": str(error)})
        return 1

    LOGGER.info("OK: %s", destination.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
