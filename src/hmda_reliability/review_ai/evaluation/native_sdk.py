"""선택적 Langfuse 4.15.6 native API 연결. SDK는 격리 worker에서만 사용한다."""

import json
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict
from datetime import UTC, datetime
from importlib import import_module
from pathlib import Path
from typing import Any

from hmda_reliability.review_ai.contracts import AgenticReviewInput
from hmda_reliability.review_ai.evaluation.annotations import (
    check_annotation_completeness,
    check_pair_decision,
)
from hmda_reliability.review_ai.evaluation.artifacts import verify_local_result
from hmda_reliability.review_ai.evaluation.identity import (
    CRITERIA,
    ReviewTarget,
    case_payload_digest,
    digest,
)
from hmda_reliability.review_ai.staged.evidence import StagedReviewResult


def _json(value: Any) -> Any:
    return value.model_dump(mode="json") if hasattr(value, "model_dump") else value


def _annotation_row(value: Any) -> dict[str, Any]:
    # SDK 4.15.6의 discriminated score 모델은 wire의 camelCase 필드를 유지한다.
    names = {
        "traceId": "trace_id",
        "observationId": "observation_id",
        "authorUserId": "author_user_id",
        "configId": "config_id",
        "dataType": "data_type",
        "stringValue": "string_value",
    }
    allowed = {"id", "name", "source", "value", "comment", "timestamp", "metadata"}
    return {
        names.get(key, key): field
        for key, field in _json(value).items()
        if key in names or key in allowed
    }


def _pages(call: Callable[..., Any], **kwargs: Any) -> list[Any]:
    rows = []
    for page in range(1, 101):
        response = call(page=page, limit=100, **kwargs)
        data = response.data
        rows.extend(data)
        if len(data) < 100:
            return rows
    raise ValueError("pagination_limit")


def _missing(error: Exception) -> bool:
    return getattr(error, "status_code", None) == 404


def make_client(settings: Mapping[str, Any]) -> Any:
    from opentelemetry.sdk.trace import TracerProvider

    Langfuse = import_module("langfuse").Langfuse
    return Langfuse(
        public_key=settings["public_key"],
        secret_key=settings["secret_key"],
        base_url=settings["base_url"],
        timeout=int(settings["io_timeout_seconds"]),
        debug=False,
        tracing_enabled=True,
        tracer_provider=TracerProvider(),
        media_upload_thread_count=0,
    )


def bootstrap(
    client: Any, dataset_name: str, options: Mapping[str, Any]
) -> tuple[dict[str, str], str]:
    configs = _pages(client.api.score_configs.get, request_options=options)
    ids = {}
    for name in (*CRITERIA, "review_decision"):
        labels = (
            ("accept", "reject", "no_change")
            if name == "review_decision"
            else ("0", "1", "2")
        )
        expected = [
            dict(label=label, value=index) for index, label in enumerate(labels)
        ]
        matches = [c for c in configs if c.name == name]
        if len(matches) > 1:
            raise ValueError("score_config_duplicate")
        if matches:
            config = matches[0]
            if (
                config.is_archived
                or config.data_type != "CATEGORICAL"
                or [_json(c) for c in config.categories or []] != expected
            ):
                raise ValueError("score_config_mismatch")
        else:
            config = client.api.score_configs.create(
                name=name,
                data_type="CATEGORICAL",
                categories=expected,
                description="HMDA rubric_v1: 사람이 점수와 사유를 입력합니다.",
                request_options=options,
            )
        ids[name] = config.id
    queue_name = dataset_name + "-rubric-v1"
    queues = [
        q
        for q in _pages(
            client.api.annotation_queues.list_queues, request_options=options
        )
        if q.name == queue_name
    ]
    config_ids = [ids[n] for n in CRITERIA]
    if len(queues) > 1:
        raise ValueError("annotation_queue_duplicate")
    if queues:
        queue = queues[0]
        if set(queue.score_config_ids) != set(config_ids):
            raise ValueError("annotation_queue_mismatch")
    else:
        queue = client.api.annotation_queues.create_queue(
            name=queue_name,
            score_config_ids=config_ids,
            description="한국어 세 단계 검토의 사람 평가",
            request_options=options,
        )
    return ids, queue.id


def run_native_experiment(
    *,
    settings: Mapping[str, Any],
    cases: Sequence[Mapping[str, Any]],
    run_name: str,
    project_revision: str,
    artifact_root: Path,
    review_case: Callable[[Mapping[str, Any]], StagedReviewResult],
    client: Any = None,
    baseline: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    active = client if client is not None else make_client(settings)
    dataset_name = settings["dataset_name"]
    options = {"timeout_in_seconds": settings["io_timeout_seconds"], "max_retries": 0}
    try:
        active.get_dataset_run(dataset_name, run_name)
    except Exception as error:
        if not _missing(error):
            raise ValueError("run_preflight_failed") from None
    else:
        raise ValueError("run_identity_exists")
    config_ids, queue_id = bootstrap(active, dataset_name, options)
    try:
        dataset = active.get_dataset(dataset_name)
    except Exception as error:
        if not _missing(error):
            raise ValueError("dataset_preflight_failed") from None
        active.create_dataset(
            name=dataset_name,
            metadata={"owner": "hmda-review-ai", "schema": "staged-v1"},
        )
        dataset = active.get_dataset(dataset_name)
    items = {item.id: item for item in dataset.items}
    data = []
    known = {}
    for case in cases:
        source = AgenticReviewInput.model_validate(
            dict(case["review_input"], project_revision=project_revision)
        )
        payload = source.model_dump(
            mode="json", include={"incident", "evidence", "draft"}
        )
        case_digest = case_payload_digest(source)
        metadata = dict(
            case_id=case["case_id"],
            case_version=case["case_version"],
            case_digest=case_digest,
            rubric_id="rubric_v1",
        )
        item_id = "hmda-" + digest(metadata).split(":")[1][:40]
        if item_id in known:
            raise ValueError("case_identity_duplicate")
        item = items.get(item_id)
        expected = case.get("oracle")
        if item is None:
            item = active.create_dataset_item(
                dataset_name=dataset_name,
                id=item_id,
                input=payload,
                expected_output=expected,
                metadata=metadata,
            )
        elif (
            item.input != payload
            or item.expected_output != expected
            or item.metadata != metadata
        ):
            raise ValueError("dataset_item_mismatch")
        known[item_id] = (case, source, case_digest)
        data.append(item)
    version = datetime.now(UTC)
    snapshot = active.get_dataset(dataset_name, version=version)
    if {item.id for item in snapshot.items} != set(known):
        raise ValueError("dataset_snapshot_mismatch")
    original = {item.id: item for item in data}
    for item in snapshot.items:
        expected = original[item.id]
        if (
            item.input != expected.input
            or item.expected_output != expected.expected_output
            or item.metadata != expected.metadata
            or getattr(item, "status", "ACTIVE") != "ACTIVE"
        ):
            raise ValueError("dataset_snapshot_mismatch")
    bindings = []
    failures = []

    def task(*, item: Any, **kwargs: Any) -> dict[str, Any]:
        # SDK는 task 예외를 자동 기록하므로 원래 예외를 이 경계 밖으로 넘기지 않는다.
        try:
            case, source, case_digest = known[item.id]
            trace_id = active.get_current_trace_id()
            observation_id = active.get_current_observation_id()
            if not trace_id or not observation_id:
                raise ValueError("trace_identity_missing")
            result = review_case(case)
            packet = verify_local_result(result, source, artifact_root)
            assert result.workflow_id is not None
            native_run = active.get_dataset_run(dataset_name, run_name)
            binding = ReviewTarget(
                case["case_id"],
                case["case_version"],
                case_digest,
                result.workflow_id,
                project_revision,
                packet["canonical_input_digest"],
                packet["output_digest"] or "",
                trace_id,
                observation_id,
                native_run.id,
            )
            metadata = dict(
                asdict(binding), status=result.status, rubric_id="rubric_v1"
            )
            if baseline is not None:
                from hmda_reliability.review_ai.evaluation.identity import (
                    check_comparable_targets,
                )

                matches = [
                    b for b in baseline["bindings"] if b["case_id"] == binding.case_id
                ]
                if len(matches) != 1:
                    raise ValueError("baseline_case_missing")
                base = ReviewTarget(**matches[0])
                _verify_target(base, artifact_root)
                if check_comparable_targets(base, binding):
                    raise ValueError("baseline_mismatch")
                metadata["comparison"] = dict(
                    baseline_run_id=base.run_id,
                    candidate_run_id=binding.run_id,
                    baseline_output_digest=base.output_digest,
                    candidate_output_digest=binding.output_digest,
                )
            active.update_current_span(metadata=metadata)
            previous = []
            for stage in packet["stages"]:
                with active.start_as_current_observation(
                    name=stage["stage_id"],
                    as_type="generation",
                    input={
                        "canonical_input": packet["canonical_input"],
                        "previous_answers": list(previous),
                    },
                    output=stage["text"],
                    level="DEFAULT" if stage["status"] == "completed" else "ERROR",
                    metadata={k: v for k, v in stage.items() if k != "text"},
                ):
                    pass
                if stage["text"] is not None:
                    previous.append(
                        {"stage_id": stage["stage_id"], "text": stage["text"]}
                    )
            bindings.append(asdict(binding))
            return {
                "status": result.status,
                "output": packet["output"],
                "stages": packet["stages"],
            }
        except Exception:
            failures.append("case_export_failed")
            return {"status": "unavailable", "failure_code": "case_export_failed"}

    result = snapshot.run_experiment(
        name="HMDA 한국어 단계 검토",
        run_name=run_name,
        task=task,
        max_concurrency=1,
        evaluators=[],
        metadata={
            "project_revision": project_revision,
            "rubric_id": "rubric_v1",
            "execution_mode": "live-staged",
            "dataset_version": version.isoformat(),
        },
    )
    if len(result.item_results) != len(cases) or len(bindings) != len(cases):
        failures.append("experiment_incomplete")
    # Task 관측은 task가 반환된 뒤 닫힌다. Native flush 이후에만 연결한다.
    for binding in bindings:
        try:
            active.api.annotation_queues.create_queue_item(
                queue_id,
                object_id=binding["observation_id"],
                object_type="OBSERVATION",
                request_options=options,
            )
        except Exception:
            failures.append("queue_attachment_failed")
    return dict(
        status="unavailable" if failures else "submitted_unverified",
        failure_code=failures[0] if failures else None,
        run_id=result.dataset_run_id,
        run_name=run_name,
        dataset_name=dataset_name,
        queue_id=queue_id,
        config_ids=config_ids,
        bindings=bindings,
    )


def _verify_target(target: ReviewTarget, root: Path) -> None:
    from hmda_reliability.review_ai.evaluation.artifacts import _read
    from hmda_reliability.review_ai.staged.evidence import StagedReviewManifest
    from hmda_reliability.review_ai.staged.store import StagedReviewStore

    cases = json.loads(Path(__file__).with_name("cases.json").read_text())
    matches = [
        c
        for c in cases
        if c["case_id"] == target.case_id and c["case_version"] == target.case_version
    ]
    if len(matches) != 1:
        raise ValueError("case_binding_mismatch")
    source = AgenticReviewInput.model_validate(
        dict(matches[0]["review_input"], project_revision=target.project_revision)
    )
    path = StagedReviewStore(root).directory(target.workflow_id) / "workflow.json"
    manifest = StagedReviewManifest.model_validate_json(_read(path, path, 2_097_152))
    result = StagedReviewResult(
        status=manifest.status,
        workflow_id=manifest.workflow_id,
        workflow_path=StagedReviewStore(root).directory(target.workflow_id)
        / "workflow.json",
        stages=manifest.stages,
        output_path=manifest.output_path,
        failure_code=manifest.failure_code,
    )
    packet = verify_local_result(result, source, root)
    if (
        packet["status"] != "completed"
        or case_payload_digest(source) != target.case_digest
        or packet["output_digest"] != target.output_digest
        or packet["canonical_input_digest"] != target.canonical_input_digest
    ):
        raise ValueError("target_binding_mismatch")


def _observation_metadata(client: Any, target: ReviewTarget) -> Mapping[str, Any]:
    cursor = None
    seen = set()
    for _ in range(100):
        response = client.api.observations.get_many(
            trace_id=target.trace_id,
            limit=100,
            cursor=cursor,
            fields="core,metadata",
            expand_metadata="comparison",
        )
        for observation in response.data:
            if observation.id == target.observation_id:
                metadata = observation.metadata
                if isinstance(metadata, str):
                    metadata = json.loads(metadata)
                if (
                    not isinstance(metadata, Mapping)
                    or metadata.get("rubric_id") != "rubric_v1"
                    or metadata.get("status") != "completed"
                    or any(metadata.get(k) != v for k, v in asdict(target).items())
                ):
                    raise ValueError("remote_target_mismatch")
                return metadata
        cursor = response.meta.cursor
        if not cursor or cursor in seen:
            break
        seen.add(cursor)
    raise ValueError("remote_observation_missing")


def read_annotations(
    client: Any,
    receipt: Mapping[str, Any],
    reviewer_id: str,
    *,
    artifact_root: Path,
    baseline: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    if not receipt.get("bindings"):
        raise ValueError("review_targets_missing")
    if baseline is not None and baseline.get("config_ids") != receipt.get("config_ids"):
        raise ValueError("baseline_config_mismatch")
    result = []
    configs = receipt["config_ids"]
    for name in (*CRITERIA, "review_decision"):
        config = client.api.score_configs.get_by_id(configs[name])
        labels = (
            ("accept", "reject", "no_change")
            if name == "review_decision"
            else ("0", "1", "2")
        )
        if (
            config.name != name
            or config.is_archived
            or config.data_type != "CATEGORICAL"
            or [(c.label, c.value) for c in config.categories or []]
            != [(label, index) for index, label in enumerate(labels)]
        ):
            raise ValueError("score_config_mismatch")
    for item in receipt["bindings"]:
        target = ReviewTarget(**item)
        _verify_target(target, artifact_root)
        metadata = _observation_metadata(client, target)
        scores = [
            _annotation_row(s)
            for s in _pages(
                client.api.scores.get_many,
                trace_id=target.trace_id,
                observation_id=target.observation_id,
                source="ANNOTATION",
            )
        ]
        errors = check_annotation_completeness(
            target, reviewer_id=reviewer_id, config_ids=configs, scores=scores
        )
        if baseline is not None:
            matches = [
                b for b in baseline["bindings"] if b["case_id"] == target.case_id
            ]
            if len(matches) != 1:
                raise ValueError("baseline_case_missing")
            base = ReviewTarget(**matches[0])
            _verify_target(base, artifact_root)
            _observation_metadata(client, base)
            decisions = [
                s
                for s in scores
                if s.get("name") == "review_decision"
                and s.get("author_user_id") == reviewer_id
            ]
            if len(decisions) != 1:
                errors = (*errors, "decision_missing_or_duplicate")
            else:
                score = dict(
                    decisions[0], metadata={"comparison": metadata.get("comparison")}
                )
                errors = (
                    *errors,
                    *check_pair_decision(
                        base,
                        target,
                        reviewer_id=reviewer_id,
                        config_id=configs["review_decision"],
                        score=score,
                    ),
                )
        result.append(
            dict(
                case_id=target.case_id,
                workflow_id=target.workflow_id,
                status="incomplete" if errors else "complete",
                violations=errors,
            )
        )
    return result
