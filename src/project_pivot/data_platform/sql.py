"""Parameter binding할 수 없는 DuckDB SQL fragment의 quoting helper."""


def quote_identifier(identifier: str) -> str:
    """Identifier를 double-quote하고 empty/NUL input을 거부한다."""

    if not identifier or "\x00" in identifier:
        msg = "식별자는 비어 있거나 null 문자를 포함할 수 없습니다."
        raise ValueError(msg)
    escaped_identifier = identifier.replace('"', '""')
    return f'"{escaped_identifier}"'


def qualify_table_name(table_name: str) -> str:
    """Dot-separated identifier의 각 조각을 quote하고 빈 조각을 거부한다."""

    parts = table_name.split(".")
    if any(not part for part in parts):
        msg = "식별자 조각은 비어 있을 수 없습니다."
        raise ValueError(msg)
    return ".".join(quote_identifier(part) for part in parts)


def quote_string_literal(value: str) -> str:
    """고정 SQL string literal을 quote한다; 동적 값은 parameter binding을 우선한다."""

    escaped_value = value.replace("'", "''")
    return f"'{escaped_value}'"
