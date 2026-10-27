"""고정 SQL 표현과 실제 DuckDB parser의 원문 보존을 검증한다."""

import duckdb
import pytest
from hypothesis import example, given
from hypothesis import strategies as st

from hmda_reliability.data_platform.sql import (
    qualify_table_name,
    quote_identifier,
    quote_string_literal,
)


@pytest.mark.unit
def test_quote_identifier_escapes_double_quotes() -> None:
    """식별자 내부 double quote를 DuckDB 규칙으로 escape한다."""

    assert quote_identifier('loan"amount') == '"loan""amount"'


@pytest.mark.unit
def test_quote_identifier_rejects_empty_or_null_character() -> None:
    """비어 있거나 null 문자를 포함한 식별자를 거부한다."""

    for identifier in ("", "loan\x00amount"):
        with pytest.raises(ValueError, match="식별자"):
            quote_identifier(identifier)


@pytest.mark.unit
def test_qualify_table_name_quotes_each_part() -> None:
    """schema.table 각 부분을 개별 식별자로 감싼다."""

    assert qualify_table_name('raw.hmda"loans') == '"raw"."hmda""loans"'


@pytest.mark.unit
def test_qualify_table_name_rejects_empty_parts() -> None:
    """qualified table name의 빈 schema/table 조각을 거부한다."""

    for table_name in ("raw.", ".loans"):
        with pytest.raises(ValueError, match="식별자"):
            qualify_table_name(table_name)


@pytest.mark.unit
def test_quote_string_literal_escapes_single_quotes() -> None:
    """문자열 리터럴 내부 single quote를 DuckDB 규칙으로 escape한다."""

    assert quote_string_literal("borrower's file") == "'borrower''s file'"


@pytest.mark.component
@given(st.text(min_size=1).filter(lambda value: "\x00" not in value))
@example('loan"; SELECT 99; --')
def test_quote_identifier_preserves_generated_content(identifier: str) -> None:
    """실제 parser가 해석한 column 이름은 원래 식별자와 같아야 한다."""

    with duckdb.connect() as connection:
        result = connection.execute(f"SELECT 7 AS {quote_identifier(identifier)}")

        assert result.description is not None
        assert result.description[0][0] == identifier
        assert result.fetchall() == [(7,)]


@pytest.mark.component
@given(st.text().filter(lambda value: "\x00" not in value))
@example("borrower's file'; SELECT 99; --")
def test_quote_string_literal_preserves_generated_content(value: str) -> None:
    """NUL은 SQL text 입력 범위 밖이며 나머지 원문은 parser를 거쳐 보존된다."""

    with duckdb.connect() as connection:
        result = connection.execute(f"SELECT {quote_string_literal(value)}")

        assert result.fetchall() == [(value,)]
