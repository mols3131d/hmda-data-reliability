"""Logical invocation evidence contracts."""

from __future__ import annotations

import urllib.parse
from copy import deepcopy
from datetime import UTC, datetime
from typing import Literal

from pydantic import Field, field_validator, model_validator

from hmda_reliability.reliability.contracts.base import ReliabilityContract
from hmda_reliability.review_ai.contracts import (
    AgenticReviewOutput,
    AgenticReviewStatus,
    AgenticReviewValidation,
    PromptIdentity,
    ReviewValidationStatus,
)
from hmda_reliability.runtime_ai.contracts import ProviderUsage


class SanitizedAgenticReviewConfiguration(ReliabilityContract):
    """Persistable provider configuration with no credential field."""

    base_url: str = Field(min_length=1, max_length=2048)
    model: str = Field(min_length=1, max_length=512)
    timeout_seconds: float = Field(gt=0, le=300)
    max_retries: int = Field(ge=0, le=5)
    temperature: Literal[0]
    max_output_tokens: int = Field(gt=0, le=32_768)
    max_prompt_bytes: int = Field(gt=0, le=1_048_576)
    max_output_bytes: int = Field(gt=0, le=1_048_576)

    @field_validator("base_url")
    @classmethod
    def _validate_base_url(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            msg = "base_url must be non-empty"
            raise ValueError(msg)
        parsed = urllib.parse.urlsplit(normalized)
        if parsed.username is not None or parsed.password is not None:
            msg = "sanitized base_url must not contain credentials"
            raise ValueError(msg)
        if parsed.query:
            msg = "sanitized base_url must not contain query parameters"
            raise ValueError(msg)
        if parsed.fragment:
            msg = "sanitized base_url must not contain URL fragments"
            raise ValueError(msg)
        return normalized


class AgenticInvocationEvidence(ReliabilityContract):
    """One sanitized record for one logical provider-started invocation."""

    invocation_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
    recorded_at: datetime
    status: AgenticReviewStatus
    configuration: SanitizedAgenticReviewConfiguration
    prompt_identity: PromptIdentity
    prompt_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    project_revision: str = Field(min_length=1, max_length=256)
    incident_id: str = Field(min_length=1, max_length=256)
    evidence_refs: tuple[str, ...] = Field(min_length=1, max_length=64)
    canonical_input: dict[str, object]
    parsed_output: AgenticReviewOutput | None = None
    validation: AgenticReviewValidation | None = None
    failure_code: str | None = Field(default=None, max_length=256)
    latency_ms: float = Field(ge=0)
    attempt_count: int = Field(ge=1)
    usage: ProviderUsage | None = None
    trace_id: str | None = Field(default=None, max_length=512)

    @field_validator("recorded_at")
    @classmethod
    def _normalize_recorded_at(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    @field_validator("canonical_input", mode="before")
    @classmethod
    def _snapshot_canonical_input(cls, value: object) -> object:
        return deepcopy(value)

    @field_validator(
        "project_revision",
        "incident_id",
        "failure_code",
        "trace_id",
    )
    @classmethod
    def _normalize_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            msg = "invocation evidence text fields must be non-empty"
            raise ValueError(msg)
        return normalized

    @field_validator("evidence_refs")
    @classmethod
    def _validate_evidence_refs(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if any(not value.strip() for value in values):
            msg = "evidence_refs must be non-empty"
            raise ValueError(msg)
        if len(values) != len(set(values)):
            msg = "evidence_refs must be unique"
            raise ValueError(msg)
        return values

    @model_validator(mode="after")
    def _validate_status_payload(self) -> AgenticInvocationEvidence:
        if self.status not in {
            AgenticReviewStatus.ACCEPTED,
            AgenticReviewStatus.VALIDATION_FAILED,
            AgenticReviewStatus.UNAVAILABLE,
        }:
            msg = "only provider-started outcomes can be persisted"
            raise ValueError(msg)

        if self.status is AgenticReviewStatus.ACCEPTED:
            if (
                self.parsed_output is None
                or self.validation is None
                or self.validation.status is not ReviewValidationStatus.ACCEPTED
                or self.failure_code is not None
            ):
                msg = "accepted evidence requires accepted output and validation"
                raise ValueError(msg)
        elif self.status is AgenticReviewStatus.VALIDATION_FAILED:
            if self.failure_code is None:
                msg = "validation_failed evidence requires a failure code"
                raise ValueError(msg)
            if (
                self.validation is not None
                and self.validation.status is not ReviewValidationStatus.REJECTED
            ):
                msg = "validation_failed evidence cannot contain accepted validation"
                raise ValueError(msg)
        elif self.status is AgenticReviewStatus.UNAVAILABLE and (
            self.parsed_output is not None
            or self.validation is not None
            or self.failure_code is None
        ):
            msg = "unavailable evidence contains only a typed failure"
            raise ValueError(msg)
        return self
