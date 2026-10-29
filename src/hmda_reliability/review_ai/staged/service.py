"""고정 대화 단계의 텍스트를 수집하고 결과 JSON을 코드로 만든다."""

from __future__ import annotations

import hashlib
import time
import uuid
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, Protocol

from pydantic import ValidationError

from hmda_reliability.reliability import Evidence, Incident, RemediationDraft
from hmda_reliability.review_ai.context import (
    ReviewContextTooLargeError,
    build_bounded_review_context,
)
from hmda_reliability.review_ai.contracts import AgenticReviewInput
from hmda_reliability.review_ai.evidence import SanitizedAgenticReviewConfiguration
from hmda_reliability.review_ai.prompt import (
    PromptTooLargeError,
    build_canonical_input,
    canonical_json_bytes,
)
from hmda_reliability.review_ai.settings import ReviewAISettings
from hmda_reliability.review_ai.staged.contracts import (
    STAGE_IDS,
    StageAnswer,
    StagedReviewOutput,
    StageId,
    assemble_staged_output,
)
from hmda_reliability.review_ai.staged.evidence import (
    StagedReviewManifest,
    StagedReviewResult,
    StagedReviewStatus,
    StageRecord,
)
from hmda_reliability.review_ai.staged.prompt import render_stage_prompt
from hmda_reliability.review_ai.staged.settings import StagedExecutionSettings
from hmda_reliability.review_ai.staged.store import StagedReviewStore
from hmda_reliability.review_ai.store import (
    InvocationEvidenceStoreError,
    InvocationResponseStore,
)
from hmda_reliability.runtime_ai.contracts import ChatMessage, ProviderResponse
from hmda_reliability.runtime_ai.provider import (
    OpenAICompatibleAdapter,
    ProviderResponseTooLargeError,
    ProviderUnavailableError,
)
from hmda_reliability.runtime_ai.settings import RuntimeAISettings


class StagedReviewProvider(Protocol):
    def invoke(
        self,
        messages: tuple[ChatMessage, ...],
        *,
        output_format: Literal["json_object", "text"] = "json_object",
        budget_seconds: float | None = None,
    ) -> ProviderResponse: ...


@dataclass(frozen=True)
class _ExecutionBudget:
    settings: StagedExecutionSettings
    clock: Callable[[], float]
    started: float

    @property
    def deadline(self) -> float:
        return self.started + self.settings.workflow_budget_seconds

    @property
    def elapsed_ms(self) -> float:
        return max(0.0, (self.clock() - self.started) * 1000)

    def failure(self, stage_deadline: float | None = None) -> str | None:
        now = self.clock()
        if now >= self.deadline:
            return "workflow_budget_exhausted"
        if stage_deadline is not None and now >= stage_deadline:
            return "stage_budget_exhausted"
        return None


def review_null_spike_staged(
    *,
    incident: Incident,
    evidence: Sequence[Evidence],
    draft: RemediationDraft,
    project_revision: str,
    settings: RuntimeAISettings,
    review_settings: ReviewAISettings | None = None,
    execution_settings: StagedExecutionSettings | None = None,
    provider: StagedReviewProvider | None = None,
    artifact_root: Path = Path(".local/artifacts"),
    workflow_id_factory: Callable[[], str] | None = None,
    clock: Callable[[], float] = time.monotonic,
) -> StagedReviewResult:
    """같은 immutable 사례의 세 답변을 원문 그대로 수집한다.

    completed는 수집·저장 완료다. 자연어의 사실성이나 사람의 승인 여부를
    판정하지 않는다. 각 Runtime 호출의 retry 외에 단계 재생성은 하지 않는다.
    """
    budget = _ExecutionBudget(
        execution_settings or StagedExecutionSettings(), clock, clock()
    )
    limits = review_settings or ReviewAISettings()
    try:
        review_input = AgenticReviewInput(
            incident=incident,
            evidence=tuple(evidence),
            draft=draft,
            project_revision=project_revision,
        )
        context = build_bounded_review_context(review_input)
        canonical_input = build_canonical_input(review_input, context=context)
        render_stage_prompt(
            canonical_input, STAGE_IDS[0], (), max_prompt_bytes=limits.max_prompt_bytes
        )
    except ValidationError:
        return StagedReviewResult(
            status="input_rejected", failure_code="invalid_review_input"
        )
    except PromptTooLargeError:
        return StagedReviewResult(
            status="input_rejected", failure_code="prompt_too_large"
        )
    except ReviewContextTooLargeError:
        return StagedReviewResult(
            status="input_rejected", failure_code="context_too_large"
        )

    workflow_id = (workflow_id_factory or _new_workflow_id)()
    store = StagedReviewStore(artifact_root)
    try:
        store.reserve(workflow_id)
    except (InvocationEvidenceStoreError, ValueError):
        return StagedReviewResult(
            status="provenance_failed",
            workflow_id=workflow_id,
            failure_code="workflow_reservation_failed",
        )
    configuration = SanitizedAgenticReviewConfiguration.model_validate(
        {**settings.sanitized_configuration(), **limits.sanitized_configuration()}
    )
    active_provider = provider or OpenAICompatibleAdapter(settings, clock=clock)
    records: list[StageRecord] = []
    answers: list[StageAnswer] = []
    for stage_id in STAGE_IDS:
        stage_started = clock()
        stage_deadline = min(
            stage_started + budget.settings.stage_budget_seconds, budget.deadline
        )
        record, answer = _run_stage(
            canonical_input,
            stage_id,
            tuple(answers),
            provider=active_provider,
            workflow_id=workflow_id,
            artifact_root=artifact_root,
            limits=limits,
            settings=settings,
            budget=budget,
            stage_deadline=stage_deadline,
        )
        record = record.model_copy(
            update={
                "budget_seconds": max(0.0, stage_deadline - stage_started),
                "elapsed_ms": max(0.0, (clock() - stage_started) * 1000),
            }
        )
        try:
            saved_record = record.model_copy(
                update={"record_path": store.stage_path(workflow_id, stage_id)}
            )
            store.write_stage(workflow_id, saved_record)
            record = saved_record
        except InvocationEvidenceStoreError:
            record = record.model_copy(
                update={
                    "status": "provenance_failed",
                    "failure_code": "stage_record_write_failed",
                }
            )
        records.append(record)
        if record.status != "completed" or answer is None:
            return _finish(
                store,
                workflow_id,
                project_revision,
                configuration,
                canonical_input,
                tuple(records),
                budget,
                status=record.status,
                failure_code=record.failure_code,
            )
        answers.append(answer)

    if failure := budget.failure():
        return _finish(
            store,
            workflow_id,
            project_revision,
            configuration,
            canonical_input,
            tuple(records),
            budget,
            status="unavailable",
            failure_code=failure,
        )
    output = assemble_staged_output(review_input, tuple(answers))
    try:
        output_path = store.write_output(
            workflow_id,
            output,
            max_bytes=limits.max_prompt_bytes + 18 * settings.max_output_bytes + 65_536,
        )
    except InvocationEvidenceStoreError:
        return _finish(
            store,
            workflow_id,
            project_revision,
            configuration,
            canonical_input,
            tuple(records),
            budget,
            status="provenance_failed",
            failure_code="staged_output_write_failed",
        )
    failure = budget.failure()
    return _finish(
        store,
        workflow_id,
        project_revision,
        configuration,
        canonical_input,
        tuple(records),
        budget,
        status="unavailable" if failure else "completed",
        failure_code=failure,
        output=output,
        output_path=output_path,
    )


def _run_stage(
    canonical_input: dict[str, object],
    stage_id: StageId,
    answers: tuple[StageAnswer, ...],
    *,
    provider: StagedReviewProvider,
    workflow_id: str,
    artifact_root: Path,
    limits: ReviewAISettings,
    settings: RuntimeAISettings,
    budget: _ExecutionBudget,
    stage_deadline: float,
) -> tuple[StageRecord, StageAnswer | None]:
    if failure := budget.failure(stage_deadline):
        return StageRecord(
            stage_id=stage_id, status="unavailable", failure_code=failure
        ), None
    try:
        rendered = render_stage_prompt(
            canonical_input, stage_id, answers, max_prompt_bytes=limits.max_prompt_bytes
        )
    except PromptTooLargeError:
        return StageRecord(
            stage_id=stage_id, status="input_rejected", failure_code="prompt_too_large"
        ), None
    base = StageRecord(
        stage_id=stage_id,
        status="completed",
        prompt_digest=rendered.prompt_digest,
        prompt_bytes=rendered.prompt_bytes,
    )
    if failure := budget.failure(stage_deadline):
        return base.model_copy(
            update={"status": "unavailable", "failure_code": failure}
        ), None
    try:
        response = provider.invoke(
            rendered.messages,
            output_format="text",
            budget_seconds=max(0.0, stage_deadline - budget.clock()),
        )
    except ProviderUnavailableError as error:
        failure = error.failure_code
        if failure == "provider_budget_exhausted":
            failure = (
                "workflow_budget_exhausted"
                if stage_deadline == budget.deadline
                else "stage_budget_exhausted"
            )
        return base.model_copy(
            update={
                "status": "unavailable",
                "failure_code": failure,
                "attempt_count": error.attempt_count,
                "latency_ms": error.latency_ms,
            }
        ), None
    except ProviderResponseTooLargeError as error:
        return base.model_copy(
            update={
                "status": "validation_failed",
                "failure_code": "response_too_large",
                "attempt_count": error.attempt_count,
                "latency_ms": error.latency_ms,
                "usage": error.usage,
                "response_metadata": error.response_metadata,
            }
        ), None
    record = base.model_copy(
        update={
            "attempt_count": response.attempt_count,
            "latency_ms": response.latency_ms,
            "usage": response.usage,
            "response_metadata": response.response_metadata,
        }
    )
    try:
        response_path = InvocationResponseStore(artifact_root).write(
            f"{workflow_id}-{stage_id}",
            response.content,
            max_response_bytes=settings.max_output_bytes,
        )
    except InvocationEvidenceStoreError:
        return record.model_copy(
            update={
                "status": "provenance_failed",
                "failure_code": "stage_response_write_failed",
            }
        ), None
    record = record.model_copy(
        update={
            "response_path": response_path,
            "response_digest": "sha256:"
            + hashlib.sha256(response.content.encode("utf-8")).hexdigest(),
        }
    )
    if failure := budget.failure(stage_deadline):
        return record.model_copy(
            update={"status": "unavailable", "failure_code": failure}
        ), None
    reason = (
        response.response_metadata.finish_reason if response.response_metadata else None
    )
    failure = (
        "stage_response_empty"
        if not response.content.strip()
        else "stage_response_incomplete"
        if reason in {"length", "content_filter", "tool_calls", "function_call"}
        else None
    )
    if failure is not None:
        return record.model_copy(
            update={"status": "validation_failed", "failure_code": failure}
        ), None
    return record, StageAnswer(stage_id=stage_id, text=response.content)


def _finish(
    store: StagedReviewStore,
    workflow_id: str,
    project_revision: str,
    configuration: SanitizedAgenticReviewConfiguration,
    canonical_input: dict[str, object],
    records: tuple[StageRecord, ...],
    budget: _ExecutionBudget,
    *,
    status: StagedReviewStatus,
    failure_code: str | None = None,
    output: StagedReviewOutput | None = None,
    output_path: Path | None = None,
) -> StagedReviewResult:
    manifest = StagedReviewManifest(
        workflow_id=workflow_id,
        project_revision=project_revision,
        configuration=configuration,
        execution_settings=budget.settings,
        elapsed_ms=budget.elapsed_ms,
        canonical_input=canonical_input,
        status=status,
        stages=records,
        physical_attempts=sum(record.attempt_count for record in records),
        max_physical_attempts=3 * (configuration.max_retries + 1),
        failure_code=failure_code,
        output_path=output_path,
        output_digest="sha256:"
        + hashlib.sha256(
            canonical_json_bytes(output.model_dump(mode="json"))
        ).hexdigest()
        if output
        else None,
    )
    try:
        workflow_path = store.write_manifest(manifest)
    except InvocationEvidenceStoreError:
        return StagedReviewResult(
            status="provenance_failed",
            workflow_id=workflow_id,
            stages=records,
            output_path=output_path,
            failure_code="workflow_record_write_failed",
        )
    return StagedReviewResult(
        status=status,
        workflow_id=workflow_id,
        workflow_path=workflow_path,
        output_path=output_path,
        stages=records,
        output=output if status == "completed" else None,
        failure_code=failure_code,
    )


def _new_workflow_id() -> str:
    return f"sr-{datetime.now(UTC):%Y%m%d}-{uuid.uuid4().hex[:12]}"
