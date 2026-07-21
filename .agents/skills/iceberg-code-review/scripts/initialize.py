#!/usr/bin/env python3
"""Initializes the configuration for iceberg-code-review skill."""

import json
import logging
import shutil
import subprocess
from typing import Any

from _shared import CONFIG_FILE, is_initialized

LOGGER = logging.getLogger(__name__)

DEFAULT_CONFIG: dict[str, Any] = {
    "reviews_dir": "docs/reviews",
    "allow_extra_frontmatter": True,
    "allow_extra_sections": True,
    "RUMDL_EXEC": None,
}


def _update_rumdl_exec(config: dict[str, Any]) -> None:
    """rumdl 설치 여부를 확인하고 config에 경로를 기록한다."""
    if shutil.which("uv"):
        try:
            out = subprocess.check_output(["uv", "tool", "list"], text=True)
            if "rumdl" in out:
                config["RUMDL_EXEC"] = "uv tool run rumdl"
                LOGGER.info("Found rumdl via uv tool")
                return
        except (subprocess.CalledProcessError, OSError):
            pass

    if rumdl_path := shutil.which("rumdl"):
        config["RUMDL_EXEC"] = rumdl_path
        LOGGER.info("Found rumdl at %s", rumdl_path)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    config_data = DEFAULT_CONFIG.copy()

    if is_initialized():
        LOGGER.info("Config is already initialized at %s", CONFIG_FILE)
        try:
            with CONFIG_FILE.open("r", encoding="utf-8") as f:
                user_config = json.load(f)
                if isinstance(user_config, dict):
                    config_data.update(user_config)
        except Exception as exc:
            LOGGER.warning("Failed to read existing config: %s", exc)

    _update_rumdl_exec(config_data)

    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with CONFIG_FILE.open("w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=4)

    LOGGER.info("Successfully updated config at %s", CONFIG_FILE)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
