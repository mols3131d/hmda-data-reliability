"""Read-only null-spike agentic review orchestration."""

from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol
from uuid import uuid4

from pydantic import ValidationError

from hmda_reliability.reliability.agentic_review.contracts import (
    AgenticReviewInput,
    AgenticReviewOutput,
    AgenticReviewResult,
    AgenticReviewStatus,
    AgenticReviewValidation,
    PromptIdentity,
    ReviewValidationStatus,
)
from hmda_reliability.reliability.agentic_review.evidence import (
    AgenticInvocationEvidence,
    SanitizedAgenticReviewConfiguration,
)
from hmda_reliability.reliability.agentic_review.prompt import (
    PromptTooLargeError,
    RenderedPrompt,
    render_review_prompt,
)
from hmda_reliability.reliability.agentic_review.provider import (
    OpenAICompatibleAdapter,
    ProviderResponse,
    ProviderResponseTooLargeError,
    ProviderUnavailableError,
    ProviderUsage,
)
from hmda_reliability.reliability.agentic_review.settings import (
    AgenticReviewSettings,
)
from hmda_reliability.reliability.agentic_review.store import (
    InvocationEvidenceStore,
    InvocationEvidenceStoreError,
)
from hmda_reliability.reliability.agentic_review.validator import (
    validate_agentic_review,
)
from hmda_reliability.reliability.contracts import Evidence, Incident
from hmda_reliability.reliability.remediation import RemediationDraft


class ReviewProvider(Protocol):
    def invoke(self, rendered: RenderedPrompt) -> ProviderResponse: ...


class InvocationEvidenceWriter(Protocol):
    def write(
        self,
        record: AgenticInvocationEvidence,
        *,
        max_record_bytes: int,
    ) -> Path: ...


def review_null_spike(
    *,
    incident: Incident,
    evidence: Sequence[Evidence],
    draft: RemediationDraft,
    prompt_identity: PromptIdentity,
    project_revision: str,
    settings: AgenticReviewSettings,
    provider: ReviewProvider | None = None,
    evidence_store: InvocationEvidenceWriter | None = None,
    artifact_root: Path = Path(".local/artifacts"),
    invocation_id_factory: Callable[[], str] | None = None,
    clock: Callable[[], datetime] | None = None,
) -> AgenticReviewResult:
    """Generate one evidence-bound advisory result without invoking recovery."""

    try:
        review_input = AgenticReviewInput(
            incident=incident,
            evidence=tuple(evidence),
            draft=draft,
            prompt_identity=prompt_identity,
            project_revision=project_revision,
        )
    except ValidationError:
        return AgenticReviewResult(
            status=AgenticReviewStatus.INPUT_REJECTED,
            failure_code="invalid_review_input",
        )

    try:
        rendered = render_review_prompt(
            review_input,
            max_prompt_bytes=settings.max_prompt_bytes,
        )
    except PromptTooLargeError:
        return AgenticReviewResult(
            status=AgenticReviewStatus.INPUT_REJECTED,
            failure_code="prompt_too_large",
        )

    review_provider = provider or OpenAICompatibleAdapter(settings)
    writer = evidence_store or InvocationEvidenceStore(artifact_root)
    make_invocation_id = invocation_id_factory or _new_invocation_id
    current_time = clock or _utc_now
    invocation_id = make_invocation_id()

    try:
        provider_response = review_provider.invoke(rendered)
    except ProviderUnavailableError as error:
        record = _build_record(
            invocation_id=invocation_id,
            recorded_at=current_time(),
            status=AgenticReviewStatus.UNAVAILABLE,
            settings=settings,
            review_input=review_input,
            rendered=rendered,
            parsed_output=None,
            validation=None,
            failure_code=error.failure_code,
            latency_ms=error.latency_ms,
            attempt_count=error.attempt_count,
            usage=None,
            trace_id=None,
        )
        return _persist_result(record=record, settings=settings, writer=writer)
    except ProviderResponseTooLargeError as error:
        record = _build_record(
            invocation_id=invocation_id,
            recorded_at=current_time(),
            status=AgenticReviewStatus.VALIDATION_FAILED,
            settings=settings,
            review_input=review_input,
            rendered=rendered,
            parsed_output=None,
            validation=None,
            failure_code="response_too_large",
            latency_ms=error.latency_ms,
            attempt_count=error.attempt_count,
            usage=error.usage,
            trace_id=error.trace_id,
        )
        return _persist_result(record=record, settings=settings, writer=writer)

    parsed_output = _parse_output(provider_response.content)
    if parsed_output is None:
        record = _build_record(
            invocation_id=invocation_id,
            recorded_at=current_time(),
            status=AgenticReviewStatus.VALIDATION_FAILED,
            settings=settings,
            review_input=review_input,
            rendered=rendered,
            parsed_output=None,
            validation=None,
            failure_code="response_schema_invalid",
            latency_ms=provider_response.latency_ms,
            attempt_count=provider_response.attempt_count,
            usage=provider_response.usage,
            trace_id=provider_response.trace_id,
        )
        return _persist_result(record=record, settings=settings, writer=writer)

    validation = validate_agentic_review(review_input, parsed_output)
    if validation.status is ReviewValidationStatus.REJECTED:
        status = AgenticReviewStatus.VALIDATION_FAILED
        failure_code = "deterministic_guard_failed"
    else:
        status = AgenticReviewStatus.ACCEPTED
        failure_code = None
    record = _build_record(
        invocation_id=invocation_id,
        recorded_at=current_time(),
        status=status,
        settings=settings,
        review_input=review_input,
        rendered=rendered,
        parsed_output=parsed_output,
        validation=validation,
        failure_code=failure_code,
        latency_ms=provider_response.latency_ms,
        attempt_count=provider_response.attempt_count,
        usage=provider_response.usage,
        trace_id=provider_response.trace_id,
    )
    return _persist_result(record=record, settings=settings, writer=writer)


def _parse_output(content: str) -> AgenticReviewOutput | None:
    try:
        payload = json.loads(content)
        return AgenticReviewOutput.model_validate(payload)
    except (json.JSONDecodeError, TypeError, ValidationError):
        return None


def _build_record(
    *,
    invocation_id: str,
    recorded_at: datetime,
    status: AgenticReviewStatus,
    settings: AgenticReviewSettings,
    review_input: AgenticReviewInput,
    rendered: RenderedPrompt,
    parsed_output: AgenticReviewOutput | None,
    validation: AgenticReviewValidation | None,
    failure_code: str | None,
    latency_ms: float,
    attempt_count: int,
    usage: ProviderUsage | None,
    trace_id: str | None,
) -> AgenticInvocationEvidence:
    return AgenticInvocationEvidence(
        invocation_id=invocation_id,
        recorded_at=recorded_at,
        status=status,
        configuration=SanitizedAgenticReviewConfiguration.model_validate(
            settings.sanitized_configuration()
        ),
        prompt_identity=review_input.prompt_identity,
        prompt_digest=rendered.prompt_digest,
        project_revision=review_input.project_revision,
        incident_id=review_input.incident.incident_id,
        evidence_refs=tuple(item.evidence_id for item in review_input.evidence),
        canonical_input=rendered.canonical_input,
        parsed_output=parsed_output,
        validation=validation,
        failure_code=failure_code,
        latency_ms=latency_ms,
        attempt_count=attempt_count,
        usage=usage,
        trace_id=trace_id,
    )


def _persist_result(
    *,
    record: AgenticInvocationEvidence,
    settings: AgenticReviewSettings,
    writer: InvocationEvidenceWriter,
) -> AgenticReviewResult:
    max_record_bytes = settings.max_prompt_bytes + settings.max_output_bytes + 16_384
    try:
        path = writer.write(record, max_record_bytes=max_record_bytes)
    except InvocationEvidenceStoreError:
        return AgenticReviewResult(
            status=AgenticReviewStatus.PROVENANCE_FAILED,
            invocation_id=record.invocation_id,
            failure_code="invocation_evidence_write_failed",
        )

    if record.status is AgenticReviewStatus.ACCEPTED:
        return AgenticReviewResult(
            status=record.status,
            output=record.parsed_output,
            validation=record.validation,
            invocation_id=record.invocation_id,
            invocation_path=path,
        )
    return AgenticReviewResult(
        status=record.status,
        validation=record.validation,
        invocation_id=record.invocation_id,
        invocation_path=path,
        failure_code=record.failure_code,
    )


def _new_invocation_id() -> str:
    return f"ar-{uuid4().hex}"


def _utc_now() -> datetime:
    return datetime.now(tz=UTC)
