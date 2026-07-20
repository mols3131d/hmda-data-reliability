#!/usr/bin/env python3
"""코드 리뷰 finding 파일을 템플릿에서 생성한다."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from shared import ReviewFileCreationError, copy_template, validate_slug

LOGGER = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="코드 리뷰 finding 파일 생성")
    parser.add_argument("--summary-file", required=True, type=Path)
    parser.add_argument("--domain", required=True)
    parser.add_argument("--finding", required=True)
    return parser.parse_args()


def create_finding(summary_file: Path, domain: str, finding: str) -> Path:
    for name, value in (("domain", domain), ("finding", finding)):
        validate_slug(name, value)

    if not summary_file.is_file():
        raise ReviewFileCreationError(f"summary 파일이 없습니다: {summary_file}")

    destination = summary_file.parent / f"{domain}-{finding}.md"
    return copy_template("{{domain}}-{{finding}}.md", destination)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = parse_args()

    try:
        destination = create_finding(args.summary_file, args.domain, args.finding)
    except ReviewFileCreationError as error:
        LOGGER.error("finding 생성 실패: %s", error, extra={"reason": str(error)})
        return 1

    LOGGER.info("finding 생성 완료: %s", destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
