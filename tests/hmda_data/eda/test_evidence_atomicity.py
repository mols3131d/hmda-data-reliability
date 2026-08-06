"""Evidence atomic write test."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.run_actual_source import write_evidence

pytestmark = pytest.mark.component


def test_write_evidence_atomic_failure_preserves_existing_artifacts(
    tmp_path: Path,
) -> None:
    """Markdown 작성 또는 atomic replace 실패 시 기존 artifact가 원본 보존된다."""
    json_path = tmp_path / "evidence.json"
    md_path = tmp_path / "evidence.md"

    json_path.write_text("ORIGINAL JSON", encoding="utf-8")
    md_path.write_text("ORIGINAL MD", encoding="utf-8")

    evidence = {
        "row_count": 100,
        "duration_seconds": 0.5,
        "null_counts": {"income": 0},
        "grain": {"distinct_group_count": 10},
    }

    def failing_write(*args: object, **kwargs: object) -> None:
        raise OSError("Disk full during markdown write")

    with (
        patch("pathlib.Path.write_text", side_effect=failing_write),
        pytest.raises(OSError, match="Disk full"),
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

    assert json_path.read_text(encoding="utf-8") == "ORIGINAL JSON"
    assert md_path.read_text(encoding="utf-8") == "ORIGINAL MD"
