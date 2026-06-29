"""DuckDB SQL 식별자 헬퍼."""

from __future__ import annotations


def quote_identifier(identifier: str) -> str:
    """DuckDB 식별자를 안전하게 감싼다."""

    if not identifier or "\x00" in identifier:
        msg = "식별자는 비어 있거나 null 문자를 포함할 수 없습니다."
        raise ValueError(msg)
    escaped_identifier = identifier.replace('"', '""')
    return f'"{escaped_identifier}"'


def qualify_table_name(table_name: str) -> str:
    """schema.table 형식의 테이블명을 DuckDB 식별자로 변환한다."""

    return ".".join(quote_identifier(part) for part in table_name.split("."))


def quote_string_literal(value: str) -> str:
    """DuckDB 문자열 리터럴을 안전하게 감싼다."""

    escaped_value = value.replace("'", "''")
    return f"'{escaped_value}'"
