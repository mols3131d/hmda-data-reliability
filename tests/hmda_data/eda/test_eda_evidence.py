"""HMDA EDA actual-source evidence 수집, provenance 및 atomic write 검증 테스트."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import cast
from unittest.mock import patch

import pytest

import scripts.run_actual_source as actual_source
from scripts.run_actual_source import (
    EvidenceProvenanceError,
    _repository_revision,
    write_evidence,
)

pytestmark = pytest.mark.component


@pytest.fixture(autouse=True)
def _clean_git_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in list(os.environ):
        if key.startswith("GIT_"):
            monkeypatch.delenv(key, raising=False)


def test_write_evidence_generates_consistent_json_and_markdown(tmp_path: Path) -> None:
    """단일 evidence 객체에서 일치하는 JSON과 Markdown을 생성한다."""
    evidence = {
        "row_count": 1000,
        "duration_seconds": 1.23,
        "null_counts": {"income": 50},
        "grain": {"distinct_group_count": 327},
        "source": {
            "path": "/machine-specific/path/year_2025.csv",
            "duckdb_config": {"temp_directory": "/machine-specific/tmp"},
        },
    }

    json_path = tmp_path / "reference.json"
    markdown_path = tmp_path / "reference.md"

    write_evidence(
        evidence,
        json_path=json_path,
        markdown_path=markdown_path,
        source_id="year_2025.csv",
        source_sha256="4a3226c6a86e61ec1e49509f39dfe9986e969b37808408df5f7eddbde3d7561f",
        repository_revision="abc123",
        observed_at="2026-08-06T00:00:00+00:00",
    )

    assert json_path.exists()
    assert markdown_path.exists()

    json_data = json.loads(json_path.read_text(encoding="utf-8"))
    assert json_data["source_id"] == "year_2025.csv"
    assert json_data["source_sha256"] == (
        "4a3226c6a86e61ec1e49509f39dfe9986e969b37808408df5f7eddbde3d7561f"
    )
    assert json_data["repository_revision"] == "abc123"
    assert json_data["observed_at"] == "2026-08-06T00:00:00+00:00"
    assert json_data["evidence"]["row_count"] == 1000

    md_text = markdown_path.read_text(encoding="utf-8")
    assert "Total Row Count: 1,000" in md_text
    assert "Income Null Count: 50" in md_text
    assert "Mart Grain Distinct Group Count: 327" in md_text
    assert "/machine-specific" not in json_path.read_text(encoding="utf-8")
    assert "/machine-specific" not in md_text


def test_repository_revision_returns_exact_head_when_clean(tmp_path: Path) -> None:
    """Clean repository에서 _repository_revision은 HEAD revision만 반환한다."""
    subprocess.run(["git", "init"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True
    )

    (tmp_path / "file.txt").write_text("hello", encoding="utf-8")
    subprocess.run(["git", "add", "file.txt"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=tmp_path, check=True)

    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    rev = _repository_revision(tmp_path)
    assert rev == head
    assert "-dirty" not in rev


@pytest.mark.parametrize(
    "setup_action",
    [
        "unstaged",
        "staged",
        "untracked",
    ],
)
def test_repository_revision_raises_on_dirty_tree(
    tmp_path: Path, setup_action: str
) -> None:
    """git status --porcelain 기준 변경이 있으면 EvidenceProvenanceError를 던진다."""
    subprocess.run(["git", "init"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True
    )

    tracked_file = tmp_path / "tracked.txt"
    tracked_file.write_text("v1", encoding="utf-8")
    subprocess.run(["git", "add", "tracked.txt"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=tmp_path, check=True)

    if setup_action == "unstaged":
        tracked_file.write_text("v2", encoding="utf-8")
    elif setup_action == "staged":
        tracked_file.write_text("v2", encoding="utf-8")
        subprocess.run(["git", "add", "tracked.txt"], cwd=tmp_path, check=True)
    elif setup_action == "untracked":
        (tmp_path / "new_untracked.txt").write_text("untracked", encoding="utf-8")

    with pytest.raises(EvidenceProvenanceError, match="dirty"):
        _repository_revision(tmp_path)


def test_write_evidence_cleans_up_new_json_on_first_creation_second_replace_failure(
    tmp_path: Path,
) -> None:
    """최초 생성 시 replace 실패하면 신규 json_path가 삭제된다."""
    json_path = tmp_path / "evidence.json"
    md_path = tmp_path / "evidence.md"

    evidence = {
        "row_count": 100,
        "duration_seconds": 0.5,
        "null_counts": {"income": 0},
        "grain": {"distinct_group_count": 10},
    }

    original_replace = os.replace
    call_count = 0

    def mock_replace(src: str | Path, dst: str | Path) -> None:
        nonlocal call_count
        call_count += 1
        if call_count == 2:
            raise OSError("Simulated second replace failure")
        original_replace(src, dst)

    with (
        patch("os.replace", side_effect=mock_replace),
        pytest.raises(OSError, match="Simulated second replace failure"),
    ):
        write_evidence(
            evidence,
            json_path=json_path,
            markdown_path=md_path,
            source_id="test.csv",
            source_sha256="dummy_hash",
            repository_revision="head_sha",
            observed_at="2026-08-07T00:00:00Z",
        )

    assert not json_path.exists()
    assert not md_path.exists()


def test_main_preserves_actual_source_analysis_and_provenance_contract(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """CLI main binds the configured source, analysis limits, and evidence metadata."""
    source_path = tmp_path / "data" / "year_2025.csv"
    json_path = tmp_path / "docs" / "reference.json"
    markdown_path = tmp_path / "docs" / "reference.md"
    observed: dict[str, object] = {}

    monkeypatch.setattr(actual_source, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(actual_source, "SOURCE_PATH", source_path)
    monkeypatch.setattr(actual_source, "JSON_PATH", json_path)
    monkeypatch.setattr(actual_source, "MARKDOWN_PATH", markdown_path)

    def fake_analyze_hmda_csv(**kwargs: object) -> dict[str, object]:
        observed["analysis"] = kwargs
        return {
            "source": {
                "scope": "full_file",
                "csv_options": {"header": True},
            }
        }

    def fake_write_evidence(
        evidence: dict[str, object],
        **kwargs: object,
    ) -> None:
        observed["evidence"] = evidence
        observed["write"] = kwargs

    monkeypatch.setattr(actual_source, "analyze_hmda_csv", fake_analyze_hmda_csv)
    monkeypatch.setattr(actual_source, "_sha256", lambda _path: "source-sha")
    monkeypatch.setattr(
        actual_source,
        "_repository_revision",
        lambda _root: "revision-sha",
    )
    monkeypatch.setattr(actual_source, "write_evidence", fake_write_evidence)

    actual_source.main()

    assert observed["analysis"] == {
        "source_path": source_path,
        "memory_limit": "2GB",
        "threads": 2,
        "temp_directory": tmp_path / ".tmp",
    }
    assert observed["evidence"] == {
        "source": {
            "id": "data/year_2025.csv",
            "scope": "full_file",
            "csv_options": {"header": True},
        }
    }
    write = cast(dict[str, object], observed["write"])
    assert write["json_path"] == json_path
    assert write["markdown_path"] == markdown_path
    assert write["source_id"] == "data/year_2025.csv"
    assert write["source_sha256"] == "source-sha"
    assert write["repository_revision"] == "revision-sha"
    assert isinstance(write["observed_at"], str)
