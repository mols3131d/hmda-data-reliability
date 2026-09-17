"""Offline representative Review AI utility proof runner tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from hmda_reliability.review_ai.evaluation_store import UtilityEvidenceStore
from scripts.run_review_ai_utility_proof import (
    build_representative_utility_proof,
    main,
)

pytestmark = pytest.mark.component


def test_representative_fixture_proves_controls_and_comparison() -> None:
    bundle = build_representative_utility_proof(
        project_revision="  proof-test-revision  "
    )

    assert bundle.quality_basis.valid is True
    assert bundle.comparison.status == "compared"
    assert bundle.comparison.decision == "accept"
    assert bundle.comparison.total_delta > 0
    assert bundle.case.project_revision == "proof-test-revision"
    assert bundle.comparison.project_revision == "proof-test-revision"
    assert bundle.quality_basis.project_revision == "proof-test-revision"


def test_runner_writes_replayable_proof_bundle(tmp_path: Path) -> None:
    assert (
        main(
            [
                "--artifact-root",
                str(tmp_path),
                "--project-revision",
                "proof-test-revision",
            ]
        )
        == 0
    )

    bundle = UtilityEvidenceStore(tmp_path).load_proof("review-ai-utility-proof-v1")
    assert bundle.quality_basis.valid is True
    assert bundle.comparison.candidate_invocation_id == "utility-candidate"
