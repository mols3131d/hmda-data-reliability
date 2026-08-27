#!/usr/bin/env python3
"""Generate repository-local ``docs/**/INDEX.tsv`` files."""

from __future__ import annotations

import argparse
import csv
import io
import sys
from collections import deque
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
DOCS_ROOT = ROOT / "docs"
INDEX_NAME = "INDEX.tsv"
HEADER = "path\tdescription\n"
DEFAULT_INDEX_DEPTH = 1
DEFAULT_DEPTH = -1
DEFAULT_DIRECTORY_ENTRY_FILES = ("README.md", "index.md")
EXCLUDED_FILES = {"AGENTS.md", "CLAUDE.md"}


def _frontmatter(path: Path) -> dict[str, Any]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "---":
        return {}

    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise ValueError(f"unterminated frontmatter: {path}") from exc

    data = yaml.safe_load("\n".join(lines[1:end])) or {}
    if not isinstance(data, dict):
        raise ValueError(f"frontmatter must be a mapping: {path}")
    return data


def _description(frontmatter: dict[str, Any], path: Path) -> str:
    value = frontmatter.get("description")
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValueError(f"description must be a string: {path}")
    return " ".join(value.split())


def _frontmatter_description(path: Path) -> str:
    return _description(_frontmatter(path), path)


def _is_document(path: Path) -> bool:
    name = path.name
    if not path.is_file() or path.suffix.lower() != ".md":
        return False
    if name in EXCLUDED_FILES or name.startswith("."):
        return False
    if name.upper().startswith("INDEX"):
        return False
    return not (name.startswith("__") and name.endswith("__.md"))


def _documents(directory: Path) -> list[Path]:
    return sorted(path for path in directory.rglob("*.md") if _is_document(path))


def _has_markdown_content(directory: Path) -> bool:
    return bool(_documents(directory))


def _route_children(directory: Path) -> list[Path]:
    return [
        child
        for child in sorted(directory.iterdir())
        if child.is_dir() and _has_markdown_content(child)
    ]


def _index_targets(docs_root: Path, index_depth: int) -> list[Path]:
    if index_depth < -1:
        raise ValueError("index_depth must be -1 or greater")

    targets: list[Path] = []
    queue = deque([(docs_root, 0)])
    while queue:
        directory, current_depth = queue.popleft()
        targets.append(directory)

        if index_depth != -1 and current_depth >= index_depth:
            continue
        queue.extend((child, current_depth + 1) for child in _route_children(directory))

    return targets


def _path_depth(path: Path, directory: Path) -> int:
    return len(path.relative_to(directory).parts) - 1


def _directory_description(
    directory: Path,
    entry_files: tuple[str, ...],
) -> str:
    for filename in entry_files:
        entry = directory / filename
        if not entry.is_file():
            continue
        frontmatter = _frontmatter(entry)
        if frontmatter:
            return _description(frontmatter, entry)
    return ""


def _rows(
    directory: Path,
    entry_files: tuple[str, ...],
    depth: int,
) -> list[tuple[str, str]]:
    if depth < -1:
        raise ValueError("depth must be -1 or greater")

    max_depth = None if depth == -1 else depth
    documents = _documents(directory)
    directories: set[Path] = set()

    for document in documents:
        for parent in document.parents:
            if parent == directory:
                break
            directories.add(parent)

    rows = [
        (
            f"{path.relative_to(directory).as_posix()}/",
            _directory_description(path, entry_files),
        )
        for path in directories
        if max_depth is None or _path_depth(path, directory) <= max_depth
    ]
    rows.extend(
        (
            path.relative_to(directory).as_posix(),
            _frontmatter_description(path),
        )
        for path in documents
        if path.name not in entry_files
        and (max_depth is None or _path_depth(path, directory) <= max_depth)
    )
    return sorted(rows, key=lambda row: row[0])


def _render(
    directory: Path,
    entry_files: tuple[str, ...],
    depth: int,
) -> str:
    output = io.StringIO(newline="")
    writer = csv.writer(output, delimiter="\t", lineterminator="\n")
    writer.writerow(("path", "description"))
    writer.writerows(_rows(directory, entry_files, depth))
    return output.getvalue()


def generate_docs_indexes(
    docs_root: Path = DOCS_ROOT,
    *,
    check: bool = False,
    index_depth: int = DEFAULT_INDEX_DEPTH,
    depth: int = DEFAULT_DEPTH,
    directory_entry_files: tuple[str, ...] | list[str] = DEFAULT_DIRECTORY_ENTRY_FILES,
) -> list[str]:
    """Generate docs indexes or report drift when ``check`` is true."""
    if not docs_root.is_dir():
        raise NotADirectoryError(docs_root)
    if index_depth < -1:
        raise ValueError("index_depth must be -1 or greater")
    if depth < -1:
        raise ValueError("depth must be -1 or greater")

    entry_files = tuple(directory_entry_files)
    if not entry_files:
        raise ValueError("directory_entry_files must not be empty")

    repository_root = docs_root.parent
    drift: list[str] = []
    targets = {
        directory / INDEX_NAME for directory in _index_targets(docs_root, index_depth)
    }

    for index_path in sorted(targets):
        desired = _render(index_path.parent, entry_files, depth)
        current = (
            index_path.read_text(encoding="utf-8") if index_path.exists() else None
        )
        relative = index_path.relative_to(repository_root).as_posix()

        if desired == HEADER:
            if current is not None:
                if check:
                    drift.append(f"stale: {relative}")
                else:
                    index_path.unlink()
            continue
        if current == desired:
            continue

        if check:
            state = "outdated" if current is not None else "missing"
            drift.append(f"{state}: {relative}")
        else:
            index_path.write_text(desired, encoding="utf-8")

    for index_path in sorted(docs_root.rglob(INDEX_NAME)):
        if index_path in targets:
            continue
        relative = index_path.relative_to(repository_root).as_posix()
        if check:
            drift.append(f"stale: {relative}")
        else:
            index_path.unlink()

    return drift


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="report index drift without modifying files",
    )
    parser.add_argument(
        "--index-depth",
        type=int,
        default=DEFAULT_INDEX_DEPTH,
        help="maximum depth where INDEX files are materialized (0=root, -1=unlimited)",
    )
    parser.add_argument(
        "--depth",
        type=int,
        default=DEFAULT_DEPTH,
        help="maximum subtree depth included in each INDEX (0=current, -1=unlimited)",
    )
    parser.add_argument(
        "--directory-entry-files",
        nargs="+",
        default=list(DEFAULT_DIRECTORY_ENTRY_FILES),
        help="ordered entrypoint filenames that provide directory descriptions",
    )
    args = parser.parse_args(argv)

    if args.index_depth < -1:
        parser.error("--index-depth must be -1 or greater")
    if args.depth < -1:
        parser.error("--depth must be -1 or greater")

    try:
        drift = generate_docs_indexes(
            check=args.check,
            index_depth=args.index_depth,
            depth=args.depth,
            directory_entry_files=args.directory_entry_files,
        )
    except (OSError, ValueError, yaml.YAMLError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    if drift:
        for item in drift:
            print(item, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
