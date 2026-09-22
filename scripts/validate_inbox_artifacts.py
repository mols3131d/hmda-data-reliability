"""Validate lightweight contracts for changed Inbox artifact roots."""

from __future__ import annotations

import re
import sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
BRANCH_WORK_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-[a-z0-9]+(?:-[a-z0-9]+)*$")
GITHUB_WORK_RE = re.compile(
    r"^github-(?P<number>[1-9]\d*)-(?P<name>[a-z0-9]+(?:-[a-z0-9]+)*)$"
)
TIMED_ARTIFACT_RE = re.compile(r"^(?P<prefix>\d{2}-\d{2})-(?P<rest>.+)$")
SEQUENCED_ARTIFACT_RE = re.compile(r"^(?P<prefix>\d{2})-(?P<rest>.+)$")
TYPE_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
REQUIRED_FIELDS = ("type", "title", "description")


def _frontmatter_fields(path: Path) -> dict[str, str]:
    """Return top-level scalar-looking frontmatter fields from a Markdown file.

    Extracts key-value lines located between YAML delimiters (`---`). Ignores indented
    child structures or blank lines.

    Args:
        path: Path to the markdown file to parse.

    Returns:
        A dictionary of raw string key-value pairs.

    Raises:
        ValueError: If opening or closing `---` delimiters are missing.
    """
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("missing YAML frontmatter opening delimiter")

    try:
        end = next(
            index for index, line in enumerate(lines[1:], 1) if line.strip() == "---"
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
    """Strip matching leading and trailing single or double quotes."""
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _has_value(value: str) -> bool:
    """Return True if a frontmatter field contains a meaningful non-null value."""
    normalized = _unquote(value.strip())
    return normalized not in {"", "null", "Null", "NULL", "~"}


def _validate_root(
    path: Path,
    artifact_name: str,
    *,
    sequenced: bool,
) -> list[str]:
    """Validate schema, naming prefix, and frontmatter consistency.

    Rules:
    - Required fields: `type`, `title`, `description` must be non-empty.
    - Type must match lowercase kebab-case.
    - Naming convention:
      - Sequenced container: must start with `NN-` (two digits).
      - Timed container: must start with `HH-MM-`, with valid hour (0-23)
        and minute (0-59), and must be prefixed with `${HH-MM}-${type}-`.

    Args:
        path: File path of the artifact markdown or bundle README.
        artifact_name: Name (or stem) of the artifact being evaluated.
        sequenced: True if in sequenced container, False if date-ordered.

    Returns:
        List of formatted error messages, or empty list if valid.
    """
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
            f"{path}: frontmatter type must be lowercase kebab-case: {artifact_type!r}"
        )
        return errors

    pattern = SEQUENCED_ARTIFACT_RE if sequenced else TIMED_ARTIFACT_RE
    match = pattern.fullmatch(artifact_name)
    if match is None:
        required_prefix = "NN-" if sequenced else "HH-MM-"
        errors.append(f"{path}: artifact name must start with {required_prefix}")
        return errors

    prefix = match.group("prefix")
    if sequenced:
        return errors

    hour_text, minute_text = prefix.split("-", 1)
    if not (0 <= int(hour_text) <= 23 and 0 <= int(minute_text) <= 59):
        errors.append(f"{path}: artifact time must be a valid HH-MM value")

    if artifact_type:
        expected_prefix = f"{prefix}-{artifact_type}-"
        if not artifact_name.startswith(expected_prefix):
            errors.append(
                f"{path}: artifact name must start with {expected_prefix!r} "
                "to match frontmatter type"
            )
    return errors


def _is_sequenced_container(container: str) -> bool | None:
    """Determine container mode: False for date, True for sequenced, None if invalid."""
    if DATE_RE.fullmatch(container):
        return False
    if BRANCH_WORK_RE.fullmatch(container) or GITHUB_WORK_RE.fullmatch(container):
        return True
    return None


def _artifact_root_for_changed_path(
    repo_root: Path,
    changed_path: Path,
) -> tuple[Path, str, bool] | None:
    """Resolve a changed Inbox path to the standalone file or bundle README root.

    Identifies whether a modified file in `inbox/` represents a standalone artifact
    or a turn/document within an artifact bundle (whose canonical root is `README.md`).
    A sequenced work-unit root `README.md` is navigation metadata, not an artifact root.

    Args:
        repo_root: Path to repository root.
        changed_path: Relative or absolute path to a changed inbox file.

    Returns:
        Tuple of `(canonical_root_path, artifact_name, is_sequenced)` or None if
        the path does not point to a valid inbox artifact.
    """
    try:
        relative = changed_path.relative_to("inbox")
    except ValueError:
        return None

    parts = relative.parts
    if len(parts) < 2:
        return None

    container = parts[0]
    sequenced = _is_sequenced_container(container)
    if sequenced is None:
        return None

    if len(parts) == 2 and sequenced and changed_path.name == "README.md":
        return None

    if len(parts) == 2 and changed_path.suffix == ".md":
        return repo_root / changed_path, changed_path.stem, sequenced

    bundle_name = parts[1]
    readme = repo_root / "inbox" / container / bundle_name / "README.md"
    if readme.is_file():
        return readme, bundle_name, sequenced
    return None


def validate_changed_paths(paths: list[str], *, repo_root: Path) -> list[str]:
    """Validate only artifact roots reached from the supplied changed paths.

    Deduplicates canonical roots so multiple edits inside a single bundle only
    trigger one validation pass on its README.

    Args:
        paths: List of file path strings reported as changed.
        repo_root: Repository root directory.

    Returns:
        List of all validation error strings encountered across inspected roots.
    """
    errors: list[str] = []
    seen_roots: set[Path] = set()

    for raw_path in paths:
        changed_path = Path(raw_path)
        root = _artifact_root_for_changed_path(repo_root, changed_path)
        if root is None:
            continue
        root_path, artifact_name, sequenced = root
        if root_path in seen_roots or not root_path.is_file():
            continue
        seen_roots.add(root_path)
        errors.extend(_validate_root(root_path, artifact_name, sequenced=sequenced))

    return errors


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for changed inbox artifact validation."""
    paths = list(sys.argv[1:] if argv is None else argv)
    errors = validate_changed_paths(paths, repo_root=Path.cwd())
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
