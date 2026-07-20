#!/usr/bin/env python3
"""Initializes the configuration for iceberg-code-review skill."""

import json
import logging
from typing import Any

from shared import CONFIG_FILE, is_initialized

LOGGER = logging.getLogger(__name__)

DEFAULT_CONFIG: dict[str, Any] = {
    "reviews_dir": "/docs/reviews",
    "allow_extra_frontmatter": True,
    "allow_extra_sections": True,
}


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    if is_initialized():
        LOGGER.info("Config is already initialized at %s", CONFIG_FILE)
        return 0

    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with CONFIG_FILE.open("w", encoding="utf-8") as f:
        json.dump(DEFAULT_CONFIG, f, indent=4)

    LOGGER.info("Successfully initialized config at %s", CONFIG_FILE)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
