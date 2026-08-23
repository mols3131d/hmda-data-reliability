"""Complete HMDA table schema/content state contract tests."""

from __future__ import annotations

from typing import Any

import duckdb
import pytest
from pydantic import ValidationError

import hmda_reliability.reliability as reliability
from hmda_reliability.hmda_data import PartitionContentIdentity


def _table_state_api() -> tuple[type[Any], Any, type[Exception]]:
    identity_type = getattr(reliability, "TableStateIdentity", None)
    builder = getattr(reliability, "create_table_state_identity", None)
    error_type = getattr(reliability, "TableStateIdentityError", None)
    assert identity_type is not None, "TableStateIdentity API가 필요합니다."
    assert builder is not None, "create_table_state_identity API가 필요합니다."
    assert error_type is not None, "TableStateIdentityError API가 필요합니다."
    return identity_type, builder, error_type


def _partition_identity(
    source_year: int,
    *,
    source_file: str | None = None,
    row_count: int = 1,
    digest: str,
) -> PartitionContentIdentity:
    return PartitionContentIdentity(
        table_name="raw.hmda_loans",
        source_year=source_year,
        source_file=source_file,
        row_count=row_count,
        digest=digest,
    )


@pytest.mark.component
def test_create_table_state_identity_preserves_complete_sorted_population() -> None:
    """State는 schema, total row와 year별 logical identity를 함께 보존한다."""

    identity_type, create_identity, _ = _table_state_api()
    with duckdb.connect(":memory:") as connection:
        _create_table(connection)

        state = create_identity(connection, "raw.hmda_loans")

    assert isinstance(state, identity_type)
    assert state.table_name == "raw.hmda_loans"
    assert state.schema_hash.startswith("sha256:")
    assert state.row_count == 3
    assert tuple(identity.source_year for identity in state.partition_identities) == (
        2024,
        2025,
    )
    assert (
        sum(identity.row_count for identity in state.partition_identities)
        == state.row_count
    )
    with pytest.raises(ValidationError):
        state.row_count = 4


@pytest.mark.unit
@pytest.mark.parametrize(
    "partition_identities",
    [
        (
            _partition_identity(2025, digest="sha256-v1:first"),
            _partition_identity(2025, digest="sha256-v1:second"),
        ),
        (
            _partition_identity(
                2025,
                source_file="part.csv",
                digest="sha256-v1:file",
            ),
        ),
    ],
    ids=("duplicate-year", "overlapping-file-scope"),
)
def test_table_state_identity_rejects_non_complete_partition_scope(
    partition_identities: tuple[PartitionContentIdentity, ...],
) -> None:
    """Duplicate year와 file-scoped identity는 complete population이 아니다."""

    identity_type, _, _ = _table_state_api()

    with pytest.raises(ValidationError):
        identity_type(
            table_name="raw.hmda_loans",
            schema_hash="sha256:schema",
            row_count=sum(identity.row_count for identity in partition_identities),
            partition_identities=partition_identities,
        )


@pytest.mark.component
def test_create_table_state_identity_rejects_null_year_population() -> None:
    """Year partition으로 덮이지 않는 row는 valid complete state가 아니다."""

    _, create_identity, error_type = _table_state_api()
    with duckdb.connect(":memory:") as connection:
        _create_table(connection)
        connection.execute(
            "INSERT INTO raw.hmda_loans VALUES (NULL, 'unknown.csv', 999)"
        )

        with pytest.raises(error_type, match="source_year"):
            create_identity(connection, "raw.hmda_loans")


@pytest.mark.unit
def test_table_state_identity_distinguishes_incomplete_or_changed_content() -> None:
    """Missing partition과 equal-count content drift는 exact state와 다르다."""

    identity_type, _, _ = _table_state_api()
    expected = identity_type(
        table_name="raw.hmda_loans",
        schema_hash="sha256:schema",
        row_count=3,
        partition_identities=(
            _partition_identity(2024, row_count=1, digest="sha256-v1:2024"),
            _partition_identity(2025, row_count=2, digest="sha256-v1:2025"),
        ),
    )
    missing_partition = identity_type(
        table_name="raw.hmda_loans",
        schema_hash="sha256:schema",
        row_count=2,
        partition_identities=(
            _partition_identity(2025, row_count=2, digest="sha256-v1:2025"),
        ),
    )
    changed_content = identity_type(
        table_name="raw.hmda_loans",
        schema_hash="sha256:schema",
        row_count=3,
        partition_identities=(
            _partition_identity(2024, row_count=1, digest="sha256-v1:2024"),
            _partition_identity(2025, row_count=2, digest="sha256-v1:changed"),
        ),
    )

    assert missing_partition != expected
    assert changed_content != expected


def _create_table(connection: duckdb.DuckDBPyConnection) -> None:
    connection.execute("CREATE SCHEMA raw")
    connection.execute(
        """
        CREATE TABLE raw.hmda_loans (
            source_year INTEGER,
            source_file_name VARCHAR,
            loan_amount INTEGER
        )
        """
    )
    connection.execute(
        """
        INSERT INTO raw.hmda_loans VALUES
            (2025, '2025-a.csv', 300),
            (2024, '2024.csv', 100),
            (2025, '2025-b.csv', 200)
        """
    )
