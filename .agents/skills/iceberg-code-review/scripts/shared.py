"""Common logic for review document generation scripts."""

import re
from pathlib import Path

SLUG_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
SKILL_DIR = Path(__file__).resolve().parent.parent


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
