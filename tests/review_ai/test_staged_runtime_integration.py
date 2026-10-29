"""실제 SDK wire부터 단계별 원문·코드 JSON까지 연결하는 회귀."""

from __future__ import annotations

import json
from functools import partial
from pathlib import Path

import httpx
import pytest
from openai import OpenAI

from hmda_reliability.review_ai.evaluation import live as live_module
from hmda_reliability.review_ai.staged.evidence import StagedReviewResult
from hmda_reliability.runtime_ai import provider as provider_module
from tests.review_ai.test_live_harness import _live_environment


@pytest.mark.integration
@pytest.mark.parametrize("second_finish", ["stop", "length"])
def test_staged_live_runs_real_sdk_history_and_mechanically_collects_text(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    second_finish: str,
) -> None:
    environment = _live_environment(tmp_path)
    environment["HMDA_AGENTIC_REVIEW_MAX_RETRIES"] = "0"
    texts = (
        '  근거 검토: "관측"을 확인한다.\n',
        '초안 비판: {"kind": "이 문자열도 그대로 보존"}\n',
        "종합: 검증 결과가 없어 사람의 확인이 필요하다.\n",
    )
    payloads: list[dict[str, object]] = []

    def respond(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        assert "response_format" not in payload
        index = len(payloads)
        payloads.append(payload)
        assistants = [
            item["content"]
            for item in payload["messages"]
            if item["role"] == "assistant"
        ]
        assert assistants == list(texts[:index])
        return httpx.Response(
            200,
            json={
                "id": f"stage-{index}",
                "object": "chat.completion",
                "created": 0,
                "model": "test-model",
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": texts[index]},
                        "finish_reason": second_finish if index == 1 else "stop",
                    }
                ],
            },
        )

    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        monkeypatch.setattr(
            provider_module, "OpenAI", partial(OpenAI, http_client=client)
        )
        exit_code = live_module.main(env=environment)

    captured = capsys.readouterr()
    result = StagedReviewResult.model_validate_json(captured.out)
    assert "단계 1/3 근거 검토 시작" in captured.err
    assert "단계 1/3 근거 검토 수집·저장 완료" in captured.err
    assert all(text not in captured.out for text in texts)
    assert result.workflow_path is not None
    manifest = json.loads(result.workflow_path.read_text(encoding="utf-8"))
    if second_finish == "length":
        assert "단계 2/3 초안 검토 실패 (validation_failed)" in captured.err
        assert "단계 3/3" not in captured.err
        assert exit_code == 1 and result.status == "validation_failed"
        assert len(payloads) == 2 and result.output_path is None
        assert manifest["failure_code"] == "stage_response_incomplete"
    else:
        assert "단계 3/3 종합 검토 수집·저장 완료" in captured.err
        assert exit_code == 0 and result.status == "completed"
        assert len(payloads) == 3 and result.output_path is not None
        output = json.loads(result.output_path.read_text(encoding="utf-8"))
        assert [stage["text"] for stage in output["stages"]] == list(texts)
        assert output["deterministic_facts"]["current_null_rate"] == 0.21
    for record, text in zip(result.stages, texts, strict=False):
        assert record.response_path is not None
        assert record.response_path.read_text(encoding="utf-8") == text
