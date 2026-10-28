"""조회 전용(Read-only) null-spike agentic review 오케스트레이션 모듈."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol
from uuid import uuid4

from pydantic import ValidationError

from hmda_reliability.logger import get_logger
from hmda_reliability.reliability.contracts import Evidence, Incident
from hmda_reliability.reliability.remediation import RemediationDraft
from hmda_reliability.review_ai.context import ReviewContextTooLargeError
from hmda_reliability.review_ai.contracts import (
    AgenticReviewInput,
    AgenticReviewOutput,
    AgenticReviewResult,
    AgenticReviewStatus,
    AgenticReviewValidation,
    PromptIdentity,
    ReviewValidationStatus,
)
from hmda_reliability.review_ai.diagnostics import (
    ReviewResponseDiagnostics,
    parse_review_response,
)
from hmda_reliability.review_ai.evidence import (
    AgenticInvocationEvidence,
    SanitizedAgenticReviewConfiguration,
)
from hmda_reliability.review_ai.prompt import (
    PromptTooLargeError,
    RenderedReviewPrompt,
    render_review_prompt,
)
from hmda_reliability.review_ai.settings import ReviewAISettings
from hmda_reliability.review_ai.store import (
    InvocationEvidenceExistsError,
    InvocationEvidenceStore,
    InvocationEvidenceStoreError,
    InvocationResponseStore,
)
from hmda_reliability.review_ai.validator import validate_agentic_review
from hmda_reliability.runtime_ai.contracts import (
    ChatMessage,
    ProviderResponse,
    ProviderResponseMetadata,
    ProviderUsage,
)
from hmda_reliability.runtime_ai.provider import (
    OpenAICompatibleAdapter,
    ProviderResponseTooLargeError,
    ProviderUnavailableError,
)
from hmda_reliability.runtime_ai.settings import RuntimeAISettings

_LOGGER = get_logger(__name__)


class ReviewProvider(Protocol):
    def invoke(self, messages: tuple[ChatMessage, ...]) -> ProviderResponse: ...


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
    settings: RuntimeAISettings,
    review_settings: ReviewAISettings | None = None,
    provider: ReviewProvider | None = None,
    evidence_store: InvocationEvidenceWriter | None = None,
    artifact_root: Path = Path(".local/artifacts"),
    invocation_id_factory: Callable[[], str] | None = None,
    clock: Callable[[], datetime] | None = None,
) -> AgenticReviewResult:
    """저장소 상태 변경 없이 evidence 기반의 advisory review 결과를 생성한다.

    전체 조회 전용 review 라이프사이클을 오케스트레이션한다:
    1. `review_input`의 유효성을 검증하고 불변 스냅샷을 생성한다.
    2. `max_prompt_bytes` 제한 아래에서 표준(canonical) 프롬프트를 렌더링한다.
    3. 재시도 및 타임아웃 경계가 적용된 `runtime_ai` 어댑터를 통해 provider를 호출한다.
    4. 응답 본문을 로컬에 보존한 뒤 JSON과 구조화된 사실을 검증한다.
    5. 감사 및 재현(replay)을 위해 정제된 호출 evidence를 디스크에 영속화한다.

    성공 시 `ACCEPTED` 상태의 `AgenticReviewResult`를 반환하며, 실패 시
    적절한 실패 상태(`INPUT_REJECTED`, `UNAVAILABLE`, `VALIDATION_FAILED`,
    `PROVENANCE_FAILED`)를 반환한다.
    """

    active_review_settings = review_settings or ReviewAISettings()
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
            max_prompt_bytes=active_review_settings.max_prompt_bytes,
        )
    except PromptTooLargeError:
        return AgenticReviewResult(
            status=AgenticReviewStatus.INPUT_REJECTED,
            failure_code="prompt_too_large",
        )
    except ReviewContextTooLargeError:
        return AgenticReviewResult(
            status=AgenticReviewStatus.INPUT_REJECTED,
            failure_code="context_too_large",
        )

    review_provider = provider or OpenAICompatibleAdapter(settings)
    writer = evidence_store or InvocationEvidenceStore(artifact_root)
    current_time = clock or _utc_now
    make_invocation_id = invocation_id_factory or (
        lambda: _new_invocation_id(current_time())
    )
    invocation_id = make_invocation_id()
    session = _ReviewSession(
        invocation_id=invocation_id,
        clock=current_time,
        settings=settings,
        review_settings=active_review_settings,
        review_input=review_input,
        rendered=rendered,
        writer=writer,
    )

    try:
        provider_response = review_provider.invoke(rendered.messages)
    except ProviderUnavailableError as error:
        return session.record_and_persist(
            status=AgenticReviewStatus.UNAVAILABLE,
            failure_code=error.failure_code,
            latency_ms=error.latency_ms,
            attempt_count=error.attempt_count,
        )
    except ProviderResponseTooLargeError as error:
        return session.record_and_persist(
            status=AgenticReviewStatus.VALIDATION_FAILED,
            failure_code="response_too_large",
            latency_ms=error.latency_ms,
            attempt_count=error.attempt_count,
            usage=error.usage,
            trace_id=error.trace_id,
            response_metadata=error.response_metadata,
        )

    try:
        response_path = InvocationResponseStore(artifact_root).write(
            invocation_id,
            provider_response.content,
            max_response_bytes=settings.max_output_bytes,
        )
    except InvocationEvidenceStoreError:
        return AgenticReviewResult(
            status=AgenticReviewStatus.PROVENANCE_FAILED,
            invocation_id=invocation_id,
            failure_code="invocation_response_write_failed",
        )
    session = replace(session, response_path=response_path)

    parsed_output, diagnostics = parse_review_response(provider_response.content)
    if parsed_output is None:
        return session.record_and_persist(
            status=AgenticReviewStatus.VALIDATION_FAILED,
            failure_code="response_schema_invalid",
            latency_ms=provider_response.latency_ms,
            attempt_count=provider_response.attempt_count,
            usage=provider_response.usage,
            trace_id=provider_response.trace_id,
            response_metadata=provider_response.response_metadata,
            response_diagnostics=diagnostics,
        )

    # 결정론적 구조 및 사실 가드레일 검증
    bounded_context = rendered.context
    if bounded_context is None:  # pragma: no cover
        # `render_review_prompt` always binds a context for this service path.
        raise RuntimeError("review prompt is missing bounded context")
    validation = validate_agentic_review(
        review_input,
        parsed_output,
        allowed_evidence_ids={
            item.evidence_id for item in bounded_context.selected_evidence
        },
    )
    if validation.status is ReviewValidationStatus.REJECTED:
        status = AgenticReviewStatus.VALIDATION_FAILED
        failure_code = "deterministic_guard_failed"
        _LOGGER.warning(
            "review 결정론적 검증 실패",
            extra={
                "invocation_id": invocation_id,
                "incident_id": review_input.incident.incident_id,
                "violations": [str(v) for v in validation.violations],
            },
        )
    else:
        status = AgenticReviewStatus.ACCEPTED
        failure_code = None

    return session.record_and_persist(
        status=status,
        parsed_output=parsed_output,
        validation=validation,
        failure_code=failure_code,
        latency_ms=provider_response.latency_ms,
        attempt_count=provider_response.attempt_count,
        usage=provider_response.usage,
        trace_id=provider_response.trace_id,
        response_metadata=provider_response.response_metadata,
    )


@dataclass(frozen=True)
class _ReviewSession:
    """단일 review 요청에서 변하지 않는 컨텍스트를 바인딩하여 증적 조립을 캡슐화한다."""

    invocation_id: str
    clock: Callable[[], datetime]
    settings: RuntimeAISettings
    review_settings: ReviewAISettings
    review_input: AgenticReviewInput
    rendered: RenderedReviewPrompt
    writer: InvocationEvidenceWriter
    response_path: Path | None = None

    def record_and_persist(
        self,
        *,
        status: AgenticReviewStatus,
        parsed_output: AgenticReviewOutput | None = None,
        validation: AgenticReviewValidation | None = None,
        failure_code: str | None = None,
        latency_ms: float = 0.0,
        attempt_count: int = 1,
        usage: ProviderUsage | None = None,
        trace_id: str | None = None,
        response_metadata: ProviderResponseMetadata | None = None,
        response_diagnostics: ReviewResponseDiagnostics | None = None,
    ) -> AgenticReviewResult:
        record = self._build_record(
            status=status,
            parsed_output=parsed_output,
            validation=validation,
            failure_code=failure_code,
            latency_ms=latency_ms,
            attempt_count=attempt_count,
            usage=usage,
            trace_id=trace_id,
            response_metadata=response_metadata,
            response_diagnostics=response_diagnostics,
        )
        return _persist_result(
            record=record,
            settings=self.settings,
            review_settings=self.review_settings,
            writer=self.writer,
            response_path=self.response_path,
        )

    def _build_record(
        self,
        *,
        status: AgenticReviewStatus,
        parsed_output: AgenticReviewOutput | None,
        validation: AgenticReviewValidation | None,
        failure_code: str | None,
        latency_ms: float,
        attempt_count: int,
        usage: ProviderUsage | None,
        trace_id: str | None,
        response_metadata: ProviderResponseMetadata | None,
        response_diagnostics: ReviewResponseDiagnostics | None,
    ) -> AgenticInvocationEvidence:
        configuration = self.settings.sanitized_configuration()
        configuration.update(self.review_settings.sanitized_configuration())
        bounded_context = self.rendered.context
        if bounded_context is None:  # pragma: no cover
            # `_ReviewSession` is created only from `render_review_prompt`.
            raise RuntimeError("review prompt is missing bounded context")
        return AgenticInvocationEvidence(
            invocation_id=self.invocation_id,
            recorded_at=self.clock(),
            status=status,
            configuration=SanitizedAgenticReviewConfiguration.model_validate(
                configuration
            ),
            prompt_identity=self.review_input.prompt_identity,
            prompt_digest=self.rendered.prompt_digest,
            project_revision=self.review_input.project_revision,
            incident_id=self.review_input.incident.incident_id,
            evidence_refs=tuple(
                item.evidence_id for item in bounded_context.selected_evidence
            ),
            canonical_input=self.rendered.canonical_input,
            parsed_output=parsed_output,
            validation=validation,
            failure_code=failure_code,
            latency_ms=latency_ms,
            attempt_count=attempt_count,
            usage=usage,
            trace_id=trace_id,
            response_metadata=response_metadata,
            response_diagnostics=response_diagnostics,
        )


def _persist_result(
    *,
    record: AgenticInvocationEvidence,
    settings: RuntimeAISettings,
    review_settings: ReviewAISettings,
    writer: InvocationEvidenceWriter,
    response_path: Path | None = None,
) -> AgenticReviewResult:
    """호출 증적 레코드를 디스크에 영속화하고 최종 AgenticReviewResult를 조립한다.

    저장 허용 바이트(`max_record_bytes`)는 설정된 프롬프트 한도와 출력 한도에
    16KiB의 표준 JSON 메타데이터 오버헤드를 합산하여 산정한다.
    디스크 쓰기 실패 시 예외를 전파하지 않고 `PROVENANCE_FAILED` 상태를 반환하여
    호출자에게 증적 불완전성을 명확히 알린다.
    """
    max_record_bytes = (
        review_settings.max_prompt_bytes + settings.max_output_bytes + 16_384
    )
    try:
        path = writer.write(record, max_record_bytes=max_record_bytes)
    except InvocationEvidenceStoreError as error:
        if (
            isinstance(error, InvocationEvidenceExistsError)
            and response_path is not None
        ):
            # 새 응답을 기존의 다른 invocation과 연결하지 않는다.
            try:
                response_path.unlink()
            except OSError:
                pass
            else:
                response_path = None
        _LOGGER.error(
            "호출 evidence 영속화 실패",
            extra={
                "invocation_id": record.invocation_id,
                "incident_id": record.incident_id,
            },
        )
        return AgenticReviewResult(
            status=AgenticReviewStatus.PROVENANCE_FAILED,
            invocation_id=record.invocation_id,
            response_path=response_path,
            failure_code="invocation_evidence_write_failed",
        )

    _LOGGER.info(
        "null-spike agentic review 완료",
        extra={
            "invocation_id": record.invocation_id,
            "incident_id": record.incident_id,
            "status": record.status,
            "prompt_digest": record.prompt_digest,
        },
    )
    if record.status is AgenticReviewStatus.ACCEPTED:
        return AgenticReviewResult(
            status=record.status,
            output=record.parsed_output,
            validation=record.validation,
            invocation_id=record.invocation_id,
            invocation_path=path,
            response_path=response_path,
        )
    return AgenticReviewResult(
        status=record.status,
        validation=record.validation,
        invocation_id=record.invocation_id,
        invocation_path=path,
        response_path=response_path,
        failure_code=record.failure_code,
    )


def _new_invocation_id(now: datetime | None = None) -> str:
    timestamp = (now or _utc_now()).strftime("%Y%m%d")
    return f"ar-{timestamp}-{uuid4().hex[:12]}"


def _utc_now() -> datetime:
    return datetime.now(tz=UTC)
