#!/usr/bin/env python3
"""리뷰 문서에 남은 YAML·Markdown 주석을 검증한다."""

from __future__ import annotations

import argparse
import logging
import re
from pathlib import Path

LOGGER = logging.getLogger(__name__)
FRONTMATTER_PATTERN = re.compile(r"\A---\n(?P<yaml>.*?)\n---\n", re.DOTALL)
BLOCK_SCALAR_PATTERN = re.compile(
    r":\s*[>|](?:[1-9][+-]?|[+-][1-9]?)?\s*$"
)
FENCE_PATTERN = re.compile(r"^ {0,3}(?P<fence>`{3,}|~{3,})(?P<rest>.*)$")
HTML_COMMENT_PATTERN = re.compile(r"<!--[\s\S]*?-->")


class CommentValidationError(Exception):
    """주석 검증 실패를 전달한다."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="리뷰 문서 잔여 주석 검증")
    parser.add_argument("review_file_path", type=Path)
    return parser.parse_args()


def count_comments(markdown_file: Path) -> int:
    if not markdown_file.is_file():
        raise CommentValidationError(f"파일이 없습니다: {markdown_file}")

    source = markdown_file.read_text()
    frontmatter = FRONTMATTER_PATTERN.match(source)
    if frontmatter is None:
        return count_markdown_comments(source)

    yaml_comments = count_yaml_comments(frontmatter.group("yaml"))
    markdown_comments = count_markdown_comments(source[frontmatter.end() :])
    return yaml_comments + markdown_comments


def has_no_comments(markdown_file: Path) -> bool:
    return count_comments(markdown_file) == 0


def count_yaml_comments(source: str) -> int:
    count = 0
    block_indent: int | None = None

    for line in source.splitlines():
        indent = len(line) - len(line.lstrip(" "))
        if block_indent is not None:
            if not line.strip() or indent > block_indent:
                continue
            block_indent = None

        comment_index = _yaml_comment_index(line)
        content = line if comment_index is None else line[:comment_index]
        if comment_index is not None:
            count += 1
        if BLOCK_SCALAR_PATTERN.search(content):
            block_indent = indent

    return count


def count_markdown_comments(source: str) -> int:
    visible_lines: list[str] = []
    fence_character: str | None = None
    fence_length = 0

    for line in source.splitlines(keepends=True):
        fence = FENCE_PATTERN.match(line)
        if fence_character is not None:
            if (
                fence
                and fence.group("fence")[0] == fence_character
                and len(fence.group("fence")) >= fence_length
                and not fence.group("rest").strip()
            ):
                fence_character = None
            visible_lines.append("\n" if line.endswith("\n") else "")
            continue

        if fence:
            marker = fence.group("fence")
            fence_character = marker[0]
            fence_length = len(marker)
            visible_lines.append("\n" if line.endswith("\n") else "")
        elif line.startswith(("    ", "\t")):
            visible_lines.append("\n" if line.endswith("\n") else "")
        else:
            visible_lines.append(_mask_inline_code(line))

    return len(HTML_COMMENT_PATTERN.findall("".join(visible_lines)))


def _yaml_comment_index(line: str) -> int | None:
    single_quoted = False
    double_quoted = False
    index = 0

    while index < len(line):
        character = line[index]
        if character == "'" and not double_quoted:
            if single_quoted and index + 1 < len(line) and line[index + 1] == "'":
                index += 2
                continue
            single_quoted = not single_quoted
        elif character == '"' and not single_quoted:
            escaped = index > 0 and line[index - 1] == "\\"
            if not escaped:
                double_quoted = not double_quoted
        elif character == "#" and not single_quoted and not double_quoted:
            if index == 0 or line[index - 1].isspace():
                return index
        index += 1

    return None


def _mask_inline_code(line: str) -> str:
    masked = list(line)
    index = 0

    while index < len(line):
        if line[index] != "`":
            index += 1
            continue

        end_of_opening = index
        while end_of_opening < len(line) and line[end_of_opening] == "`":
            end_of_opening += 1
        marker = line[index:end_of_opening]
        closing = line.find(marker, end_of_opening)
        if closing == -1:
            index = end_of_opening
            continue

        for masked_index in range(index, closing + len(marker)):
            masked[masked_index] = " "
        index = closing + len(marker)

    return "".join(masked)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = parse_args()

    try:
        count = count_comments(args.review_file_path)
    except CommentValidationError as error:
        LOGGER.error("주석 검증 실패: %s", error, extra={"reason": str(error)})
        return 1

    if count:
        LOGGER.error("주석 검증 실패: 주석 %d개 남음", count, extra={"count": count})
        return 1

    LOGGER.info("주석 검증 완료: %s", args.review_file_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
