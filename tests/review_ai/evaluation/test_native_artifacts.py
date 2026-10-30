import json

import pytest

from hmda_reliability.review_ai.contracts import AgenticReviewInput
from hmda_reliability.review_ai.evaluation.artifacts import verify_local_result
from tests.review_ai.test_staged_service import TextProvider, response, run_review

pytestmark = pytest.mark.component


def test_verified_export_uses_raw_files_and_has_no_local_paths(
    null_spike_review_material, tmp_path
):
    material = null_spike_review_material
    result = run_review(material, tmp_path, TextProvider([response("답변")] * 3))
    source = AgenticReviewInput(
        incident=material.detection.incident,
        evidence=[material.detection.evidence],
        draft=material.draft,
        project_revision="revision-under-test",
    )
    packet = verify_local_result(result, source, tmp_path)
    assert [s["text"] for s in packet["stages"]] == ["답변"] * 3
    assert str(tmp_path) not in json.dumps(packet, ensure_ascii=False)
    result.stages[0].response_path.write_text("변조")
    with pytest.raises(ValueError):
        verify_local_result(result, source, tmp_path)


def test_partial_failure_retains_returned_text_for_native_review(
    null_spike_review_material, tmp_path
):

    material = null_spike_review_material
    provider = TextProvider(
        [response("앞선 답변"), response("미완료 원문", finish_reason="length")]
    )
    result = run_review(material, tmp_path, provider)
    source = AgenticReviewInput(
        incident=material.detection.incident,
        evidence=[material.detection.evidence],
        draft=material.draft,
        project_revision="revision-under-test",
    )
    packet = verify_local_result(result, source, tmp_path)
    assert result.status == "validation_failed"
    assert packet["stages"][1]["text"] == "미완료 원문"
    assert packet["output"] is None
