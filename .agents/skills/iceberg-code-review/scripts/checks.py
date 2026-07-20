import re
from pathlib import Path
from typing import Any

import yaml
from schema import TEMPLATE_SCHEMAS

PLACEHOLDER_PATTERN = re.compile(r"{{[A-Za-z가-힣_]+}}")
FRONTMATTER_PATTERN = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
HEADING_PATTERN = re.compile(r"^## (?P<name>.+)$", re.MULTILINE)
HTML_COMMENT_PATTERN = re.compile(r"<!--[\s\S]*?-->")


def parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """Parses YAML front matter and separates metadata and body."""
    match = FRONTMATTER_PATTERN.match(content)
    if not match:
        return {}, content

    metadata = yaml.safe_load(match.group(1)) or {}
    body = content[match.end() :]
    return metadata, body


def count_placeholders(markdown_file: Path) -> int:
    """Returns the number of {{...}} placeholders left in the markdown file."""
    return len(PLACEHOLDER_PATTERN.findall(markdown_file.read_text()))


def has_no_placeholders(markdown_file: Path) -> bool:
    """Returns True if there are no unfilled placeholders."""
    return count_placeholders(markdown_file) == 0


def validate_review_file(
    review_file_path: Path, expected_type: str | None = None
) -> list[str]:
    try:
        content = review_file_path.read_text(encoding="utf-8")
    except Exception as e:
        return [f"FILE_READ_ERROR: {e}"]

    metadata, body = parse_frontmatter(content)
    if not metadata:
        return ["MISSING_FRONTMATTER"]

    document_type = metadata.get("type")
    if expected_type and document_type != expected_type:
        return [f"TYPE_MISMATCH: expected {expected_type}, got {document_type}"]

    if document_type not in TEMPLATE_SCHEMAS:
        return [f"UNSUPPORTED_DOCUMENT_TYPE: {document_type}"]

    required_metadata = TEMPLATE_SCHEMAS[document_type]["frontmatter"]
    required_sections = TEMPLATE_SCHEMAS[document_type]["sections"]

    errors = []
    for field, schema in required_metadata.items():
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

    matches = list(HEADING_PATTERN.finditer(body))
    sections = {
        m.group("name"): body[
            m.end() : (matches[i + 1].start() if i + 1 < len(matches) else len(body))
        ]
        for i, m in enumerate(matches)
    }

    if tuple(sections) != required_sections:
        expected_sections = ", ".join(required_sections)
        errors.append(f"INVALID_SECTION_ORDER (expected: {expected_sections})")

    if empty := [name for name, section in sections.items() if not section.strip()]:
        errors.append(f"EMPTY_SECTIONS_FOUND: {', '.join(empty)}")

    return errors


def validate_no_comments(review_file_path: Path) -> list[str]:
    try:
        content = review_file_path.read_text(encoding="utf-8")
    except Exception as e:
        return [f"FILE_READ_ERROR: {e}"]

    # Find YAML and HTML comments using simple regex (KISS principle)
    # Match common comment patterns instead of full AST parsing
    match = FRONTMATTER_PATTERN.match(content)
    frontmatter_text = match.group(1) if match else ""
    yaml_comments = len(re.findall(r"(?m)^[^#\n]*#", frontmatter_text))
    html_comments = len(HTML_COMMENT_PATTERN.findall(content))
    count = yaml_comments + html_comments

    return [f"REMAINING_COMMENTS: {count}"] if count > 0 else []
