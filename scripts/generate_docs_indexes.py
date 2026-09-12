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
    """마크다운 문서 상단의 YAML 프런트매터를 파싱하여 반환한다.

    Args:
        path: 읽을 파일의 `Path`.

    Returns:
        파싱된 프런트매터 딕셔너리. 프런트매터가 없으면 빈 딕셔너리 `{}` 반환.

    Raises:
        ValueError: 프런트매터 닫는 구분자(`---`)가 누락되었거나 매핑이 아닌 경우.
    """
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
    """프런트매터 딕셔너리에서 'description' 값을 추출하고 공백을 정규화한다.

    Args:
        frontmatter: 파싱된 프런트매터 딕셔너리.
        path: 오류 메시지 표기용 파일 경로.

    Returns:
        정규화된 설명 문자열. 키가 없으면 빈 문자열 `""`.

    Raises:
        ValueError: 'description' 필드가 문자열 타입이 아닌 경우.
    """
    value = frontmatter.get("description")
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValueError(f"description must be a string: {path}")
    return " ".join(value.split())


def _frontmatter_description(path: Path) -> str:
    """단일 마크다운 파일에서 설명(description) 문자열을 읽어온다."""
    return _description(_frontmatter(path), path)


def _is_document(path: Path) -> bool:
    """주어진 경로가 문서 색인 대상 마크다운 파일인지 판별한다.

    제외 기준:
    - 디렉토리이거나 확장자가 `.md`가 아닌 파일
    - 특수 파일(`AGENTS.md`, `CLAUDE.md`, 숨김 파일)
    - 색인 파일 자체(`INDEX`로 시작하는 파일)
    - 템플릿/내부 파일(`__*__.md` 패턴)
    """
    name = path.name
    if not path.is_file() or path.suffix.lower() != ".md":
        return False
    if name in EXCLUDED_FILES or name.startswith("."):
        return False
    if name.upper().startswith("INDEX"):
        return False
    return not (name.startswith("__") and name.endswith("__.md"))


def _documents(directory: Path) -> list[Path]:
    """디렉토리 하위의 모든 유효한 문서 파일 목록을 정렬하여 반환한다."""
    return sorted(path for path in directory.rglob("*") if _is_document(path))


def _directory_description(directory: Path) -> str:
    """하위 디렉토리의 엔트리 파일(`README.md` 등)에서 디렉토리 설명을 추출한다."""
    for filename in DIRECTORY_ENTRY_FILES:
        entry = directory / filename
        if not entry.is_file():
            continue
        frontmatter = _frontmatter(entry)
        if frontmatter:
            return _description(frontmatter, entry)
    return ""


def _rows(directory: Path) -> list[tuple[str, str]]:
    """특정 디렉토리에 대한 TSV 색인 행 목록(`[(상대경로, 설명), ...]`)을 생성한다.

    수집 대상:
    1. 해당 디렉토리의 직계 및 간접 하위 디렉토리 (끝에 `/` 표기)
    2. 해당 디렉토리의 문서 파일들 (`README.md`, `index.md` 제외)

    Returns:
        상대 경로 기준 사전순으로 정렬된 `(path, description)` 튜플 리스트.
    """
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
    """디렉토리 색인 TSV 테이블 문자열을 렌더링한다.

    출력 포맷 계약:
    - 첫 줄은 `path\\tdescription\\n` 헤더.
    - 설명이 없는 행은 후행 탭 없이 `path\\n`만 출력(trailing tab 방지).
    """
    output = io.StringIO(newline="")
    writer = csv.writer(output, delimiter="\t", lineterminator="\n")
    writer.writerow(("path", "description"))
    for path, description in _rows(directory):
        writer.writerow((path, description) if description else (path,))
    return output.getvalue()


def _targets(docs_root: Path) -> list[Path]:
    """`INDEX.tsv` 파일이 생성되어야 하는 대상 디렉토리 목록을 결정한다.

    `INDEX_DEPTH` 설정(기본값 1)에 따라 `docs_root` 자신과
    그 직계 자식 디렉토리들까지만 인덱스 대상 디렉토리로 수집한다.
    """
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
        path for name in sorted(child_names) if (path := docs_root / name).is_dir()
    )
    return targets


def generate_docs_indexes(
    docs_root: Path = DOCS_ROOT,
    *,
    check: bool = False,
) -> list[str]:
    """Generate docs indexes or report drift when ``check`` is true."""
    if not docs_root.is_dir():
        raise NotADirectoryError(docs_root)

    repository_root = docs_root.parent
    drift: list[str] = []
    targets = {directory / INDEX_NAME for directory in _targets(docs_root)}

    for index_path in sorted(targets):
        desired = _render(index_path.parent)
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
    args = parser.parse_args(argv)

    try:
        drift = generate_docs_indexes(check=args.check)
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
