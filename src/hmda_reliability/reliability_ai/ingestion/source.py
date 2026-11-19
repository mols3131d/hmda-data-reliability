"""허용된 파일을 고정하고 실제 적재와 같은 파서로 준비 상태를 판정한다."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import stat
import tempfile
import time
from collections.abc import Callable
from contextlib import ExitStack
from pathlib import Path
from threading import Timer
from typing import Any

import duckdb

from hmda_reliability.data_operations.request import DataOperationRequest
from hmda_reliability.hmda_data.errors import HMDADataValidationError
from hmda_reliability.hmda_data.ingestion._common import (
    validate_source_required_columns,
)
from hmda_reliability.hmda_data.ingestion.partition import inspect_partition_rows


def _identity(s: os.stat_result) -> tuple[int, int, int, int, int]:
    return s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns


def _files(
    directory: Path, check_time: Callable[[], None]
) -> dict[str, tuple[int, ...]]:
    files = {}
    for path in directory.iterdir():
        check_time()
        if path.suffix.lower() not in {".csv", ".parquet"}:
            continue
        info = path.lstat()
        if stat.S_ISLNK(info.st_mode):
            raise OSError("source_symlink")
        if stat.S_ISREG(info.st_mode):
            files[path.name] = _identity(info)
    return dict(sorted(files.items()))


def inspect_inputs(
    request: DataOperationRequest,
    *,
    deadline: float,
    clock: Callable[[], float] = time.monotonic,
) -> dict[str, Any]:
    """원천·Bronze에 쓰지 않고, 읽을 수 있었던 동일 버전의 근거만 반환한다."""

    def check_time() -> None:
        if clock() >= deadline:
            raise TimeoutError

    facts: dict[str, Any] = {
        "status": "needs_human",
        "version": None,
        "sources": [],
        "row_count": None,
        "parse_status": "not_checked",
        "reason": "source_unavailable",
    }
    try:
        check_time()
        files = _files(request.source_root, check_time)
        with tempfile.TemporaryDirectory() as snapshot:
            paths: list[Path] = []
            manifest: list[tuple[str, str]] = []
            for name, signature in files.items():
                check_time()
                digest = hashlib.sha256()
                path = Path(snapshot) / name
                with (
                    os.fdopen(
                        os.open(
                            request.source_root / name,
                            os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                        ),
                        "rb",
                    ) as source,
                    path.open("xb") as out,
                ):
                    if _identity(os.fstat(source.fileno())) != signature:
                        raise OSError("source_changed")
                    while chunk := source.read(1024 * 1024):
                        check_time()
                        digest.update(chunk)
                        out.write(chunk)
                manifest.append((name, digest.hexdigest()))
                paths.append(path)
            check_time()
            if files != _files(request.source_root, check_time):
                raise OSError("source_changed")
            version = hashlib.sha256(
                json.dumps(manifest, ensure_ascii=False, separators=(",", ":")).encode()
            ).hexdigest()
            check_time()
            facts["version"] = version
            if not paths:
                return {**facts, "status": "blocked", "reason": "empty_source"}
            with duckdb.connect(":memory:") as conn, ExitStack() as cleanup:
                remaining = deadline - clock()
                if remaining <= 0:
                    raise TimeoutError
                if math.isfinite(remaining):
                    timer = Timer(remaining, conn.interrupt)
                    timer.daemon = True
                    timer.start()
                    cleanup.callback(timer.join)
                    cleanup.callback(timer.cancel)
                for number, path in enumerate(paths):
                    check_time()
                    missing: list[str] = []
                    try:
                        validate_source_required_columns(conn, [path])
                    except HMDADataValidationError as exc:
                        missing = exc.context["missing_columns"]
                    check_time()
                    year = re.search(r"\d{4}", path.name)
                    facts["sources"].append(
                        {
                            "source_id": f"source-{number + 1}",
                            "name": path.name,
                            "format": path.suffix[1:].lower(),
                            "source_year": int(year[0]) if year else None,
                            "missing_columns": missing,
                        }
                    )
                    if missing:
                        facts.update(status="blocked", reason="missing_columns")
                if facts["status"] == "blocked":
                    return facts
                count = inspect_partition_rows(
                    conn, paths, request.source_year, request.source_file
                )
                check_time()
                return {
                    **facts,
                    "row_count": count,
                    "parse_status": "passed",
                    "status": "ready" if count else "blocked",
                    "reason": "verified" if count else "empty_partition",
                }
    except (TimeoutError, duckdb.InterruptException):
        if facts["status"] != "blocked":
            facts["reason"] = "workflow_budget_exhausted"
        return facts
    except (
        duckdb.ConversionException,
        duckdb.InvalidInputException,
        duckdb.BinderException,
    ):
        if clock() >= deadline:
            if facts["status"] != "blocked":
                facts["reason"] = "workflow_budget_exhausted"
            return facts
        return {
            **facts,
            "status": "blocked",
            "reason": "parse_failed",
            "parse_status": "failed",
        }
    except (OSError, duckdb.Error):
        return facts
