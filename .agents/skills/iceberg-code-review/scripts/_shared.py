"""Common logic for review document generation scripts."""

import json
import re
from pathlib import Path
from typing import Any

SLUG_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
SKILL_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = SKILL_DIR / "user_data" / "config.json"


def is_initialized() -> bool:
    return CONFIG_FILE.is_file()


def load_config() -> dict[str, Any]:
    defaults = {
        "reviews_dir": "docs/reviews",
        "allow_extra_frontmatter": True,
        "allow_extra_sections": True,
    }

    if CONFIG_FILE.is_file():
        try:
            user_config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            if isinstance(user_config, dict):
                defaults.update(user_config)
        except Exception:
            pass

    return defaults


def get_reviews_dir(workspace_dir: Path | None = None) -> Path:
    """Returns the resolved reviews directory path."""
    rel_dir = load_config().get("reviews_dir", "docs/reviews").lstrip("/")
    return (workspace_dir / rel_dir) if workspace_dir else Path(rel_dir)


class ReviewFileCreationError(Exception):
    """Passes context related to review document creation failures."""


def validate_slug(name: str, value: str) -> None:
    if SLUG_PATTERN.fullmatch(value) is None:
        raise ReviewFileCreationError(
            f"INVALID_SLUG_FORMAT: {name} (allowed: a-z, 0-9, hyphens)"
        )


def copy_template(template_name: str, destination: Path) -> Path:
    template = SKILL_DIR / "templates" / template_name

    if not template.is_file():
        raise ReviewFileCreationError(f"TEMPLATE_NOT_FOUND: {template}")
    if destination.exists():
        raise ReviewFileCreationError(f"FILE_ALREADY_EXISTS: {destination}")

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(template.read_text(encoding="utf-8"), encoding="utf-8")
    return destination
