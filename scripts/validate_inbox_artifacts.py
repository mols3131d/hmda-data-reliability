"""Validate lightweight contracts for changed Inbox artifact roots."""

from __future__ import annotations

import re
import sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ARTIFACT_RE = re.compile(r"^(?P<time>\d{2}-\d{2})-(?P<rest>.+)$")
TYPE_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
REQUIRED_FIELDS = ("type", "title", "description")


def _frontmatter_fields(path: Path) -> dict[str, str]:
    """Return top-level scalar-looking frontmatter fields from a Markdown file."""
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("missing YAML frontmatter opening delimiter")

    try:
        end = next(
            index
            for index, line in enumerate(lines[1:], 1)
            if line.strip() == "---"
        )
    except StopIteration as exc:
        raise ValueError("missing YAML frontmatter closing delimiter") from exc

    fields: dict[str, str] = {}
    for line in lines[1:end]:
        if not line or line[0].isspace() or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        if key:
            fields[key] = value.strip()
    return fields


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _has_value(value: str) -> bool:
    normalized = _unquote(value.strip())
    return normalized not in {"", "null", "Null", "NULL", "~"}


def _validate_root(path: Path, artifact_name: str) -> list[str]:
    errors: list[str] = []
    try:
        fields = _frontmatter_fields(path)
    except ValueError as exc:
        return [f"{path}: {exc}"]

    for field in REQUIRED_FIELDS:
        value = fields.get(field)
        if value is None or not _has_value(value):
            errors.append(
                f"{path}: required frontmatter field '{field}' is missing or empty"
            )

    raw_type = fields.get("type", "")
    artifact_type = _unquote(raw_type.strip())
    if artifact_type and not TYPE_RE.fullmatch(artifact_type):
        errors.append(
            f"{path}: frontmatter type must be lowercase kebab-case: "
            f"{artifact_type!r}"
        )
        return errors

    match = ARTIFACT_RE.fullmatch(artifact_name)
    if match is None:
        errors.append(f"{path}: artifact name must start with HH-MM-")
        return errors

    hour_text, minute_text = match.group("time").split("-", 1)
    if not (0 <= int(hour_text) <= 23 and 0 <= int(minute_text) <= 59):
        errors.append(f"{path}: artifact time must be a valid HH-MM value")

    if artifact_type:
        expected_prefix = f"{match.group('time')}-{artifact_type}-"
        if not artifact_name.startswith(expected_prefix):
            errors.append(
                f"{path}: artifact name must start with {expected_prefix!r} "
                "to match frontmatter type"
            )
    return errors


def _artifact_root_for_changed_path(
    repo_root: Path,
    changed_path: Path,
) -> tuple[Path, str] | None:
    """Resolve a changed Inbox path to the standalone file or bundle README root."""
    try:
        relative = changed_path.relative_to("inbox")
    except ValueError:
        return None

    parts = relative.parts
    if len(parts) < 2 or not DATE_RE.fullmatch(parts[0]):
        return None

    if len(parts) == 2 and changed_path.suffix == ".md":
        return repo_root / changed_path, changed_path.stem

    bundle_name = parts[1]
    if not ARTIFACT_RE.fullmatch(bundle_name):
        return None

    readme = repo_root / "inbox" / parts[0] / bundle_name / "README.md"
    if readme.is_file():
        return readme, bundle_name
    return None


def validate_changed_paths(paths: list[str], *, repo_root: Path) -> list[str]:
    """Validate only artifact roots reached from the supplied changed paths."""
    errors: list[str] = []
    seen_roots: set[Path] = set()

    for raw_path in paths:
        changed_path = Path(raw_path)
        root = _artifact_root_for_changed_path(repo_root, changed_path)
        if root is None:
            continue
        root_path, artifact_name = root
        if root_path in seen_roots or not root_path.is_file():
            continue
        seen_roots.add(root_path)
        errors.extend(_validate_root(root_path, artifact_name))

    return errors


def main(argv: list[str] | None = None) -> int:
    paths = list(sys.argv[1:] if argv is None else argv)
    errors = validate_changed_paths(paths, repo_root=Path.cwd())
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
