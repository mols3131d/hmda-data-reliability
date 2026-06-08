"""Taxi 합성 데이터 SQL 조각."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from project_pivot.taxi_data.sql import quote_identifier


def sampled_source_query(
    *,
    timestamp_column: str,
    partition_column: str,
) -> str:
    timestamp = quote_identifier(timestamp_column)
    partition = quote_identifier(partition_column)
    return f"""
        WITH source AS (
            SELECT
                *,
                CAST({timestamp} AS DATE) AS {partition}
            FROM read_parquet(?)
            WHERE {timestamp} IS NOT NULL
        ),
        ranked AS (
            SELECT
                *,
                row_number() OVER (
                    PARTITION BY {partition}
                    ORDER BY
                        hash(CAST({timestamp} AS VARCHAR)),
                        {timestamp},
                        hash(COLUMNS(*))
                ) AS __sample_rank,
                count(*) OVER (PARTITION BY {partition}) AS __partition_count
            FROM source
        )
        SELECT * EXCLUDE (__sample_rank, __partition_count)
        FROM ranked
        WHERE __sample_rank <= greatest(
            1,
            CAST(ceil(__partition_count * ?) AS BIGINT)
        )
    """


def replace_text_clause(columns: Sequence[str]) -> str:
    if not columns:
        return ""
    replacements = ", ".join(
        f"CAST({quote_identifier(column)} AS VARCHAR) AS {quote_identifier(column)}"
        for column in columns
    )
    return f" REPLACE ({replacements})"


def rename_clause(columns: Mapping[str, str]) -> str:
    if not columns:
        return ""
    renames = ", ".join(
        f"{quote_identifier(source)} AS {quote_identifier(target)}"
        for source, target in columns.items()
    )
    return f" RENAME ({renames})"
