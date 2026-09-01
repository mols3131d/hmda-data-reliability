"""Behavioral tests for generated documentation indexes."""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from scripts.generate_docs_indexes import generate_docs_indexes


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _read_tsv(path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            path_value = row.get("path")
            if path_value is None:
                raise AssertionError(f"missing path field: {row}")
            rows.append(
                {
                    "path": path_value,
                    "description": row.get("description") or "",
                }
            )
    return rows


@pytest.mark.component
def test_generate_projects_paths_and_frontmatter_descriptions(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    _write(docs / "README.md", "# Docs\n")
    _write(docs / "AGENTS.md", "# Agent guidance\n")
    _write(docs / "CLAUDE.md", "# Compatibility\n")
    _write(docs / "guide.md", "# Guide\n")
    _write(
        docs / "references" / "README.md",
        "---\ndescription: Reference docs.\n---\n# References\n",
    )
    _write(
        docs / "references" / "nested" / "deep.md",
        "---\ndescription: Deep reference.\n---\n# Deep\n",
    )

    assert generate_docs_indexes(docs) == []

    assert _read_tsv(docs / "INDEX.tsv") == [
        {"path": "guide.md", "description": ""},
        {"path": "references/", "description": "Reference docs."},
        {"path": "references/nested/", "description": ""},
        {"path": "references/nested/deep.md", "description": "Deep reference."},
    ]
    assert _read_tsv(docs / "references" / "INDEX.tsv") == [
        {"path": "nested/", "description": ""},
        {"path": "nested/deep.md", "description": "Deep reference."},
    ]
    assert not (docs / "references" / "nested" / "INDEX.tsv").exists()


@pytest.mark.component
def test_generate_omits_trailing_tab_for_empty_description(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    _write(docs / "guide.md", "# Guide\n")

    assert generate_docs_indexes(docs) == []

    index_path = docs / "INDEX.tsv"
    assert index_path.read_text(encoding="utf-8") == "path\tdescription\nguide.md\n"
    assert _read_tsv(index_path) == [{"path": "guide.md", "description": ""}]


@pytest.mark.component
def test_generate_omits_header_only_directory_index(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    _write(
        docs / "references" / "README.md",
        "---\ndescription: Reference docs.\n---\n# References\n",
    )

    assert generate_docs_indexes(docs) == []

    assert _read_tsv(docs / "INDEX.tsv") == [
        {"path": "references/", "description": "Reference docs."}
    ]
    assert not (docs / "references" / "INDEX.tsv").exists()


@pytest.mark.component
def test_generate_check_reports_drift_without_modifying_files(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    guide = docs / "guide.md"
    _write(guide, "---\ndescription: Initial.\n---\n# Guide\n")
    _write(docs / "references" / "nested" / "reference.md", "# Reference\n")
    generate_docs_indexes(docs)

    original_root_index = (docs / "INDEX.tsv").read_text(encoding="utf-8")
    _write(guide, "---\ndescription: Updated.\n---\n# Guide\n")
    (docs / "references" / "INDEX.tsv").unlink()
    stale = docs / "references" / "nested" / "INDEX.tsv"
    _write(stale, "path\tdescription\nold.md\tOld.\n")

    assert generate_docs_indexes(docs, check=True) == [
        "outdated: docs/INDEX.tsv",
        "missing: docs/references/INDEX.tsv",
        "stale: docs/references/nested/INDEX.tsv",
    ]
    assert (docs / "INDEX.tsv").read_text(encoding="utf-8") == original_root_index
    assert stale.exists()


@pytest.mark.component
def test_generate_rejects_non_string_description(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    _write(
        docs / "guide.md",
        "---\ndescription:\n  - invalid\n---\n# Guide\n",
    )

    with pytest.raises(ValueError, match="description must be a string"):
        generate_docs_indexes(docs)
