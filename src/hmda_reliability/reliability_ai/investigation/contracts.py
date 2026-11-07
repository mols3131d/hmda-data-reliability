"""인시던트 조사(investigation) 계약 모델 정의 모듈."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from pydantic import Field

from hmda_reliability.reliability.contracts.base import ReliabilityContract
from hmda_reliability.runtime_ai.contracts import (
    ProviderResponseMetadata,
    ProviderUsage,
)


class ToolCallRecord(ReliabilityContract):
    """실행된 단일 도구 호출의 입력, 결과, 지연 시간 기록."""

    call_id: str
    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    result: dict[str, Any] = Field(default_factory=dict)
    latency_ms: float = Field(ge=0.0)
    status: Literal["success", "error"]


class InvestigationFinding(ReliabilityContract):
    """조사 과정에서 확인된 개별 사실/발견점."""

    topic: str = Field(min_length=1)
    description: str = Field(min_length=1)
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)


class InvestigationHypothesis(ReliabilityContract):
    """원인 또는 영향에 대한 검증 가설."""

    hypothesis: str = Field(min_length=1)
    status: Literal["supported", "rejected", "uncertain"]
    rationale: str = Field(min_length=1)


class InvestigationUncertainty(ReliabilityContract):
    """현재 증거만으로는 확정할 수 없는 불확실성 및 추가 확인 필요성."""

    topic: str = Field(min_length=1)
    description: str = Field(min_length=1)
    needed_evidence: str = Field(min_length=1)


class InvestigationTurnRecord(ReliabilityContract):
    """에이전트 단일 턴 실행 기록."""

    turn: int = Field(ge=0)
    role: str
    content: str = ""
    tool_call_id: str | None = None
    tool_calls: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    latency_ms: float = Field(default=0.0, ge=0.0)
    attempt_count: int | None = Field(default=None, ge=0)
    usage: ProviderUsage | None = None
    response_metadata: ProviderResponseMetadata | None = None
    failure_code: str | None = None


class InvestigationResult(ReliabilityContract):
    """도구 기반 조사 루프의 최종 결과 계약."""

    incident_id: str
    status: Literal["completed", "budget_exhausted", "tool_cycle_detected", "error"]
    failure_code: str | None = None
    facts: dict[str, Any] = Field(default_factory=dict)
    findings: tuple[InvestigationFinding, ...] = Field(default_factory=tuple)
    hypotheses: tuple[InvestigationHypothesis, ...] = Field(default_factory=tuple)
    uncertainties: tuple[InvestigationUncertainty, ...] = Field(default_factory=tuple)
    tool_calls: tuple[ToolCallRecord, ...] = Field(default_factory=tuple)
    invocation_id: str | None = None
    response_paths: tuple[Path, ...] = Field(default_factory=tuple)
    turns: tuple[InvestigationTurnRecord, ...] = Field(default_factory=tuple)
    manifest_path: Path | None = None
