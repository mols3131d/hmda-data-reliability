"""합성 결함 query 결과를 case-scoped Parquet output으로 materialize한다."""

from __future__ import annotations

import shutil
from collections.abc import Iterator, Sequence
from pathlib import Path

import duckdb

from hmda_reliability.data_platform.sql import quote_string_literal
from hmda_reliability.hmda_data.errors import SyntheticCaseError
from hmda_reliability.logger import get_logger

_LOGGER = get_logger(__name__)


def write_case_file(
    *,
    connection: duckdb.DuckDBPyConnection,
    case_name: str,
    output_root: str | Path,
    source_paths: Sequence[str | Path],
    query: str,
    params: list[object],
) -> Path:
    """Case output을 단일 Parquet으로 쓰고 생성된 path를 반환한다.

    동일 ``case_name`` directory가 있으면 ``COPY`` 전에 directory 전체를 삭제한다.
    새 write가 실패해도 이전 case output은 복구하지 않는다. ``case_name``은
    ``output_root`` 밖을 가리킬 수 없는 단일 이름이어야 한다. 삭제 범위 안에
    source file이 있으면 기존 파일을 변경하지 않고 ``SyntheticCaseError``로 거부한다.
    """

    case_dir = _prepare_case_dir(connection, output_root, case_name, source_paths)
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


def _prepare_case_dir(
    connection: duckdb.DuckDBPyConnection,
    output_root: str | Path,
    case_name: str,
    source_paths: Sequence[str | Path],
) -> Path:
    """Output root 내부의 case directory만 허용하고 기존 directory를 교체한다."""

    if not case_name or case_name in {".", ".."} or Path(case_name).name != case_name:
        msg = "case_name은 단일 디렉터리 이름이어야 합니다."
        raise SyntheticCaseError(msg, context={"case_name": case_name})
    case_dir = Path(output_root) / case_name
    _validate_source_paths(connection, source_paths, case_dir)
    if case_dir.exists():
        shutil.rmtree(case_dir)
    case_dir.mkdir(parents=True, exist_ok=True)
    return case_dir


def _validate_source_paths(
    connection: duckdb.DuckDBPyConnection,
    source_paths: Sequence[str | Path],
    case_dir: Path,
) -> None:
    """Reader가 선택한 파일과 입력 경로의 링크를 삭제 범위에서 보호한다."""

    resolved_case_dir = case_dir.resolve()
    for source_path in source_paths:
        try:
            matches = connection.execute(
                "SELECT file FROM glob(?)", [Path(source_path).as_posix()]
            ).fetchall()
        except duckdb.Error as exc:
            msg = "HMDA 합성 원천 경로 조회에 실패했습니다."
            raise SyntheticCaseError(
                msg, context={"source_path": str(source_path)}
            ) from exc
        for match in matches:
            path = Path(str(match[0]))
            # Case directory 자체는 재생성되지만 그 안의 경로와 링크는 삭제된다.
            if path.resolve().is_relative_to(resolved_case_dir) or any(
                entry != resolved_case_dir and entry.is_relative_to(resolved_case_dir)
                for entry in _source_path_entries(path)
            ):
                msg = "합성 출력 디렉터리에 포함된 원천 경로는 삭제할 수 없습니다."
                raise SyntheticCaseError(
                    msg,
                    context={"source_path": str(path), "case_dir": str(case_dir)},
                )


def _source_path_entries(path: Path) -> Iterator[Path]:
    """입력 해석에 쓰이는 실제 경로와 중간 symlink entry를 모두 순회한다."""

    pending = [path]
    visited: set[Path] = set()
    while pending:
        entry = pending.pop()
        if entry in visited:
            continue
        visited.add(entry)
        if entry.parent != entry:
            pending.append(entry.parent)
        if entry.is_symlink():
            yield entry.parent.resolve() / entry.name
            target = entry.readlink()
            pending.append(target if target.is_absolute() else entry.parent / target)
        else:
            yield entry.resolve()
