"""SDK를 생략하지 않고 native compile과 experiment task 계약을 실행한다."""

import json

import pytest
from langfuse import Langfuse
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from tests.review_ai.conftest import NATIVE_QUESTIONS, native_prompt
from tests.review_ai.test_staged_service import TEXTS, TextProvider, response

pytestmark = pytest.mark.component


def test_native_chat_prompt_compiles_message_placeholder_in_order():
    prompt = native_prompt("draft_critique")
    history = [
        {"role": "user", "content": "가상 사례"},
        {"role": "system", "content": NATIVE_QUESTIONS["evidence_review"]},
        {"role": "assistant", "content": "첫 단계의 한국어 원문"},
    ]

    compiled = prompt.compile(history=history)

    assert compiled[1:4] == history
    assert compiled[-1] == {
        "role": "system",
        "content": NATIVE_QUESTIONS["draft_critique"],
    }
    assert prompt.name == "hmda-review-ai/draft_critique" and prompt.version == 7


def test_pinned_sdk_really_runs_a_task_without_remote_io():
    exporter = InMemorySpanExporter()
    client = Langfuse(
        public_key="pk-test-native-contract",
        secret_key="unused",
        base_url="http://unused.invalid",
        tracer_provider=TracerProvider(),
        span_exporter=exporter,
        media_upload_thread_count=0,
    )
    calls = []

    def task(*, item, **_kwargs):
        calls.append(item["input"])
        return {"result": "보존된 답변"}

    try:
        result = client.run_experiment(
            name="sdk-contract",
            data=[{"input": {"case": "synthetic"}}],
            task=task,
            max_concurrency=1,
            evaluators=[],
        )
        assert calls == [{"case": "synthetic"}]
        assert len(result.item_results) == 1 and exporter.get_finished_spans()
    finally:
        client.shutdown()


def test_real_generation_sdk_records_call_messages_usage_and_prompt_version(
    native_langfuse, null_spike_review_material, tmp_path
):
    from hmda_reliability.review_ai.staged.service import review_null_spike_staged
    from hmda_reliability.runtime_ai import RuntimeAISettings
    from hmda_reliability.runtime_ai.contracts import ProviderUsage

    exporter = InMemorySpanExporter()
    client = Langfuse(
        public_key="pk-test-generation-contract",
        secret_key="unused",
        base_url="http://unused.invalid",
        tracer_provider=TracerProvider(),
        span_exporter=exporter,
        media_upload_thread_count=0,
    )
    material = null_spike_review_material
    usage = ProviderUsage(prompt_tokens=10, completion_tokens=4, total_tokens=14)
    provider = TextProvider(
        [response(text).model_copy(update={"usage": usage}) for text in TEXTS]
    )

    try:
        result = review_null_spike_staged(
            incident=material.detection.incident,
            evidence=[material.detection.evidence],
            draft=material.draft,
            project_revision="native-generation-test",
            settings=RuntimeAISettings(
                base_url="http://unused.invalid/v1", api_key="unused", model="fake"
            ),
            provider=provider,
            prompts=native_langfuse.prompts,
            langfuse_client=client,
            artifact_root=tmp_path,
        )
        assert result.status == "completed"
        client.flush()
        spans = exporter.get_finished_spans()
        assert len(spans) == 3
        for index, span in enumerate(spans):
            attrs = span.attributes
            assert attrs is not None
            assert attrs["langfuse.observation.type"] == "generation"
            assert attrs["langfuse.observation.prompt.name"] == (
                f"hmda-review-ai/{result.stages[index].stage_id}"
            )
            assert attrs["langfuse.observation.prompt.version"] == 7
            serialized_input = attrs["langfuse.observation.input"]
            serialized_usage = attrs["langfuse.observation.usage_details"]
            assert isinstance(serialized_input, str)
            assert isinstance(serialized_usage, str)
            assert json.loads(serialized_input) == [
                message.model_dump(mode="json") for message in provider.calls[index]
            ]
            assert attrs["langfuse.observation.output"] == TEXTS[index]
            assert json.loads(serialized_usage) == {
                "input": 10,
                "output": 4,
                "total": 14,
            }
    finally:
        client.shutdown()
