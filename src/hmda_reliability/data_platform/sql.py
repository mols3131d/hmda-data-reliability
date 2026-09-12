"""DuckDB SQL identifier와 고정 string literal을 위한 quoting helper."""


def quote_identifier(identifier: str) -> str:
    """SQL 식별자를 double-quote로 감싸고 내부 quote를 escape한다.

    Preconditions:
        - identifier는 비어 있지 않아야 한다.
        - DuckDB SQL 파서 오류를 방지하기 위해 null 문자('\\x00')를 포함할 수 없다.

    Exceptions:
        - ValueError: 빈 문자열이거나 null 문자가 포함된 경우.
    """

    if not identifier or "\x00" in identifier:
        msg = "식별자는 비어 있거나 null 문자를 포함할 수 없습니다."
        raise ValueError(msg)
    escaped_identifier = identifier.replace('"', '""')
    return f'"{escaped_identifier}"'


def qualify_table_name(table_name: str) -> str:
    """점으로 구분된 테이블 식별자(예: 'schema.table')의 각 부분을 개별 quote한다.

    Preconditions:
        - table_name의 split 결과 어떤 부분(part)도 비어 있지 않아야 한다.
          (예: '.table', 'schema.' 거부).

    Exceptions:
        - ValueError: 식별자 조각 중 하나라도 비어 있는 경우.
    """

    parts = table_name.split(".")
    if any(not part for part in parts):
        msg = "식별자 조각은 비어 있을 수 없습니다."
        raise ValueError(msg)
    return ".".join(quote_identifier(part) for part in parts)


def quote_string_literal(value: str) -> str:
    """고정 SQL string literal을 single-quote로 감싸고 내부 quote를 escape한다.

    Contract:
        - 고정 상수 문자열 리터럴 전용 helper다.
        - 사용자 입력 등 동적 값은 SQL injection 방지를 위해 항상
          parameter binding(? 또는 $1)을 우선해야 한다.
    """

    escaped_value = value.replace("'", "''")
    return f"'{escaped_value}'"
