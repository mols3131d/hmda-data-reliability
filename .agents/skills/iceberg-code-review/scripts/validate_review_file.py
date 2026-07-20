#!/usr/bin/env python3
"""생성된 코드 리뷰 문서의 필수 구조와 내용을 검증한다."""

from __future__ import annotations

import argparse
import logging
import re
from pathlib import Path

LOGGER = logging.getLogger(__name__)
FRONTMATTER_PATTERN = re.compile(r"\A---\n(?P<metadata>.*?)\n---\n", re.DOTALL)
HEADING_PATTERN = re.compile(r"^## (?P<name>.+)$", re.MULTILINE)
REQUIRED_STRUCTURE = {
    "code-review-summary": (
        ("title", "date", "type"),
        ("Summary", "Findings"),
    ),
    "code-review-finding": (
        ("title", "description", "type", "severity", "status"),
        ("Summary", "Observation", "Impact", "Recommendation", "Verification"),
    ),
}


class ReviewFileValidationError(Exception):
    """리뷰 문서 구조 검증 실패를 전달한다."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="코드 리뷰 문서 구조 검증")
    parser.add_argument("review_file_path", type=Path)
    return parser.parse_args()


def validate_review_file(review_file_path: Path) -> None:
    if not review_file_path.is_file():
        raise ReviewFileValidationError(f"파일이 없습니다: {review_file_path}")

    content = review_file_path.read_text()
    frontmatter = FRONTMATTER_PATTERN.match(content)
    if frontmatter is None:
        raise ReviewFileValidationError("front matter가 없습니다.")

    metadata = _parse_metadata(frontmatter.group("metadata"))
    document_type = metadata.get("type")
    if document_type not in REQUIRED_STRUCTURE:
        raise ReviewFileValidationError(f"지원하지 않는 type입니다: {document_type}")

    required_metadata, required_sections = REQUIRED_STRUCTURE[document_type]
    missing_metadata = [name for name in required_metadata if not metadata.get(name)]
    if missing_metadata:
        raise ReviewFileValidationError(
            f"필수 metadata가 없습니다: {', '.join(missing_metadata)}"
        )

    body = content[frontmatter.end() :]
    sections = _parse_sections(body)
    if tuple(sections) != required_sections:
        raise ReviewFileValidationError(
            f"필수 section 순서가 다릅니다: {', '.join(required_sections)}"
        )

    empty_sections = [name for name, section in sections.items() if not section.strip()]
    if empty_sections:
        raise ReviewFileValidationError(
            f"빈 section이 있습니다: {', '.join(empty_sections)}"
        )


def _parse_metadata(source: str) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for line in source.splitlines():
        if ":" not in line:
            continue
        name, value = line.split(":", 1)
        metadata[name.strip()] = value.strip().strip("'\"")
    return metadata


def _parse_sections(body: str) -> dict[str, str]:
    matches = list(HEADING_PATTERN.finditer(body))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        sections[match.group("name")] = body[match.end() : end]
    return sections


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = parse_args()

    try:
        validate_review_file(args.review_file_path)
    except ReviewFileValidationError as error:
        LOGGER.error("리뷰 문서 검증 실패: %s", error, extra={"reason": str(error)})
        return 1

    LOGGER.info("리뷰 문서 검증 완료: %s", args.review_file_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
