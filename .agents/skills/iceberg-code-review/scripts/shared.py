"""리뷰 문서 생성 스크립트의 공통 로직."""

from pathlib import Path
import re
import shutil


SLUG_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
PLACEHOLDER_PATTERN = re.compile(r"{{[A-Za-z가-힣_]+}}")
SKILL_DIR = Path(__file__).resolve().parent.parent


class ReviewFileCreationError(Exception):
    """리뷰 문서 생성 실패와 관련 context를 전달한다."""


def validate_slug(name: str, value: str) -> None:
    if SLUG_PATTERN.fullmatch(value) is None:
        raise ReviewFileCreationError(
            f"{name}은 소문자 영숫자와 하이픈만 허용합니다."
        )


def copy_template(template_name: str, destination: Path) -> Path:
    template = SKILL_DIR / "templates" / template_name

    if not template.is_file():
        raise ReviewFileCreationError(f"템플릿이 없습니다: {template}")
    if destination.exists():
        raise ReviewFileCreationError(f"파일이 이미 있습니다: {destination}")

    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(template, destination)
    return destination


def count_placeholders(markdown_file: Path) -> int:
    """Markdown 파일에 남은 `{{...}}` placeholder 수를 반환한다."""
    return len(PLACEHOLDER_PATTERN.findall(markdown_file.read_text()))


def has_no_placeholders(markdown_file: Path) -> bool:
    """미작성 placeholder가 없으면 True를 반환한다."""
    return count_placeholders(markdown_file) == 0
