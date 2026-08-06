"""HMDA 원천 CSV의 read-only EDA 계산."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import duckdb

from project_pivot.hmda_data.errors import HMDADataValidationError

REQUIRED_EDA_COLUMNS = (
    "activity_year",
    "state_code",
    "loan_purpose",
    "action_taken",
    "loan_amount",
    "income",
)
EXPECTED_TYPE_FAMILIES = {
    "activity_year": frozenset({"TINYINT", "SMALLINT", "INTEGER", "BIGINT", "HUGEINT"}),
    "state_code": frozenset({"VARCHAR"}),
    "loan_purpose": frozenset({"TINYINT", "SMALLINT", "INTEGER", "BIGINT", "HUGEINT"}),
    "action_taken": frozenset({"TINYINT", "SMALLINT", "INTEGER", "BIGINT", "HUGEINT"}),
    "loan_amount": frozenset(
        {"TINYINT", "SMALLINT", "INTEGER", "BIGINT", "HUGEINT", "DECIMAL", "DOUBLE"}
    ),
    "income": frozenset(
        {"TINYINT", "SMALLINT", "INTEGER", "BIGINT", "HUGEINT", "DECIMAL", "DOUBLE"}
    ),
}
CSV_OPTIONS = {
    "header": True,
    "nullstr": ["NA", ""],
    "sample_size": 200_000,
}


def _quote_identifier(identifier: str) -> str:
    return f'"{identifier.replace(chr(34), chr(34) * 2)}"'


def _type_family(inferred_type: str) -> str:
    return inferred_type.partition("(")[0]


def _collect_code_distributions(
    connection: duckdb.DuckDBPyConnection,
    inferred_types: dict[str, str],
    row_count: int,
) -> dict[str, list[dict[str, Any]]]:
    distributions: dict[str, list[dict[str, Any]]] = {}
    target_code_cols = [
        col
        for col in ("action_taken", "loan_purpose", "state_code")
        if col in inferred_types
    ]
    for col in target_code_cols:
        quoted_col = _quote_identifier(col)
        dist_rows = connection.execute(
            f"""
            SELECT {quoted_col} AS val, count(*) AS val_count
            FROM hmda_eda_source
            WHERE {quoted_col} IS NOT NULL
            GROUP BY {quoted_col}
            ORDER BY val_count DESC, val ASC
            """
        ).fetchall()
        distributions[col] = [
            {
                "value": row[0],
                "count": row[1],
                "share": row[1] / row_count if row_count else 0.0,
            }
            for row in dist_rows
        ]
    return distributions


def _collect_numeric_summaries(
    connection: duckdb.DuckDBPyConnection,
    inferred_types: dict[str, str],
) -> dict[str, dict[str, Any]]:
    numeric_summaries: dict[str, dict[str, Any]] = {}
    target_numeric_cols = [
        col for col in ("loan_amount", "income") if col in inferred_types
    ]
    for col in target_numeric_cols:
        quoted_col = _quote_identifier(col)
        row = connection.execute(
            f"""
            SELECT
                count({quoted_col}) AS non_null_count,
                min({quoted_col}) AS min_val,
                quantile_cont({quoted_col}, 0.25) AS p25_val,
                median({quoted_col}) AS median_val,
                quantile_cont({quoted_col}, 0.75) AS p75_val,
                max({quoted_col}) AS max_val
            FROM hmda_eda_source
            """
        ).fetchone()
        if row and row[0] > 0:
            numeric_summaries[col] = {
                "non_null_count": row[0],
                "min": float(row[1]) if row[1] is not None else None,
                "p25": float(row[2]) if row[2] is not None else None,
                "median": float(row[3]) if row[3] is not None else None,
                "p75": float(row[4]) if row[4] is not None else None,
                "max": float(row[5]) if row[5] is not None else None,
            }
        else:
            numeric_summaries[col] = {
                "non_null_count": 0,
                "min": None,
                "p25": None,
                "median": None,
                "p75": None,
                "max": None,
            }
    return numeric_summaries


def _calculate_grain_alignment(
    connection: duckdb.DuckDBPyConnection,
    inferred_types: dict[str, str],
    row_count: int,
) -> dict[str, Any]:
    grain_cols = ["activity_year", "state_code", "loan_purpose"]
    has_all_grain_cols = all(col in inferred_types for col in grain_cols)
    if has_all_grain_cols:
        grain_result = connection.execute(
            """
            SELECT
                count(
                    DISTINCT (activity_year, state_code, loan_purpose)
                ) FILTER (
                    WHERE activity_year IS NOT NULL
                      AND state_code IS NOT NULL
                      AND loan_purpose IS NOT NULL
                ) AS distinct_groups,
                count(*) FILTER (
                    WHERE activity_year IS NULL
                       OR state_code IS NULL
                       OR loan_purpose IS NULL
                ) AS null_key_rows
            FROM hmda_eda_source
            """
        ).fetchone()
        distinct_groups = grain_result[0] if grain_result else 0
        null_key_rows = grain_result[1] if grain_result else 0
        return {
            "columns": grain_cols,
            "distinct_group_count": distinct_groups,
            "null_key_rows": null_key_rows,
            "coverage_rate": (row_count - null_key_rows) / row_count
            if row_count
            else 0.0,
        }
    return {
        "columns": [col for col in grain_cols if col in inferred_types],
        "distinct_group_count": 0,
        "null_key_rows": 0,
        "coverage_rate": 0.0,
    }


def analyze_hmda_csv(
    source_path: str | Path,
    *,
    memory_limit: str = "2GB",
    threads: int = 2,
    temp_directory: str | Path,
    max_activity_years: int = 32,
) -> dict[str, Any]:
    """HMDA CSV 전체를 aggregate하고 JSON-serializable evidence를 반환한다."""

    input_path = Path(source_path).expanduser().resolve()
    if not input_path.is_file():
        raise FileNotFoundError(f"HMDA EDA input file does not exist: {input_path}")
    if max_activity_years < 1:
        raise ValueError("max_activity_years must be at least 1")

    resolved_temp_directory = Path(temp_directory).expanduser().resolve()
    resolved_temp_directory.mkdir(parents=True, exist_ok=True)
    duckdb_config: dict[str, str | bool | int | float | list[str]] = {
        "memory_limit": memory_limit,
        "threads": threads,
        "temp_directory": str(resolved_temp_directory),
    }
    connection = duckdb.connect(config=duckdb_config)
    try:
        source_relation = connection.sql(
            """
            SELECT * FROM read_csv_auto(
                $input_path,
                header=true,
                nullstr=['NA', ''],
                sample_size=200000
            )
            """,
            params={"input_path": str(input_path)},
        )
        source_relation.create_view("hmda_eda_source", replace=True)
        schema_rows = [
            {"name": name, "type": str(column_type)}
            for name, column_type in zip(
                source_relation.columns, source_relation.types, strict=True
            )
        ]
        inferred_types = {row["name"]: row["type"] for row in schema_rows}
        required_schema = [
            {
                "column": column,
                "inferred_type": inferred_types.get(column),
                "status": (
                    "valid"
                    if column in inferred_types
                    and _type_family(inferred_types[column])
                    in EXPECTED_TYPE_FAMILIES[column]
                    else "missing"
                    if column not in inferred_types
                    else "type mismatch"
                ),
            }
            for column in REQUIRED_EDA_COLUMNS
        ]
        missing_required = [
            item["column"] for item in required_schema if item["status"] != "valid"
        ]
        if missing_required:
            raise HMDADataValidationError(
                f"Required EDA column validation failed: {missing_required}"
            )

        profile_columns = [
            column for column in REQUIRED_EDA_COLUMNS if column in inferred_types
        ]
        metric_select = ["count(*) AS row_count"] + [
            f"count(*) FILTER (WHERE {_quote_identifier(column)} IS NULL) "
            f"AS {_quote_identifier(column)}"
            for column in profile_columns
        ]

        has_activity_year = "activity_year" in inferred_types
        grouping_select = (
            "activity_year, grouping(activity_year) AS is_total, "
            if has_activity_year
            else ""
        )
        grouping_clause = (
            "GROUP BY GROUPING SETS ((), (activity_year)) "
            "ORDER BY is_total DESC "
            f"LIMIT {max_activity_years + 2}"
            if has_activity_year
            else ""
        )
        started_at = time.monotonic()
        metric_rows = connection.execute(
            f"SELECT {grouping_select}{', '.join(metric_select)} "
            f"FROM hmda_eda_source {grouping_clause}"
        ).fetchall()

        total_row = next(
            row for row in metric_rows if not has_activity_year or row[1] == 1
        )
        metric_offset = 2 if has_activity_year else 0
        row_count = total_row[metric_offset]
        null_counts = dict(
            zip(
                profile_columns,
                total_row[metric_offset + 1 : metric_offset + 1 + len(profile_columns)],
                strict=True,
            )
        )
        activity_year_rows = (
            sorted(
                (row for row in metric_rows if row[1] == 0),
                key=lambda row: (row[0] is None, row[0]),
            )
            if has_activity_year
            else []
        )
        if len(activity_year_rows) > max_activity_years:
            msg = (
                "activity_year cardinality exceeds "
                f"the configured bound of {max_activity_years}"
            )
            raise HMDADataValidationError(msg)

        distributions = _collect_code_distributions(
            connection, inferred_types, row_count
        )
        numeric_summaries = _collect_numeric_summaries(connection, inferred_types)
        grain = _calculate_grain_alignment(connection, inferred_types, row_count)
        duration_seconds = time.monotonic() - started_at

        return {
            "source": {
                "path": str(input_path),
                "scope": "full_file",
                "csv_options": CSV_OPTIONS,
                "duckdb_config": duckdb_config,
            },
            "duration_seconds": duration_seconds,
            "row_count": row_count,
            "activity_year_counts": [
                {"activity_year": row[0], "row_count": row[metric_offset]}
                for row in activity_year_rows
            ],
            "null_counts": null_counts,
            "null_rates": {
                column: null_count / row_count if row_count else 0.0
                for column, null_count in null_counts.items()
            },
            "schema": {
                "columns": schema_rows,
                "required_columns": required_schema,
            },
            "distributions": distributions,
            "numeric_summaries": numeric_summaries,
            "grain": grain,
        }
    finally:
        connection.close()
