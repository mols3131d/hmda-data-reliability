import json
from contextlib import nullcontext
from types import SimpleNamespace as NS

import pytest

from hmda_reliability.review_ai.evaluation.native_sdk import run_native_experiment
from tests.review_ai.test_staged_service import TextProvider, response, run_review

pytestmark = pytest.mark.component


class Missing(Exception):
    status_code = 404


class FakeClient:
    def __init__(self):
        self.configs = []
        self.queues = []
        self.items = []
        self.dataset = False
        self.running = False
        self.observations = []
        self.metadata = {}
        self.api = NS(
            score_configs=NS(
                get=lambda **kw: NS(data=self.configs), create=self.config
            ),
            annotation_queues=NS(
                list_queues=lambda **kw: NS(data=self.queues),
                create_queue=self.queue,
                create_queue_item=lambda *a, **kw: None,
            ),
        )

    def config(self, **kw):
        item = NS(
            id="config-" + kw["name"],
            is_archived=False,
            **{k: v for k, v in kw.items() if k != "request_options"},
        )
        self.configs.append(item)
        return item

    def queue(self, **kw):
        item = NS(id="queue", **{k: v for k, v in kw.items() if k != "request_options"})
        self.queues.append(item)
        return item

    def get_dataset_run(self, *a):
        if not self.running:
            raise Missing()
        return NS(id="native-run")

    def get_dataset(self, name, **kwargs):
        if not self.dataset:
            raise Missing()
        return NS(
            items=self.items,
            run_experiment=lambda **kw: self.run_experiment(
                data=list(self.items), **kw
            ),
        )

    def create_dataset(self, **kw):
        self.dataset = True

    def create_dataset_item(self, **kw):
        item = NS(
            id=kw["id"],
            input=kw["input"],
            expected_output=kw["expected_output"],
            metadata=kw["metadata"],
        )
        self.items.append(item)
        return item

    def get_current_trace_id(self):
        return "trace"

    def get_current_observation_id(self):
        return "observation"

    def update_current_span(self, **kw):
        self.metadata = kw["metadata"]

    def start_as_current_observation(self, **kw):
        self.observations.append(kw)
        return nullcontext()

    def run_experiment(self, **kw):
        assert kw["max_concurrency"] == 1 and kw["evaluators"] == []
        self.running = True
        values = [kw["task"](item=item) for item in kw["data"]]
        self.running = False
        return NS(item_results=values, dataset_run_id="native-run")


def case(material):
    from hmda_reliability.review_ai.contracts import AgenticReviewInput

    source = AgenticReviewInput(
        incident=material.detection.incident,
        evidence=[material.detection.evidence],
        draft=material.draft,
        project_revision="revision-under-test",
    )
    return dict(
        case_id="case",
        case_version="1",
        review_input=source.model_dump(mode="json", exclude={"project_revision"}),
        oracle={"numeric": "reviewer-only-secret"},
    )


def execute(material, tmp_path, client, tamper=False):
    provider = TextProvider([response("한국어 원문")] * 3)

    def review(item):
        result = run_review(material, tmp_path, provider)
        if tamper:
            result.stages[0].response_path.write_text("다른 본문")
        return result

    settings = dict(
        base_url="http://unused.invalid",
        public_key="public",
        secret_key="PRIVATE_KEY",
        io_timeout_seconds=1,
        dataset_name="test-dataset",
    )
    receipt = run_native_experiment(
        settings=settings,
        cases=[case(material)],
        run_name="test-run",
        project_revision="revision-under-test",
        artifact_root=tmp_path,
        review_case=review,
        client=client,
    )
    return receipt, provider


def test_native_task_preserves_real_review_and_reuses_bootstrap(
    null_spike_review_material, tmp_path
):
    client = FakeClient()
    queued = []

    def enqueue(*args, **kwargs):
        assert not client.running, "관측 task가 끝난 뒤 대기열에 연결해야 한다"
        queued.append(kwargs["object_id"])

    client.api.annotation_queues.create_queue_item = enqueue
    receipt, provider = execute(null_spike_review_material, tmp_path, client)
    assert receipt["status"] == "submitted_unverified"
    assert queued == ["observation"]
    assert len(provider.calls) == 3
    assert len(client.observations) == 3
    assert (
        client.observations[1]["input"]["previous_answers"][0]["text"] == "한국어 원문"
    )
    assert all(
        "reviewer-only-secret" not in m.content
        for messages in provider.calls
        for m in messages
    )
    assert "PRIVATE_KEY" not in json.dumps(client.metadata)
    assert str(tmp_path) not in json.dumps(receipt)
    before = (len(client.configs), len(client.queues), len(client.items))
    execute(null_spike_review_material, tmp_path / "second", client)
    assert before == (len(client.configs), len(client.queues), len(client.items))


def test_tampered_raw_is_not_exported_and_model_is_not_retried(
    null_spike_review_material, tmp_path
):
    client = FakeClient()
    receipt, provider = execute(
        null_spike_review_material, tmp_path, client, tamper=True
    )
    assert receipt["status"] == "unavailable" and not receipt["bindings"]
    assert len(provider.calls) == 3 and not client.observations


def test_conflicting_score_config_is_rejected_before_model(
    null_spike_review_material, tmp_path
):
    client = FakeClient()
    client.configs = [
        NS(name="added_value", is_archived=False, data_type="NUMERIC", categories=[])
    ]
    with pytest.raises(ValueError, match="score_config_mismatch"):
        execute(null_spike_review_material, tmp_path, client)


def test_existing_run_is_not_overwritten(null_spike_review_material, tmp_path):
    client = FakeClient()
    client.running = True
    with pytest.raises(ValueError, match="run_identity_exists"):
        execute(null_spike_review_material, tmp_path, client)
    assert not client.items and not client.configs


def test_conflicting_queue_is_not_silently_reconfigured(
    null_spike_review_material, tmp_path
):
    client = FakeClient()
    client.queues = [NS(name="test-dataset-rubric-v1", score_config_ids=["other"])]
    with pytest.raises(ValueError, match="annotation_queue_mismatch"):
        execute(null_spike_review_material, tmp_path, client)
    assert not client.items and not client.observations


def test_pinned_sdk_really_runs_a_task_without_remote_io():
    sdk = pytest.importorskip("langfuse")
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
        InMemorySpanExporter,
    )

    exporter = InMemorySpanExporter()
    client = sdk.Langfuse(
        public_key="pk-test-native-contract",
        secret_key="unused",
        base_url="http://unused.invalid",
        tracer_provider=TracerProvider(),
        span_exporter=exporter,
        media_upload_thread_count=0,
    )
    calls = []

    def task(*, item):
        calls.append(item["input"])
        return {"result": "보존된 답변"}

    result = client.run_experiment(
        name="sdk-contract",
        data=[{"input": {"case": "synthetic"}}],
        task=task,
        max_concurrency=1,
        evaluators=[],
    )
    assert calls == [{"case": "synthetic"}]
    assert len(result.item_results) == 1 and exporter.get_finished_spans()
    client.shutdown()


def test_pinned_sdk_score_config_wire_accepts_the_native_categories():
    pytest.importorskip("langfuse")
    from typing import Any

    import httpx
    from langfuse.api import LangfuseAPI

    categories = [{"label": str(v), "value": v} for v in range(3)]
    requests = []

    def respond(request):
        body = json.loads(request.content)
        requests.append(body)
        return httpx.Response(
            200,
            json=dict(
                body,
                id="config",
                projectId="project",
                createdAt="2026-10-30T00:00:00Z",
                updatedAt="2026-10-30T00:00:00Z",
                isArchived=False,
            ),
        )

    with httpx.Client(transport=httpx.MockTransport(respond)) as transport:
        api: Any = LangfuseAPI(
            base_url="https://unused.invalid", httpx_client=transport
        )
        config = api.score_configs.create(
            name="added_value", data_type="CATEGORICAL", categories=categories
        )
    assert requests[0]["categories"] == categories
    assert [(c.label, c.value) for c in config.categories] == [
        ("0", 0),
        ("1", 1),
        ("2", 2),
    ]
