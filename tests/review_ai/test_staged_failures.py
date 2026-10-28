"""호출 전 identity 충돌 거부와 custom provider의 UTF-8 저장 실패 경계."""

from __future__ import annotations

from pathlib import Path

import pytest

from hmda_reliability.runtime_ai.contracts import ProviderResponse

from .conftest import NullSpikeReviewMaterial
from .test_staged_service import TEXTS, TextProvider, response, run_review


@pytest.mark.component
@pytest.mark.parametrize("collision", ["legacy_record", "dangling_response"])
def test_existing_stage_identity_is_rejected_before_any_provider_call(
    null_spike_review_material: NullSpikeReviewMaterial,
    tmp_path: Path,
    collision: str,
) -> None:
    directory = "invocations" if collision == "legacy_record" else "responses"
    suffix = ".json" if collision == "legacy_record" else ".txt"
    path = tmp_path / "agentic-review" / directory / f"sr-unit-synthesis{suffix}"
    path.parent.mkdir(parents=True)
    if collision == "legacy_record":
        path.write_text("{}", encoding="utf-8")
    else:
        path.symlink_to(tmp_path / "missing-response-target")
        assert not path.exists()
    provider = TextProvider([response(text) for text in TEXTS])

    result = run_review(null_spike_review_material, tmp_path, provider)

    assert provider.calls == []
    assert result.status == "provenance_failed"
    assert result.failure_code == "workflow_reservation_failed"
    assert result.stages == ()
    assert not (tmp_path / "agentic-review" / "staged" / "sr-unit").exists()
    if collision == "legacy_record":
        assert path.read_text(encoding="utf-8") == "{}"
    else:
        assert path.is_symlink()
        assert path.readlink() == tmp_path / "missing-response-target"


@pytest.mark.component
def test_unencodable_custom_provider_answer_retains_prior_checkpoint_and_fails_typed(
    null_spike_review_material: NullSpikeReviewMaterial,
    tmp_path: Path,
) -> None:
    provider = TextProvider(
        [
            response(TEXTS[0]),
            ProviderResponse(content="\ud800", attempt_count=1, latency_ms=1.0),
        ]
    )

    result = run_review(null_spike_review_material, tmp_path, provider)

    assert result.status == "provenance_failed"
    assert result.failure_code == "stage_response_write_failed"
    assert len(provider.calls) == 2
    assert result.output is None and result.output_path is None
    assert result.workflow_path is not None and result.workflow_path.is_file()
    first, second = result.stages
    assert first.status == "completed"
    assert first.response_path is not None
    assert first.response_path.read_bytes() == TEXTS[0].encode("utf-8")
    assert first.record_path is not None and first.record_path.is_file()
    assert second.status == "provenance_failed"
    assert second.failure_code == "stage_response_write_failed"
    assert second.attempt_count == 1
    assert second.response_path is None and second.response_digest is None
    assert second.record_path is not None and second.record_path.is_file()
