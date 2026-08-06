"""Evidence atomic write test."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.run_actual_source import write_evidence

pytestmark = pytest.mark.component


def test_write_evidence_cleans_up_new_json_on_first_creation_second_replace_failure(
    tmp_path: Path,
) -> None:
    """최초 생성 시 replace 실패하면 신규 json_path가 삭제된다."""
    import os

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
