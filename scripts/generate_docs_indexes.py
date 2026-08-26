#!/usr/bin/env python3
"""Generate repository-local ``docs/**/INDEX.tsv`` files."""

from __future__ import annotations

import argparse
import csv
import io
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
DOCS_ROOT = ROOT / "docs"
INDEX_NAME = "INDEX.tsv"
HEADER = "path\tdescription\n"
INDEX_DEPTH = 1
DIRECTORY_ENTRY_FILES = ("README.md", "index.md")
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
    return sorted(path for path in directory.rglob("*") if _is_document(path))


def _directory_description(directory: Path) -> str:
    for filename in DIRECTORY_ENTRY_FILES:
        entry = directory / filename
        if not entry.is_file():
            continue
        frontmatter = _frontmatter(entry)
        if frontmatter:
            return _description(frontmatter, entry)
    return ""


def _rows(directory: Path) -> list[tuple[str, str]]:
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
            _directory_description(path),
        )
        for path in directories
    ]
    rows.extend(
        (
            path.relative_to(directory).as_posix(),
            _frontmatter_description(path),
        )
        for path in documents
        if path.name not in DIRECTORY_ENTRY_FILES
    )
    return sorted(rows, key=lambda row: row[0])


def _render(directory: Path) -> str:
    output = io.StringIO(newline="")
    writer = csv.writer(output, delimiter="\t", lineterminator="\n")
    writer.writerow(("path", "description"))
    writer.writerows(_rows(directory))
    return output.getvalue()


def _targets(docs_root: Path) -> list[Path]:
    targets = [docs_root]
    if INDEX_DEPTH == 0:
        return targets

    documents = _documents(docs_root)
    child_names = {
        document.relative_to(docs_root).parts[0]
        for document in documents
        if len(document.relative_to(docs_root).parts) > 1
    }
    targets.extend(
        path
        for name in sorted(child_names)
        if (path := docs_root / name).is_dir()
    )
    return targets


def generate(docs_root: Path = DOCS_ROOT, *, check: bool = False) -> list[str]:
    if not docs_root.is_dir():
        raise NotADirectoryError(docs_root)

    repository_root = docs_root.parent
    drift: list[str] = []
    targets = {directory / INDEX_NAME for directory in _targets(docs_root)}

    for index_path in sorted(targets):
        desired = _render(index_path.parent)
        current = index_path.read_text(encoding="utf-8") if index_path.exists() else None
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
    args = parser.parse_args(argv)

    try:
        drift = generate(check=args.check)
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
