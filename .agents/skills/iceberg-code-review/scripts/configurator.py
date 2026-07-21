#!/usr/bin/env python3
"""Configures user data settings for iceberg-code-review skill."""

import argparse
import json
import logging
from typing import Any

from _shared import CONFIG_FILE, is_initialized

LOGGER = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Configure user data settings")
    parser.add_argument("--reviews-dir", type=str, help="Directory to store reviews")
    parser.add_argument(
        "--allow-extra-frontmatter",
        type=str,
        choices=["true", "false"],
        help="Allow extra frontmatter keys",
    )
    parser.add_argument(
        "--allow-extra-sections",
        type=str,
        choices=["true", "false"],
        help="Allow extra sections",
    )
    return parser.parse_args()


def parse_bool(value: str | None) -> bool | None:
    if value is None:
        return None
    return value.lower() == "true"


def update_config(updates: dict[str, Any]) -> None:
    config = {}
    if CONFIG_FILE.is_file():
        try:
            config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception as e:
            LOGGER.warning("Could not read existing config: %s", e)

    config.update(updates)

    with CONFIG_FILE.open("w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    if not is_initialized():
        LOGGER.error("Not initialized. Run initialize.py first.")
        return 1

    args = parse_args()
    updates = {}
    if args.reviews_dir is not None:
        updates["reviews_dir"] = args.reviews_dir

    allow_frontmatter = parse_bool(args.allow_extra_frontmatter)
    if allow_frontmatter is not None:
        updates["allow_extra_frontmatter"] = allow_frontmatter

    allow_sections = parse_bool(args.allow_extra_sections)
    if allow_sections is not None:
        updates["allow_extra_sections"] = allow_sections

    if not updates:
        LOGGER.info("No configuration options provided to update.")
        return 0

    update_config(updates)
    LOGGER.info("Successfully updated configuration: %s", updates)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
