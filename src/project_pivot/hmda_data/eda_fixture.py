"""HMDA EDA memory workload fixture 생성과 검증."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import duckdb
from pydantic import BaseModel, ConfigDict, Field, model_validator

from project_pivot.hmda_data.errors import HMDADataValidationError

FIXTURE_VERSION = "hmda-eda-memory-v1"
FIXTURE_FILE_NAME = "hmda-eda-memory.csv"
MANIFEST_FILE_NAME = "manifest.json"


class HMDAEDAFixtureManifest(BaseModel):
    """대표 EDA fixture의 재현성과 expected invariant 계약."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    version: str
    seed: int
    schema_columns: list[str]
    row_count: int = Field(gt=0)
    row_width_bytes: float = Field(gt=0)
    null_rates: dict[str, float]
    activity_year_cardinality: int = Field(gt=0)
    activity_year_skew: dict[str, float]
    file_count: int = Field(gt=0)
    files: list[dict[str, str | int]]
    expected: dict[str, Any]

    @model_validator(mode="after")
    def validate_files(self) -> HMDAEDAFixtureManifest:
        if self.file_count != len(self.files):
            raise ValueError("file_count does not match files")
        return self


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def prepare_hmda_eda_fixture(
    output_directory: str | Path,
    *,
    row_count: int = 5_000_000,
    seed: int = 20_250_731,
) -> HMDAEDAFixtureManifest:
    """대표 HMDA CSV와 manifest를 측정 process 밖에서 생성한다."""

    if row_count < 1:
        raise ValueError("row_count must be at least 1")

    output_path = Path(output_directory).expanduser().resolve()
    output_path.mkdir(parents=True, exist_ok=True)
    fixture_path = output_path / FIXTURE_FILE_NAME
    manifest_path = output_path / MANIFEST_FILE_NAME
    connection = duckdb.connect()
    try:
        connection.execute(
            """
            COPY (
                SELECT
                    CASE
                        WHEN row_id % 10 < 7 THEN 2025
                        WHEN row_id % 10 < 9 THEN 2024
                        ELSE 2023
                    END AS activity_year,
                    CASE row_id % 5
                        WHEN 0 THEN 'CA'
                        WHEN 1 THEN 'NY'
                        WHEN 2 THEN 'TX'
                        WHEN 3 THEN 'FL'
                        ELSE 'IL'
                    END AS state_code,
                    lpad(CAST((row_id % 99999) + 1 AS VARCHAR), 5, '0') AS county_code,
                    CASE row_id % 4 WHEN 0 THEN 31 ELSE 1 END AS loan_purpose,
                    CASE row_id % 5 WHEN 0 THEN 3 ELSE 1 END AS action_taken,
                    CASE
                        WHEN row_id % 50 = 0 THEN NULL
                        ELSE 100000 + ((row_id * 7919 + $seed) % 900000)
                    END AS loan_amount,
                    CASE
                        WHEN row_id % 20 = 0 THEN NULL
                        ELSE 30 + ((row_id * 1543 + $seed) % 270)
                    END AS income,
                    TIMESTAMP '2025-01-01 00:00:00'
                        + (row_id % 365) * INTERVAL 1 DAY AS observed_at,
                    repeat('x', 96) AS representative_padding
                FROM range($row_count) AS rows(row_id)
            ) TO $fixture_path (HEADER, DELIMITER ',')
            """,
            {
                "seed": seed,
                "row_count": row_count,
                "fixture_path": str(fixture_path),
            },
        )
        stats = connection.execute(
            """
            SELECT
                count(*) AS row_count,
                count(*) FILTER (WHERE loan_amount IS NULL) AS loan_amount_nulls,
                count(*) FILTER (WHERE income IS NULL) AS income_nulls,
                max(observed_at) AS freshness_at,
                activity_year,
                count(*) AS activity_year_count
            FROM read_csv_auto($fixture_path, header=true)
            GROUP BY GROUPING SETS ((), (activity_year))
            ORDER BY activity_year NULLS FIRST
            """,
            {"fixture_path": str(fixture_path)},
        ).fetchall()
    finally:
        connection.close()

    total_row = stats[0]
    activity_year_counts = [
        {"activity_year": row[4], "row_count": row[5]} for row in stats[1:]
    ]
    file_size = fixture_path.stat().st_size
    manifest = HMDAEDAFixtureManifest(
        version=FIXTURE_VERSION,
        seed=seed,
        schema_columns=[
            "activity_year",
            "state_code",
            "county_code",
            "loan_purpose",
            "action_taken",
            "loan_amount",
            "income",
            "observed_at",
            "representative_padding",
        ],
        row_count=total_row[0],
        row_width_bytes=file_size / total_row[0],
        null_rates={
            "loan_amount": total_row[1] / total_row[0],
            "income": total_row[2] / total_row[0],
        },
        activity_year_cardinality=len(activity_year_counts),
        activity_year_skew={
            str(row["activity_year"]): row["row_count"] / total_row[0]
            for row in activity_year_counts
        },
        file_count=1,
        files=[
            {
                "path": fixture_path.name,
                "size_bytes": file_size,
                "sha256": _sha256(fixture_path),
            }
        ],
        expected={
            "row_count": total_row[0],
            "null_counts": {
                "loan_amount": total_row[1],
                "income": total_row[2],
            },
            "activity_year_counts": activity_year_counts,
            "freshness_at": total_row[3].isoformat(),
        },
    )
    manifest_path.write_text(
        json.dumps(manifest.model_dump(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def validate_hmda_eda_fixture(
    fixture_directory: str | Path,
) -> tuple[Path, HMDAEDAFixtureManifest]:
    """대표 fixture와 manifest의 필수 계약 및 hash를 검증한다."""

    fixture_root = Path(fixture_directory).expanduser().resolve()
    manifest_path = fixture_root / MANIFEST_FILE_NAME
    if not manifest_path.is_file():
        raise HMDADataValidationError(
            f"Fixture manifest does not exist: {manifest_path}"
        )

    manifest = HMDAEDAFixtureManifest.model_validate_json(
        manifest_path.read_text(encoding="utf-8")
    )
    if manifest.version != FIXTURE_VERSION:
        raise HMDADataValidationError(
            f"Unsupported fixture version: {manifest.version}"
        )

    file_record = manifest.files[0]
    fixture_path = fixture_root / str(file_record["path"])
    if not fixture_path.is_file():
        raise HMDADataValidationError(f"Fixture file does not exist: {fixture_path}")
    if fixture_path.stat().st_size != file_record["size_bytes"]:
        raise HMDADataValidationError("Fixture file size does not match manifest")
    if _sha256(fixture_path) != file_record["sha256"]:
        raise HMDADataValidationError("Fixture file hash does not match manifest")
    return fixture_path, manifest


def validate_hmda_eda_evidence(
    evidence: dict[str, Any],
    manifest: HMDAEDAFixtureManifest,
) -> None:
    """Memory workload 결과의 schema와 핵심 invariant를 검증한다."""

    expected = manifest.expected
    required_schema = evidence["schema"]["required_columns"]
    if any(row["status"] != "valid" for row in required_schema):
        raise HMDADataValidationError("EDA result has invalid required schema")
    if evidence["row_count"] != expected["row_count"]:
        raise HMDADataValidationError("EDA row count does not match manifest")
    for column, expected_count in expected["null_counts"].items():
        if evidence["null_counts"][column] != expected_count:
            raise HMDADataValidationError(
                f"EDA null count does not match manifest: {column}"
            )
    if evidence["activity_year_counts"] != expected["activity_year_counts"]:
        raise HMDADataValidationError("EDA activity-year counts do not match manifest")
    if evidence["freshness"]["freshness_at"] != expected["freshness_at"]:
        raise HMDADataValidationError("EDA freshness does not match manifest")
