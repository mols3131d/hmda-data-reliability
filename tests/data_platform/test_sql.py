"""DuckDB SQL quoting 헬퍼 테스트."""

import pytest

from project_pivot.data_platform.sql import (
    qualify_table_name,
    quote_identifier,
    quote_string_literal,
)


def test_quote_identifier_escapes_double_quotes() -> None:
    """식별자 내부 double quote를 DuckDB 규칙으로 escape한다."""

    assert quote_identifier('loan"amount') == '"loan""amount"'


def test_quote_identifier_rejects_empty_or_null_character() -> None:
    """비어 있거나 null 문자를 포함한 식별자를 거부한다."""

    for identifier in ("", "loan\x00amount"):
        with pytest.raises(ValueError, match="식별자"):
            quote_identifier(identifier)


def test_qualify_table_name_quotes_each_part() -> None:
    """schema.table 각 부분을 개별 식별자로 감싼다."""

    assert qualify_table_name('raw.hmda"loans') == '"raw"."hmda""loans"'


def test_quote_string_literal_escapes_single_quotes() -> None:
    """문자열 리터럴 내부 single quote를 DuckDB 규칙으로 escape한다."""

    assert quote_string_literal("borrower's file") == "'borrower''s file'"
