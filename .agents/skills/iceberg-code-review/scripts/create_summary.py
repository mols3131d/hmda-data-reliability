#!/usr/bin/env python3
"""Generates a code review summary file from a template."""

from __future__ import annotations

import argparse
import logging
from datetime import date
from pathlib import Path

from shared import ReviewFileCreationError, copy_template, validate_slug

LOGGER = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create code review summary file")
    parser.add_argument("--reviews-dir", required=True, type=Path)
    parser.add_argument("--title-slug", required=True)
    return parser.parse_args()


def create_summary(reviews_dir: Path, title_slug: str) -> Path:
    validate_slug("title-slug", title_slug)
    destination = reviews_dir / f"{date.today():%Y%m%d}-{title_slug}" / "__summary__.md"
    return copy_template("__summary__.md", destination)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = parse_args()

    try:
        destination = create_summary(args.reviews_dir, args.title_slug)
    except ReviewFileCreationError as error:
        LOGGER.error("Fail: %s", error, extra={"reason": str(error)})
        return 1

    LOGGER.info("OK: %s", destination.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
