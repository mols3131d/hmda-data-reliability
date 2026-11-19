"""준비 판정을 호출자가 지정한 로더 입력과 파일별 내용에 결합한다."""

import hashlib
import json
from pathlib import Path

import duckdb
import pytest

from hmda_reliability.data_operations.request import DataOperationRequest
from hmda_reliability.reliability_ai.ingestion.source import inspect_inputs

pytestmark = pytest.mark.component
HEADER = (
    "activity_year,loan_purpose,action_taken,loan_amount,"
    "income,state_code,county_code\n"
)
ROW = "2020,1,1,500,42,06,002\n"


@pytest.mark.parametrize("kind", ["csv", "parquet"])
def test_prepare_counts_by_filename_with_loader_rules(
    tmp_path: Path, kind: str
) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    path = raw / f"loans_2025.{kind}"
    if kind == "csv":
        path.write_text(HEADER + ROW * 2)
    else:
        with duckdb.connect() as con:
            con.execute(
                "CREATE TABLE x AS SELECT 2020 activity_year, 1 loan_purpose, "
                "1 action_taken, 500 loan_amount, 42 income, '06' state_code, "
                "'002' county_code FROM range(2)"
            )
            con.execute("COPY x TO ? (FORMAT PARQUET)", [str(path)])
    original = path.read_bytes()
    req = DataOperationRequest(
        source_root=raw, database_path=tmp_path / "bronze.duckdb"
    )
    facts = inspect_inputs(req, deadline=float("inf"))
    manifest = [[path.name, hashlib.sha256(original).hexdigest()]]
    assert (
        facts["version"]
        == hashlib.sha256(
            json.dumps(manifest, separators=(",", ":"), ensure_ascii=False).encode()
        ).hexdigest()
    )
    assert (facts["status"], facts["row_count"]) == ("ready", 2)
    assert path.read_bytes() == original
    assert not req.database_path.exists()


def test_prepare_checks_other_input_even_with_file_filter(tmp_path: Path) -> None:
    target = tmp_path / "part2025.csv"
    target.write_text(HEADER + ROW)
    (tmp_path / "part2024.csv").write_text("activity_year,income\n2024,100\n")
    req = DataOperationRequest(source_root=tmp_path, source_file=target.name)
    facts = inspect_inputs(req, deadline=float("inf"))
    assert facts["status"] == "blocked"
    assert "loan_amount" in facts["sources"][0]["missing_columns"]


def test_confirmed_empty_and_unreadable_are_distinct(tmp_path: Path) -> None:
    req = DataOperationRequest(source_root=tmp_path)
    assert inspect_inputs(req, deadline=float("inf"))["status"] == "blocked"
    req = req.model_copy(update={"source_root": tmp_path / "absent"})
    assert inspect_inputs(req, deadline=float("inf"))["status"] == "needs_human"


def test_symlink_cannot_expand_declared_input(tmp_path: Path) -> None:
    root = tmp_path / "raw"
    root.mkdir()
    secret = tmp_path / "outside.csv"
    secret.write_text(HEADER + ROW)
    (root / "loans2025.csv").symlink_to(secret)
    assert (
        inspect_inputs(DataOperationRequest(source_root=root), deadline=float("inf"))[
            "status"
        ]
        == "needs_human"
    )


def test_parse_failure_vs_empty_target(tmp_path: Path) -> None:
    source = tmp_path / "loans2024.csv"
    source.write_text(HEADER + ROW)
    req = DataOperationRequest(source_root=tmp_path)
    assert inspect_inputs(req, deadline=float("inf"))["reason"] == "empty_partition"
    source.unlink()
    (tmp_path / "loans2025.parquet").write_bytes(b"this is invalid parquet data")
    evidence = inspect_inputs(req, deadline=float("inf"))
    assert (evidence["status"], evidence["reason"]) == ("blocked", "parse_failed")


@pytest.mark.parametrize(
    ("late_index", "expected"), [(0, "needs_human"), (1, "blocked")]
)
def test_missing_column_evidence_must_arrive_before_deadline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, late_index: int, expected: str
) -> None:
    from hmda_reliability.hmda_data.ingestion._common import (
        validate_source_required_columns,
    )
    from hmda_reliability.reliability_ai.ingestion import source

    for name in ("a_2025.csv", "b_2025.csv"):
        (tmp_path / name).write_text("income\n10\n")
    now = 0.0
    calls = 0

    def schema(conn: duckdb.DuckDBPyConnection, paths: list[Path]) -> None:
        nonlocal now, calls
        try:
            validate_source_required_columns(conn, paths)
        finally:
            if calls == late_index:
                now = 4.0
            calls += 1

    monkeypatch.setattr(source, "validate_source_required_columns", schema)
    result = inspect_inputs(
        DataOperationRequest(source_root=tmp_path), deadline=4.0, clock=lambda: now
    )
    assert result["status"] == expected
    assert len(result["sources"]) == late_index
