#!/usr/bin/env python3
"""코드 리뷰 summary 파일을 템플릿에서 생성한다."""

from __future__ import annotations

import argparse
import logging
from datetime import date
from pathlib import Path

from shared import ReviewFileCreationError, copy_template, validate_slug

LOGGER = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="코드 리뷰 summary 파일 생성")
    parser.add_argument("--reviews-dir", required=True, type=Path)
    parser.add_argument("--title-slug", required=True)
    return parser.parse_args()


def create_summary(reviews_dir: Path, title_slug: str) -> Path:
    validate_slug("title-slug", title_slug)
    destination = reviews_dir / f"{date.today():%Y%m%d}-{title_slug}" / "__summary__.md"
    return copy_template("__summary__.md", destination)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = parse_args()

    try:
        destination = create_summary(args.reviews_dir, args.title_slug)
    except ReviewFileCreationError as error:
        LOGGER.error("summary 생성 실패: %s", error, extra={"reason": str(error)})
        return 1

    LOGGER.info("summary 생성 완료: %s", destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
