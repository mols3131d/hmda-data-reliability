#!/usr/bin/env python3
"""문서 frontmatter를 읽어 ADR과 backlog 인덱스를 갱신한다."""

from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Final

LOGGER = logging.getLogger(__name__)

ROOT: Final[Path] = Path(__file__).resolve().parents[1]


class IndexTarget:
    """인덱싱 대상 디렉터리 설정."""

    def __init__(self, source_dir: Path, index_file: Path, fields: list[str], sort_key: str) -> None:
        self.source_dir = source_dir
        self.index_file = index_file
        self.fields = fields
        self.sort_key = sort_key


TARGETS: Final[list[IndexTarget]] = [
    IndexTarget(
        source_dir=ROOT / "docs/adrs",
        index_file=ROOT / "docs/adrs/INDEX.csv",
        fields=["id", "title", "status", "description", "date"],
        sort_key="id",
    ),
    IndexTarget(
        source_dir=ROOT / "docs/adrs/archive",
        index_file=ROOT / "docs/adrs/archive/INDEX.csv",
        fields=["id", "title", "status", "description", "date"],
        sort_key="id",
    ),
    IndexTarget(
        source_dir=ROOT / "docs/backlogs",
        index_file=ROOT / "docs/backlogs/INDEX.csv",
        fields=["title", "description"],
        sort_key="title",
    ),
]

SKIP_NAMES: Final[set[str]] = {"README.md", "TEMPLATE.md", "INDEX.md"}
SKIP_SUFFIXES: Final[tuple[str, ...]] = (".original.md",)
ARCHIVED_ADR_STATUSES: Final[set[str]] = {"deprecated", "superseded", "rejected"}


def parse_frontmatter(path: Path) -> dict[str, str | list[str]]:
    """Markdown frontmatter의 단순 key/value와 list 값을 파싱한다."""
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "---":
        return {}

    result: dict[str, str | list[str]] = {}
    current_key: str | None = None

    for line in lines[1:]:
        if line == "---":
            break

        stripped = line.strip()
        if not stripped:
            continue

        if stripped.startswith("- ") and current_key:
            values = result.setdefault(current_key, [])
            if isinstance(values, list):
                values.append(clean_value(stripped[2:]))
            continue

        key, separator, value = stripped.partition(":")
        if not separator:
            current_key = None
            continue

        current_key = key
        raw_value = value.strip()
        result[key] = [] if raw_value == "" else clean_value(raw_value)

    return result


def clean_value(value: str) -> str:
    """따옴표로 감싼 YAML scalar 값을 CSV용 문자열로 정리한다."""
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def csv_value(value: str | list[str] | None) -> str:
    """frontmatter 값을 CSV cell 문자열로 변환한다."""
    if value is None:
        return ""
    if isinstance(value, list):
        return ";".join(value)
    return value


def should_index(path: Path) -> bool:
    """INDEX 생성 대상 Markdown 파일인지 판단한다."""
    if path.name in SKIP_NAMES:
        return False
    return not any(path.name.endswith(suffix) for suffix in SKIP_SUFFIXES)


def build_row(frontmatter: dict[str, str | list[str]], target: IndexTarget) -> dict[str, str]:
    """문서 하나를 CSV row로 변환한다."""
    return {field: csv_value(frontmatter.get(field)) for field in target.fields}


def archive_inactive_adrs() -> int:
    """archive 대상 ADR을 인덱싱 전에 archive 디렉터리로 이동한다."""
    source_dir = ROOT / "docs/adrs"
    archive_dir = source_dir / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)

    moved_count = 0
    paths = sorted(path for path in source_dir.glob("*.md") if should_index(path))
    for path in paths:
        status = csv_value(parse_frontmatter(path).get("status"))
        if status not in ARCHIVED_ADR_STATUSES:
            continue

        target_path = archive_dir / path.name
        if target_path.exists():
            raise FileExistsError(f"archive 대상 파일이 이미 존재합니다: {target_path}")

        path.rename(target_path)
        moved_count += 1
        LOGGER.info(
            "ADR archive 이동 완료",
            extra={"source_file": str(path), "target_file": str(target_path), "status": status},
        )

    return moved_count


def write_index(target: IndexTarget) -> int:
    """대상 디렉터리의 INDEX.csv를 갱신하고 row 수를 반환한다."""
    target.index_file.parent.mkdir(parents=True, exist_ok=True)
    paths = sorted(path for path in target.source_dir.glob("*.md") if should_index(path))
    rows = []
    for path in paths:
        frontmatter = parse_frontmatter(path)
        if frontmatter:
            rows.append(build_row(frontmatter, target))

    rows.sort(key=lambda row: row[target.sort_key])

    with target.index_file.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=target.fields)
        writer.writeheader()
        writer.writerows(rows)

    LOGGER.info(
        "문서 인덱스 갱신 완료",
        extra={"index_file": str(target.index_file), "row_count": len(rows)},
    )
    return len(rows)


def main() -> int:
    """모든 문서 인덱스를 갱신한다."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    archive_inactive_adrs()
    for target in TARGETS:
        write_index(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
