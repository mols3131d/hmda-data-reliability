"""Validate lightweight contracts for changed Inbox artifact roots."""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
GITHUB_WORK_RE = re.compile(
    r"^github-(?P<number>[1-9]\d*)-(?P<name>[a-z0-9]+(?:-[a-z0-9]+)*)$"
)
TIMED_ARTIFACT_RE = re.compile(r"^(?P<prefix>\d{2}-\d{2})-(?P<rest>.+)$")
SEQUENCED_ARTIFACT_RE = re.compile(r"^(?P<prefix>\d{2})-(?P<rest>.+)$")
TYPE_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
REQUIRED_FIELDS = ("type", "title", "description")


def _frontmatter_fields(path: Path) -> dict[str, str]:
    """Return top-level scalar-looking frontmatter fields from a Markdown file."""
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
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _has_value(value: str) -> bool:
    normalized = _unquote(value.strip())
    return normalized not in {"", "null", "Null", "NULL", "~"}


def _validate_root(
    path: Path,
    artifact_name: str,
    *,
    sequenced: bool,
) -> list[str]:
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


def _artifact_root_for_changed_path(
    repo_root: Path,
    changed_path: Path,
) -> tuple[Path, str, bool] | None:
    """Resolve a changed Inbox path to the standalone file or bundle README root."""
    try:
        relative = changed_path.relative_to("inbox")
    except ValueError:
        return None

    parts = relative.parts
    if len(parts) < 2:
        return None

    container = parts[0]
    if DATE_RE.fullmatch(container):
        sequenced = False
    elif GITHUB_WORK_RE.fullmatch(container):
        sequenced = True
    else:
        return None

    if len(parts) == 2 and changed_path.suffix == ".md":
        return repo_root / changed_path, changed_path.stem, sequenced

    bundle_name = parts[1]
    readme = repo_root / "inbox" / container / bundle_name / "README.md"
    if readme.is_file():
        return readme, bundle_name, sequenced
    return None


def _new_github_root_for_added_path(added_path: Path) -> tuple[str, str] | None:
    """Return GitHub work container and new top-level root for an added root path."""
    try:
        relative = added_path.relative_to("inbox")
    except ValueError:
        return None

    parts = relative.parts
    if len(parts) < 2 or not GITHUB_WORK_RE.fullmatch(parts[0]):
        return None

    if len(parts) == 2 and added_path.suffix == ".md":
        return parts[0], added_path.stem

    if len(parts) == 3 and parts[2] == "README.md":
        return parts[0], parts[1]

    return None


def _sequence_value(name: str) -> int | None:
    match = SEQUENCED_ARTIFACT_RE.fullmatch(name)
    if match is None:
        return None
    return int(match.group("prefix"))


def _validate_new_github_sequences(
    added_paths: list[str],
    *,
    repo_root: Path,
) -> list[str]:
    """Require newly added GitHub roots to append after the largest existing sequence."""
    added_roots: dict[str, set[str]] = defaultdict(set)
    for raw_path in added_paths:
        root = _new_github_root_for_added_path(Path(raw_path))
        if root is not None:
            container, root_name = root
            added_roots[container].add(root_name)

    errors: list[str] = []
    for container, new_names in added_roots.items():
        directory = repo_root / "inbox" / container
        if not directory.is_dir():
            continue

        existing_values: list[int] = []
        for child in directory.iterdir():
            if child.is_file() and child.suffix == ".md":
                name = child.stem
            elif child.is_dir():
                name = child.name
            else:
                continue
            if name in new_names:
                continue
            value = _sequence_value(name)
            if value is not None:
                existing_values.append(value)

        expected_start = max(existing_values, default=-1) + 1
        ordered_new = sorted(
            (value, name)
            for name in new_names
            if (value := _sequence_value(name)) is not None
        )
        expected_values = list(
            range(expected_start, expected_start + len(ordered_new))
        )
        actual_values = [value for value, _name in ordered_new]
        if actual_values == expected_values:
            continue

        expected_text = ", ".join(f"{value:02d}" for value in expected_values)
        actual_text = ", ".join(f"{value:02d}" for value in actual_values)
        errors.append(
            f"{directory}: new top-level sequence must append after the current maximum; "
            f"expected [{expected_text}], got [{actual_text}]"
        )

    return errors


def validate_changed_paths(
    paths: list[str],
    *,
    repo_root: Path,
    added_paths: list[str] | None = None,
) -> list[str]:
    """Validate artifact roots reached from changed paths and append-only new roots."""
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

    if added_paths:
        errors.extend(_validate_new_github_sequences(added_paths, repo_root=repo_root))
    return errors


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--added" in args:
        split_at = args.index("--added")
        paths = args[:split_at]
        added_paths = args[split_at + 1 :]
    else:
        paths = args
        added_paths = []

    errors = validate_changed_paths(
        paths,
        repo_root=Path.cwd(),
        added_paths=added_paths,
    )
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
