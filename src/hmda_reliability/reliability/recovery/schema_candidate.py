"""테이블 스키마 복구를 위한 사전 점검(preflight) 모듈."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import duckdb
from pydantic import Field, model_validator

from hmda_reliability.data_platform.duckdb import (
    DuckDBConnectionManager,
    DuckDBMutationLockError,
    database_mutation_lock,
)
from hmda_reliability.data_platform.sql import (
    qualify_table_name,
    quote_identifier,
    quote_string_literal,
)
from hmda_reliability.reliability.contracts import (
    ReliabilityContract,
    TableStateIdentity,
)
from hmda_reliability.reliability.errors import (
    SchemaRecoveryCandidateError,
    TableStateIdentityError,
)
from hmda_reliability.reliability.profiling import create_table_state_identity

if TYPE_CHECKING:
    from hmda_reliability.data_operations.dbt_result import DbtBuildResult


class SchemaRecoveryCandidateEvidence(ReliabilityContract):
    """불변의 완전한 후보 상태 및 downstream dbt evidence."""

    candidate_state: TableStateIdentity
    dbt_projection_id: str = Field(min_length=1)
    validation_evidence_refs: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_projection_evidence(self) -> SchemaRecoveryCandidateEvidence:
        if self.validation_evidence_refs[-1] != self.dbt_projection_id:
            raise ValueError(
                "마지막 validation evidence는 dbt projection이어야 합니다."
            )
        return self


class StagedSchemaRecoveryCandidate(ReliabilityContract):
    """승인된 상태와 일치하는 스테이징된 Parquet 아티팩트 계약."""

    artifact_path: Path
    candidate_state: TableStateIdentity


def preflight_schema_recovery_candidate(
    connection: duckdb.DuckDBPyConnection,
    *,
    expected_after_state: TableStateIdentity,
    dbt_result: DbtBuildResult,
) -> SchemaRecoveryCandidateEvidence:
    """대상 데이터베이스 변경 전에 격리된 후보 데이터베이스 상태를 사전 점검한다."""

    if (
        not dbt_result.succeeded
        or dbt_result.return_code != 0
        or not dbt_result.projection_id.strip()
    ):
        raise SchemaRecoveryCandidateError(
            "candidate dbt validation이 성공하지 않았습니다.",
            context={
                "return_code": dbt_result.return_code,
                "succeeded": dbt_result.succeeded,
                "projection_id": dbt_result.projection_id,
            },
        )
    try:
        candidate_state = create_table_state_identity(
            connection,
            expected_after_state.table_name,
        )
    except TableStateIdentityError as exc:
        raise SchemaRecoveryCandidateError(
            "candidate table state를 검증할 수 없습니다.",
            context={"table_name": expected_after_state.table_name},
        ) from exc
    if candidate_state != expected_after_state:
        expected_years = {
            identity.source_year
            for identity in expected_after_state.partition_identities
        }
        candidate_years = {
            identity.source_year for identity in candidate_state.partition_identities
        }
        raise SchemaRecoveryCandidateError(
            "candidate table state가 expected after state와 다릅니다.",
            context={
                "table_name": expected_after_state.table_name,
                "expected_state": expected_after_state.model_dump(mode="json"),
                "candidate_state": candidate_state.model_dump(mode="json"),
                "missing_source_years": sorted(expected_years - candidate_years),
                "unexpected_source_years": sorted(candidate_years - expected_years),
            },
        )
    evidence_refs = (
        candidate_state.schema_hash,
        *(identity.digest for identity in candidate_state.partition_identities),
        dbt_result.projection_id,
    )
    return SchemaRecoveryCandidateEvidence(
        candidate_state=candidate_state,
        dbt_projection_id=dbt_result.projection_id,
        validation_evidence_refs=evidence_refs,
    )


def stage_approved_schema_recovery_candidate(
    *,
    candidate_database_path: str | Path,
    approved_candidate_state: TableStateIdentity,
    staging_directory: str | Path,
) -> StagedSchemaRecoveryCandidate:
    """Export and revalidate the exact approved candidate under its mutation lock."""

    database_path = Path(candidate_database_path)
    staging_root = Path(staging_directory)
    artifact_path = staging_root / "approved-candidate.parquet"
    if not database_path.is_file():
        raise SchemaRecoveryCandidateError(
            "approved candidate database를 찾을 수 없습니다.",
            context={"candidate_database_path": str(database_path)},
        )
    try:
        with (
            database_mutation_lock(database_path),
            DuckDBConnectionManager(database_path) as connection,
        ):
            current_state = create_table_state_identity(
                connection,
                approved_candidate_state.table_name,
            )
            if current_state != approved_candidate_state:
                raise SchemaRecoveryCandidateError(
                    "approved candidate state가 approval 이후 변경되었습니다.",
                    context={
                        "approved_candidate_state": (
                            approved_candidate_state.model_dump(mode="json")
                        ),
                        "current_candidate_state": current_state.model_dump(
                            mode="json"
                        ),
                    },
                )
            staging_root.mkdir(parents=True, exist_ok=True)
            artifact_path.unlink(missing_ok=True)
            connection.execute(
                f"COPY {qualify_table_name(approved_candidate_state.table_name)} "
                f"TO {quote_string_literal(artifact_path.as_posix())} "
                "(FORMAT PARQUET)"
            )
            staged_state = _staged_table_state(
                artifact_path,
                approved_candidate_state.table_name,
            )
            if staged_state != approved_candidate_state:
                raise SchemaRecoveryCandidateError(
                    "staged candidate state가 approved candidate와 다릅니다.",
                    context={
                        "approved_candidate_state": (
                            approved_candidate_state.model_dump(mode="json")
                        ),
                        "staged_candidate_state": staged_state.model_dump(mode="json"),
                    },
                )
    except SchemaRecoveryCandidateError:
        artifact_path.unlink(missing_ok=True)
        raise
    except (DuckDBMutationLockError, OSError, duckdb.Error) as exc:
        artifact_path.unlink(missing_ok=True)
        raise SchemaRecoveryCandidateError(
            "approved candidate를 staging할 수 없습니다.",
            context={
                "candidate_database_path": str(database_path),
                "artifact_path": str(artifact_path),
            },
        ) from exc
    return StagedSchemaRecoveryCandidate(
        artifact_path=artifact_path,
        candidate_state=staged_state,
    )


def _staged_table_state(
    artifact_path: Path,
    table_name: str,
) -> TableStateIdentity:
    schema_name, separator, _ = table_name.partition(".")
    if not separator:
        raise SchemaRecoveryCandidateError(
            "schema recovery target은 schema-qualified table이어야 합니다.",
            context={"table_name": table_name},
        )
    with DuckDBConnectionManager() as connection:
        connection.execute(f"CREATE SCHEMA {quote_identifier(schema_name)}")
        connection.execute(
            f"CREATE VIEW {qualify_table_name(table_name)} AS "
            "SELECT * FROM read_parquet("
            f"{quote_string_literal(artifact_path.as_posix())})"
        )
        return create_table_state_identity(connection, table_name)
