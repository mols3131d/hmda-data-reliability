"""합성 결함 query 결과를 case-scoped Parquet output으로 materialize한다."""

from __future__ import annotations

import shutil
from pathlib import Path

import duckdb

from project_pivot.data_platform.sql import quote_string_literal
from project_pivot.hmda_data.errors import SyntheticCaseError
from project_pivot.logger import get_logger

_LOGGER = get_logger(__name__)


def write_case_file(
    *,
    connection: duckdb.DuckDBPyConnection,
    case_name: str,
    output_root: str | Path,
    query: str,
    params: list[object],
) -> Path:
    """Case output을 단일 Parquet으로 쓰고 생성된 path를 반환한다.

    동일 ``case_name`` directory가 이미 있으면 새 결과를 쓰기 전에 directory 전체를
    삭제한다. ``case_name``은 ``output_root`` 밖을 가리킬 수 없는 단일 이름이어야 한다.
    """

    case_dir = _prepare_case_dir(output_root, case_name)
    target_path = case_dir / f"{case_name}.parquet"
    try:
        connection.execute(
            f"""
            COPY ({query})
            TO {quote_string_literal(str(target_path))}
            (FORMAT PARQUET)
            """,
            params,
        )
    except duckdb.Error as exc:
        msg = (
            "HMDA 합성 결함 파일 생성에 실패했습니다: "
            f"case={case_name}, output_root={output_root}"
        )
        raise SyntheticCaseError(msg, context={"case_name": case_name}) from exc
    _LOGGER.debug(
        "HMDA 합성 결함 파일 생성 완료",
        extra={"case_name": case_name, "target_path": str(target_path)},
    )
    return target_path


def _prepare_case_dir(output_root: str | Path, case_name: str) -> Path:
    """Output root 내부의 case directory만 허용하고 기존 directory를 교체한다."""

    if not case_name or case_name in {".", ".."} or Path(case_name).name != case_name:
        msg = "case_name은 단일 디렉터리 이름이어야 합니다."
        raise SyntheticCaseError(msg, context={"case_name": case_name})
    case_dir = Path(output_root) / case_name
    if case_dir.exists():
        shutil.rmtree(case_dir)
    case_dir.mkdir(parents=True, exist_ok=True)
    return case_dir
