"""HMDA 원천 CSV의 read-only EDA 계산."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

import duckdb

from project_pivot.hmda_data.errors import HMDADataValidationError

REQUIRED_EDA_COLUMNS = (
    "activity_year",
    "state_code",
    "county_code",
    "loan_purpose",
    "action_taken",
    "loan_amount",
    "income",
)
EXPECTED_TYPE_FAMILIES = {
    "activity_year": frozenset({"TINYINT", "SMALLINT", "INTEGER", "BIGINT", "HUGEINT"}),
    "state_code": frozenset({"VARCHAR"}),
    "county_code": frozenset({"VARCHAR"}),
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
        schema_payload = json.dumps(
            sorted(schema_rows, key=lambda row: row["name"]),
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
        schema_hash = f"sha256:{hashlib.sha256(schema_payload.encode()).hexdigest()}"

        profile_columns = [
            column for column in REQUIRED_EDA_COLUMNS if column in inferred_types
        ]
        metric_select = ["count(*) AS row_count"] + [
            f"count(*) FILTER (WHERE {_quote_identifier(column)} IS NULL) "
            f"AS {_quote_identifier(column)}"
            for column in profile_columns
        ]
        if "observed_at" in inferred_types:
            metric_select.append(
                'max(try_cast("observed_at" AS TIMESTAMP)) AS freshness_value'
            )

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
        duration_seconds = time.monotonic() - started_at

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

        freshness_value = total_row[-1] if "observed_at" in inferred_types else None
        freshness = {
            "status": "measured" if freshness_value is not None else "unmeasured",
            "source_column": "observed_at" if "observed_at" in inferred_types else None,
            "freshness_at": (
                freshness_value.isoformat() if freshness_value is not None else None
            ),
            "boundary": {
                "file_mtime": "filesystem metadata; not source freshness",
                "bronze_ingested_at": (
                    "ingestion time from separate raw-table EDA path"
                ),
            },
        }
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
                "schema_hash": schema_hash,
            },
            "freshness": freshness,
        }
    finally:
        connection.close()
