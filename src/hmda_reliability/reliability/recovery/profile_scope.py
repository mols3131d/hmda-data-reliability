"""복구의 numeric year observation과 profile population 정합성 검증."""

from pathlib import Path

import duckdb

from hmda_reliability.data_platform.sql import qualify_table_name
from hmda_reliability.reliability.errors import ApprovalGateError
from hmda_reliability.reliability.profiling import ProfileSnapshotRequest


def ensure_recovery_profile_population(
    connection: duckdb.DuckDBPyConnection,
    request: ProfileSnapshotRequest,
    *,
    artifact_path: Path | None = None,
) -> None:
    """승인된 year와 profile 표현이 다른 행을 선택하면 mutation 전에 거부한다."""

    relation = qualify_table_name(request.table_name)
    parameters: list[object] = []
    if artifact_path is not None:
        relation = "read_parquet(?)"
        parameters.append(artifact_path.as_posix())
    parameters.extend((str(request.partition), str(request.partition)))
    try:
        mismatch = connection.execute(
            f"""
            SELECT EXISTS (
                SELECT 1 FROM {relation}
                WHERE (source_year = CAST(? AS BIGINT)) IS DISTINCT FROM
                    (CAST(source_year AS VARCHAR) = ?)
            )
            """,
            parameters,
        ).fetchone()
    except duckdb.CatalogException:
        if artifact_path is None:
            return
        raise
    if mismatch is not None and mismatch[0]:
        raise ApprovalGateError(
            "recovery profile population이 승인된 source_year observation과 다릅니다."
        )
