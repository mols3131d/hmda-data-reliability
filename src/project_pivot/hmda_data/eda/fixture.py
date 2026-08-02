"""HMDA EDA memory workload fixture 생성과 검증."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Literal

import duckdb
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from project_pivot.hmda_data.eda.analysis import REQUIRED_EDA_COLUMNS
from project_pivot.hmda_data.errors import HMDADataValidationError

FIXTURE_VERSION = "hmda-eda-memory-v1"
FIXTURE_FILE_NAME = "hmda-eda-memory.csv"
MANIFEST_FILE_NAME = "manifest.json"
REQUIRED_EDA_COLUMN_SET = frozenset(REQUIRED_EDA_COLUMNS)
FIXTURE_SCHEMA_COLUMNS = (
    *REQUIRED_EDA_COLUMNS,
    "observed_at",
    "representative_padding",
)


class HMDAEDAFixtureFile(BaseModel):
    """Fixture file integrity record."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    path: str = Field(min_length=1)
    size_bytes: int = Field(gt=0)
    sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")


class HMDAEDAActivityYearCount(BaseModel):
    """Expected row count for one activity year."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    activity_year: int
    row_count: int = Field(gt=0)


class HMDAEDAFreshnessExpectation(BaseModel):
    """Expected source freshness state."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["measured", "unmeasured"]
    freshness_at: str | None

    @model_validator(mode="after")
    def validate_state(self) -> HMDAEDAFreshnessExpectation:
        if (self.status == "measured") != (self.freshness_at is not None):
            raise ValueError("freshness status does not match freshness_at")
        return self


class HMDAEDAFixtureExpected(BaseModel):
    """Expected correctness invariants for the generated fixture."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    row_count: int = Field(gt=0)
    required_column_null_counts: dict[str, int]
    activity_year_counts: list[HMDAEDAActivityYearCount]
    freshness: HMDAEDAFreshnessExpectation

    @model_validator(mode="after")
    def validate_required_columns(self) -> HMDAEDAFixtureExpected:
        if set(self.required_column_null_counts) != REQUIRED_EDA_COLUMN_SET:
            raise ValueError(
                "required_column_null_counts must cover all required EDA columns"
            )
        if any(
            count < 0 or count > self.row_count
            for count in self.required_column_null_counts.values()
        ):
            raise ValueError("required-column null counts are outside row-count bounds")
        return self


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
    files: list[HMDAEDAFixtureFile]
    expected: HMDAEDAFixtureExpected

    @model_validator(mode="after")
    def validate_contract(self) -> HMDAEDAFixtureManifest:
        if tuple(self.schema_columns) != FIXTURE_SCHEMA_COLUMNS:
            raise ValueError(
                "schema_columns does not match the complete fixture schema"
            )
        if set(self.null_rates) != REQUIRED_EDA_COLUMN_SET:
            raise ValueError("null_rates must cover all required EDA columns")
        if any(
            not math.isfinite(rate) or rate < 0 or rate > 1
            for rate in self.null_rates.values()
        ):
            raise ValueError("null rates must be between 0 and 1")
        if self.file_count != len(self.files):
            raise ValueError("file_count does not match files")
        if len({file.path for file in self.files}) != len(self.files):
            raise ValueError("files contains duplicate paths")
        if self.expected.row_count != self.row_count:
            raise ValueError("expected row count does not match manifest row count")

        year_counts = {
            str(item.activity_year): item.row_count
            for item in self.expected.activity_year_counts
        }
        if len(year_counts) != len(self.expected.activity_year_counts):
            raise ValueError("activity-year counts contains duplicate years")
        if len(year_counts) != self.activity_year_cardinality:
            raise ValueError("activity-year cardinality does not match expected counts")
        if set(self.activity_year_skew) != set(year_counts):
            raise ValueError("activity-year skew keys do not match expected counts")
        if sum(year_counts.values()) != self.row_count:
            raise ValueError("activity-year counts do not sum to row count")
        if any(
            not math.isfinite(rate) or rate < 0 or rate > 1
            for rate in self.activity_year_skew.values()
        ):
            raise ValueError("activity-year skew must be between 0 and 1")
        if not math.isclose(
            sum(self.activity_year_skew.values()), 1.0, rel_tol=0, abs_tol=1e-9
        ):
            raise ValueError("activity-year skew must sum to 1")
        for year, count in year_counts.items():
            if not math.isclose(
                self.activity_year_skew[year],
                count / self.row_count,
                rel_tol=0,
                abs_tol=1e-9,
            ):
                raise ValueError("activity-year skew does not match expected counts")
        for column in REQUIRED_EDA_COLUMNS:
            expected_rate = (
                self.expected.required_column_null_counts[column] / self.row_count
            )
            if not math.isclose(
                self.null_rates[column], expected_rate, rel_tol=0, abs_tol=1e-9
            ):
                raise ValueError(
                    f"null rate does not match expected null count: {column}"
                )
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
        HMDAEDAActivityYearCount(activity_year=row[4], row_count=row[5])
        for row in stats[1:]
    ]
    file_size = fixture_path.stat().st_size
    manifest = HMDAEDAFixtureManifest(
        version=FIXTURE_VERSION,
        seed=seed,
        schema_columns=list(FIXTURE_SCHEMA_COLUMNS),
        row_count=total_row[0],
        row_width_bytes=file_size / total_row[0],
        null_rates={
            "activity_year": 0.0,
            "state_code": 0.0,
            "county_code": 0.0,
            "loan_purpose": 0.0,
            "action_taken": 0.0,
            "loan_amount": total_row[1] / total_row[0],
            "income": total_row[2] / total_row[0],
        },
        activity_year_cardinality=len(activity_year_counts),
        activity_year_skew={
            str(row.activity_year): row.row_count / total_row[0]
            for row in activity_year_counts
        },
        file_count=1,
        files=[
            HMDAEDAFixtureFile(
                path=fixture_path.name,
                size_bytes=file_size,
                sha256=_sha256(fixture_path),
            )
        ],
        expected=HMDAEDAFixtureExpected(
            row_count=total_row[0],
            required_column_null_counts={
                "activity_year": 0,
                "state_code": 0,
                "county_code": 0,
                "loan_purpose": 0,
                "action_taken": 0,
                "loan_amount": total_row[1],
                "income": total_row[2],
            },
            activity_year_counts=activity_year_counts,
            freshness=HMDAEDAFreshnessExpectation(
                status="measured",
                freshness_at=total_row[3].isoformat(),
            ),
        ),
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

    try:
        manifest = HMDAEDAFixtureManifest.model_validate_json(
            manifest_path.read_text(encoding="utf-8")
        )
    except (OSError, ValidationError) as error:
        raise HMDADataValidationError(f"Invalid fixture manifest: {error}") from error
    if manifest.version != FIXTURE_VERSION:
        raise HMDADataValidationError(
            f"Unsupported fixture version: {manifest.version}"
        )

    fixture_path: Path | None = None
    try:
        for file_record in manifest.files:
            declared_path = Path(file_record.path)
            if declared_path.is_absolute() or ".." in declared_path.parts:
                raise HMDADataValidationError("Fixture file path escapes fixture root")
            file_path = fixture_root / declared_path
            if not file_path.is_file():
                raise HMDADataValidationError(
                    f"Fixture file does not exist: {file_path}"
                )
            if file_path.stat().st_size != file_record.size_bytes:
                raise HMDADataValidationError(
                    f"Fixture file size does not match manifest: {file_record.path}"
                )
            if _sha256(file_path) != file_record.sha256:
                raise HMDADataValidationError(
                    f"Fixture file hash does not match manifest: {file_record.path}"
                )
            if file_record.path == FIXTURE_FILE_NAME:
                fixture_path = file_path
    except OSError as error:
        raise HMDADataValidationError(
            f"Fixture file validation failed: {error}"
        ) from error
    if fixture_path is None:
        raise HMDADataValidationError(
            f"Fixture manifest does not declare {FIXTURE_FILE_NAME}"
        )
    return fixture_path, manifest


def hmda_eda_fixture_provenance(
    fixture_directory: str | Path,
    manifest: HMDAEDAFixtureManifest,
) -> dict[str, Any]:
    """Return reproducible fixture identity and invariant summary."""

    fixture_root = Path(fixture_directory).expanduser().resolve()
    manifest_path = fixture_root / MANIFEST_FILE_NAME
    schema_payload = json.dumps(
        manifest.schema_columns,
        ensure_ascii=True,
        separators=(",", ":"),
    ).encode()
    return {
        "fixture_version": manifest.version,
        "fixture_directory": str(fixture_root),
        "manifest_sha256": _sha256(manifest_path),
        "files": [file.model_dump() for file in manifest.files],
        "schema_fingerprint": (f"sha256:{hashlib.sha256(schema_payload).hexdigest()}"),
        "row_count": manifest.row_count,
        "expected_invariants": manifest.expected.model_dump(),
    }


def validate_hmda_eda_evidence(
    evidence: dict[str, Any],
    manifest: HMDAEDAFixtureManifest,
) -> None:
    """Memory workload 결과의 schema와 핵심 invariant를 검증한다."""

    try:
        required_schema = evidence["schema"]["required_columns"]
        schema_statuses = {row["column"]: row["status"] for row in required_schema}
        if len(schema_statuses) != len(required_schema):
            raise HMDADataValidationError(
                "EDA result has duplicate required schema columns"
            )
        if set(schema_statuses) != REQUIRED_EDA_COLUMN_SET or any(
            status != "valid" for status in schema_statuses.values()
        ):
            raise HMDADataValidationError("EDA result has invalid required schema")
        if evidence["row_count"] != manifest.expected.row_count:
            raise HMDADataValidationError("EDA row count does not match manifest")

        null_counts = evidence["null_counts"]
        null_rates = evidence["null_rates"]
        if set(null_counts) != REQUIRED_EDA_COLUMN_SET:
            raise HMDADataValidationError(
                "EDA null counts do not cover all required columns"
            )
        if set(null_rates) != REQUIRED_EDA_COLUMN_SET:
            raise HMDADataValidationError(
                "EDA null rates do not cover all required columns"
            )
        for column in REQUIRED_EDA_COLUMNS:
            if (
                null_counts[column]
                != manifest.expected.required_column_null_counts[column]
            ):
                raise HMDADataValidationError(
                    f"EDA null count does not match manifest: {column}"
                )
            if not math.isclose(
                null_rates[column],
                manifest.null_rates[column],
                rel_tol=0,
                abs_tol=1e-9,
            ):
                raise HMDADataValidationError(
                    f"EDA null rate does not match manifest: {column}"
                )

        expected_year_counts = [
            item.model_dump() for item in manifest.expected.activity_year_counts
        ]
        if evidence["activity_year_counts"] != expected_year_counts:
            raise HMDADataValidationError(
                "EDA activity-year counts do not match manifest"
            )
        if len(evidence["activity_year_counts"]) != manifest.activity_year_cardinality:
            raise HMDADataValidationError(
                "EDA activity-year cardinality does not match manifest"
            )
        freshness = evidence["freshness"]
        if (
            freshness["status"] != manifest.expected.freshness.status
            or freshness["freshness_at"] != manifest.expected.freshness.freshness_at
        ):
            raise HMDADataValidationError("EDA freshness does not match manifest")
    except HMDADataValidationError:
        raise
    except (KeyError, TypeError, ValueError) as error:
        raise HMDADataValidationError(
            f"Invalid EDA evidence contract: {error}"
        ) from error
