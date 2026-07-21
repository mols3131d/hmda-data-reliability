import re
from pathlib import Path
from typing import Any

from _schema import TEMPLATE_SCHEMAS
from _shared import load_config

try:
    import yaml

    HAS_YAML = True
except ImportError:
    HAS_YAML = False

PLACEHOLDER_PATTERN = re.compile(r"{{[A-Za-z_]+}}")
FRONTMATTER_PATTERN = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
HEADING_PATTERN = re.compile(r"^## (?P<name>.+)$", re.MULTILINE)
HTML_COMMENT_PATTERN = re.compile(r"<!--[\s\S]*?-->")


class FrontmatterParseError(Exception):
    """잘못된 YAML frontmatter 파싱 실패를 나타낸다."""


class FrontmatterTypeError(Exception):
    """YAML frontmatter root가 mapping이 아님을 나타낸다."""


def parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """Parses YAML front matter. Uses pyyaml if available, else simple parser."""
    match = FRONTMATTER_PATTERN.match(content)
    if not match:
        return {}, content

    if HAS_YAML:
        try:
            metadata = yaml.safe_load(match.group(1)) or {}
        except yaml.YAMLError as error:
            raise FrontmatterParseError from error
        if not isinstance(metadata, dict):
            raise FrontmatterTypeError
    else:
        metadata = {}
        for line in match.group(1).splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" in line:
                key, val = line.split(":", 1)
                metadata[key.strip()] = val.strip().strip("'\"")

    body = content[match.end() :]
    return metadata, body


def count_placeholders(markdown_file: Path) -> int:
    """Returns the number of {{...}} placeholders left in the markdown file."""
    return len(PLACEHOLDER_PATTERN.findall(markdown_file.read_text(encoding="utf-8")))


def has_no_placeholders(markdown_file: Path) -> bool:
    """Returns True if there are no unfilled placeholders."""
    return count_placeholders(markdown_file) == 0


def _check_frontmatter(
    metadata: dict[str, Any], schema_meta: dict[str, Any], allow_extra: bool
) -> list[str]:
    errors = []
    if not allow_extra:
        extra = set(metadata.keys()) - set(schema_meta.keys())
        if extra:
            errors.append(f"EXTRA_FRONTMATTER_FOUND: {', '.join(extra)}")

    for field, schema in schema_meta.items():
        if schema.get("required", False) and not metadata.get(field):
            errors.append(f"MISSING_REQUIRED_METADATA: {field}")
        elif field in metadata:
            val = metadata[field]
            expected_type = schema.get("type", str)
            if isinstance(expected_type, type) and not isinstance(val, expected_type):
                errors.append(
                    f"INVALID_METADATA_TYPE: {field} "
                    f"(expected: {expected_type.__name__}, "
                    f"actual: {type(val).__name__})"
                )

            allowed = schema.get("allowed_values")
            if allowed and val not in allowed:
                allowed_str = ", ".join(allowed)
                errors.append(
                    f"INVALID_METADATA_VALUE: {field} "
                    f"(actual: {val}, allowed: {allowed_str})"
                )
    return errors


def _check_sections(
    body: str, required_sections: tuple[str, ...], allow_extra: bool
) -> list[str]:
    errors = []
    matches = list(HEADING_PATTERN.finditer(body))
    sections = {
        m.group("name"): body[
            m.end() : (matches[i + 1].start() if i + 1 < len(matches) else len(body))
        ]
        for i, m in enumerate(matches)
    }

    actual_sections = list(sections.keys())

    if allow_extra:
        missing = [s for s in required_sections if s not in actual_sections]
        if missing:
            errors.append(f"MISSING_REQUIRED_SECTION: {', '.join(missing)}")
        else:
            req_indices = [actual_sections.index(s) for s in required_sections]
            if req_indices != sorted(req_indices):
                errors.append(
                    "INVALID_SECTION_ORDER (required sections are out of order)"
                )
    else:
        if tuple(actual_sections) != required_sections:
            expected_sections = ", ".join(required_sections)
            errors.append(f"INVALID_SECTION_ORDER (expected: {expected_sections})")

    if empty := [name for name, section in sections.items() if not section.strip()]:
        errors.append(f"EMPTY_SECTIONS_FOUND: {', '.join(empty)}")

    return errors


def validate_review_file(
    review_file_path: Path, expected_type: str | None = None
) -> list[str]:
    try:
        content = review_file_path.read_text(encoding="utf-8")
    except Exception as e:
        return [f"FILE_READ_ERROR: {e}"]

    errors = []
    placeholder_count = len(PLACEHOLDER_PATTERN.findall(content))
    if placeholder_count:
        errors.append(f"REMAINING_PLACEHOLDERS: {placeholder_count}")

    try:
        metadata, body = parse_frontmatter(content)
    except FrontmatterParseError:
        errors.append("INVALID_FRONTMATTER_YAML")
        return errors
    except FrontmatterTypeError:
        errors.append("INVALID_FRONTMATTER_TYPE")
        return errors

    if not metadata:
        errors.append("MISSING_FRONTMATTER")
        return errors

    document_type = metadata.get("type")
    if expected_type and document_type != expected_type:
        errors.append(f"TYPE_MISMATCH: expected {expected_type}, got {document_type}")
        return errors

    if document_type not in TEMPLATE_SCHEMAS:
        errors.append(f"UNSUPPORTED_DOCUMENT_TYPE: {document_type}")
        return errors

    schema = TEMPLATE_SCHEMAS[document_type]
    config = load_config()

    errors.extend(
        _check_frontmatter(
            metadata, schema["frontmatter"], config.get("allow_extra_frontmatter", True)
        )
    )
    errors.extend(
        _check_sections(
            body, schema["sections"], config.get("allow_extra_sections", True)
        )
    )

    return errors


def validate_no_comments(review_file_path: Path) -> list[str]:
    try:
        content = review_file_path.read_text(encoding="utf-8")
    except Exception as e:
        return [f"FILE_READ_ERROR: {e}"]

    html_comments = len(HTML_COMMENT_PATTERN.findall(content))
    return [f"REMAINING_COMMENTS: {html_comments}"] if html_comments else []
