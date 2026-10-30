"""실제 로컬 원문과 조회한 원격 관측에 연결된 사람 annotation만 확인한다."""

import json
from pathlib import Path
from types import SimpleNamespace as NS

import pytest

from hmda_reliability.review_ai.contracts import AgenticReviewInput
from hmda_reliability.review_ai.evaluation import native_sdk
from hmda_reliability.review_ai.staged.service import review_null_spike_staged
from hmda_reliability.runtime_ai.settings import RuntimeAISettings
from tests.review_ai.evaluation.test_native_integrity import scores
from tests.review_ai.evaluation.test_native_sdk import FakeClient
from tests.review_ai.test_staged_service import TextProvider, response

pytestmark = pytest.mark.component


@pytest.fixture
def native_review(tmp_path):
    case = json.loads(Path(native_sdk.__file__).with_name("cases.json").read_text())[0]
    source = AgenticReviewInput.model_validate(
        dict(case["review_input"], project_revision="actual-revision")
    )
    client = FakeClient()

    def review(_case):
        return review_null_spike_staged(
            incident=source.incident,
            evidence=source.evidence,
            draft=source.draft,
            project_revision=source.project_revision,
            settings=RuntimeAISettings(
                base_url="http://unused.invalid", api_key="unused", model="test"
            ),
            provider=TextProvider([response("보존된 한국어 답변")] * 3),
            artifact_root=tmp_path,
            workflow_id_factory=lambda: "sr-annotations",
        )

    receipt = native_sdk.run_native_experiment(
        settings=dict(dataset_name="test", io_timeout_seconds=1),
        cases=[case],
        run_name="annotations",
        project_revision=source.project_revision,
        artifact_root=tmp_path,
        review_case=review,
        client=client,
    )
    assert receipt["status"] == "submitted_unverified"
    by_id = {c.id: c for c in client.configs}
    for config in client.configs:
        config.categories = [NS(**c) for c in config.categories]
    client.api.score_configs.get_by_id = by_id.__getitem__
    records = [
        dict(
            s, config_id=receipt["config_ids"][s["name"]], observation_id="observation"
        )
        for s in scores()
    ]
    wire_names = {
        "trace_id": "traceId",
        "observation_id": "observationId",
        "author_user_id": "authorUserId",
        "config_id": "configId",
        "data_type": "dataType",
        "string_value": "stringValue",
    }
    records = [
        {wire_names.get(key, key): value for key, value in row.items()}
        for row in records
    ]
    queries = []

    def query(**kwargs):
        queries.append(kwargs)
        # 앞 페이지의 다른 검토자 점수로 완비를 만들 수 없다.
        return NS(
            data=[dict(records[0], authorUserId="another")] * 100
            if kwargs["page"] == 1
            else records
        )

    client.api.scores = NS(get_many=query)
    client.api.observations = NS(
        get_many=lambda **kw: NS(
            data=[NS(id="observation", metadata=client.metadata)], meta=NS(cursor=None)
        )
    )
    return client, receipt, queries


def test_read_checks_manifest_remote_binding_and_paginated_human_annotations(
    native_review, tmp_path
):
    client, receipt, queries = native_review
    result = native_sdk.read_annotations(
        client, receipt, "human", artifact_root=tmp_path
    )
    assert result[0]["status"] == "complete"
    assert [q["page"] for q in queries] == [1, 2]
    assert all(
        q["trace_id"] == "trace"
        and q["observation_id"] == "observation"
        and q["source"] == "ANNOTATION"
        for q in queries
    )


@pytest.mark.parametrize(
    "field,value",
    [("output_digest", "substituted"), ("rubric_id", "other"), ("status", "failed")],
)
def test_remote_output_substitution_is_rejected(native_review, tmp_path, field, value):
    client, receipt, queries = native_review
    client.metadata[field] = value
    with pytest.raises(ValueError, match="remote_target_mismatch"):
        native_sdk.read_annotations(client, receipt, "human", artifact_root=tmp_path)
    assert not queries


def test_local_raw_substitution_is_rejected_before_query(native_review, tmp_path):
    client, receipt, queries = native_review
    next((tmp_path / "agentic-review" / "responses").glob("*.txt")).write_text(
        "바꾼 답변"
    )
    with pytest.raises(ValueError, match="response_digest_mismatch"):
        native_sdk.read_annotations(client, receipt, "human", artifact_root=tmp_path)
    assert not queries


def test_different_rubric_config_cannot_be_used_as_a_baseline(native_review, tmp_path):
    client, receipt, _ = native_review
    with pytest.raises(ValueError, match="baseline_config_mismatch"):
        native_sdk.read_annotations(
            client,
            receipt,
            "human",
            artifact_root=tmp_path,
            baseline=dict(receipt, config_ids={}),
        )


def test_pinned_sdk_annotation_wire_maps_to_completeness(native_review, tmp_path):
    pytest.importorskip("langfuse")
    import httpx
    from langfuse.api import LangfuseAPI

    client, receipt, _ = native_review
    rows = [
        dict(
            id=s["name"],
            name=s["name"],
            traceId="trace",
            observationId="observation",
            configId=receipt["config_ids"][s["name"]],
            dataType="CATEGORICAL",
            source="ANNOTATION",
            authorUserId="human",
            value=1,
            stringValue="1",
            comment="실제 사람이 남긴 사유",
            timestamp="2026-10-30T00:00:00Z",
            createdAt="2026-10-30T00:00:00Z",
            updatedAt="2026-10-30T00:00:00Z",
            metadata={},
            environment="default",
        )
        for s in scores()
    ]
    with httpx.Client(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                200,
                json=dict(
                    data=rows, meta=dict(page=1, limit=100, totalItems=5, totalPages=1)
                ),
            )
        )
    ) as transport:
        api = LangfuseAPI(base_url="https://unused.invalid", httpx_client=transport)
        client.api.scores = api.scores
        result = native_sdk.read_annotations(
            client, receipt, "human", artifact_root=tmp_path
        )
    assert result[0]["status"] == "complete"
