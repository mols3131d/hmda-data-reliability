#!/usr/bin/env python3
"""Validates a code review finding file."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from checks import validate_no_comments, validate_review_file

LOGGER = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate code review finding file")
    parser.add_argument("review_file_path", type=Path)
    return parser.parse_args()


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = parse_args()

    errors = []
    errors.extend(validate_no_comments(args.review_file_path))
    errors.extend(validate_review_file(args.review_file_path, expected_type="finding"))

    if errors:
        for error in errors:
            LOGGER.error("FAIL: %s", error)
        return 1

    LOGGER.info("OK: %s", args.review_file_path.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
