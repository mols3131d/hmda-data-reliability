"""Typed orchestration and read-only boundary integration tests."""

from __future__ import annotations

from collections.abc import Sequence
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path

import pytest

from hmda_reliability.reliability.agentic_review import contracts
from hmda_reliability.reliability.agentic_review import provider as provider_module
from hmda_reliability.reliability.agentic_review import service as service_module
from hmda_reliability.reliability.agentic_review import store as store_module
from hmda_reliability.reliability.agentic_review.evidence import (
    AgenticInvocationEvidence,
)
from hmda_reliability.reliability.agentic_review.prompt import RenderedPrompt
from hmda_reliability.reliability.agentic_review.settings import AgenticReviewSettings
from hmda_reliability.reliability.contracts import Evidence

from .conftest import NullSpikeReviewMaterial

pytestmark = pytest.mark.integration


def _settings(**updates: object) -> AgenticReviewSettings:
    values: dict[str, object] = {
        "base_url": "http://localhost:11434/v1",
        "api_key": "local-test-key",
        "model": "test-model",
    }
    values.update(updates)
    return AgenticReviewSettings.model_validate(values)


def _review_input(material: NullSpikeReviewMaterial) -> contracts.AgenticReviewInput:
    return contracts.AgenticReviewInput(
        incident=material.detection.incident,
        evidence=[material.detection.evidence],
        draft=material.draft,
        prompt_identity=contracts.PromptIdentity(),
        project_revision="e09c54b",
    )


def _safe_output(material: NullSpikeReviewMaterial) -> contracts.AgenticReviewOutput:
    review_input = _review_input(material)
    evidence_id = review_input.evidence[0].evidence_id
    return contracts.AgenticReviewOutput(
        incident_id=review_input.incident.incident_id,
        incident_type="null_spike",
        target_column=review_input.target_column,
        deterministic_facts=review_input.deterministic_facts,
        review_summary="제공된 canonical facts와 draft가 일치한다.",
        evidence_used=[evidence_id],
        findings=[],
        uncertainties=["Root cause는 human review가 필요하다."],
        advisory_recommendation="needs_human_review",
    )


class FakeProvider:
    def __init__(
        self,
        outcome: (
            provider_module.ProviderResponse
            | provider_module.ProviderUnavailableError
            | provider_module.ProviderResponseTooLargeError
        ),
        events: list[str] | None = None,
    ) -> None:
        self.outcome = outcome
        self.calls = 0
        self.events = events

    def invoke(self, rendered: RenderedPrompt) -> provider_module.ProviderResponse:
        self.calls += 1
        if self.events is not None:
            self.events.append("provider")
        if isinstance(self.outcome, Exception):
            raise self.outcome
        return self.outcome


class RecordingStore:
    def __init__(self, root: Path, events: list[str] | None = None) -> None:
        self.delegate = store_module.InvocationEvidenceStore(root)
        self.events = events
        self.records: list[AgenticInvocationEvidence] = []

    def write(
        self,
        record: AgenticInvocationEvidence,
        *,
        max_record_bytes: int,
    ) -> Path:
        self.records.append(record)
        if self.events is not None:
            self.events.append("store")
        return self.delegate.write(record, max_record_bytes=max_record_bytes)


class FailingStore:
    def write(
        self,
        record: AgenticInvocationEvidence,
        *,
        max_record_bytes: int,
    ) -> Path:
        raise store_module.InvocationEvidenceWriteError("simulated durable failure")


def _call(
    material: NullSpikeReviewMaterial,
    *,
    provider: service_module.ReviewProvider,
    evidence_store: service_module.InvocationEvidenceWriter,
    settings: AgenticReviewSettings | None = None,
    evidence: Sequence[Evidence] | None = None,
) -> contracts.AgenticReviewResult:
    return service_module.review_null_spike(
        incident=material.detection.incident,
        evidence=([material.detection.evidence] if evidence is None else evidence),
        draft=material.draft,
        prompt_identity=contracts.PromptIdentity(),
        project_revision="e09c54b",
        settings=settings or _settings(),
        provider=provider,
        evidence_store=evidence_store,
        invocation_id_factory=lambda: "inv-fixed",
        clock=lambda: datetime(2026, 8, 27, 2, 0, tzinfo=UTC),
    )


def test_accepted_review_is_validated_then_persisted_and_returned(
    tmp_path: Path,
    null_spike_review_material: NullSpikeReviewMaterial,
) -> None:
    material = null_spike_review_material
    events: list[str] = []
    provider = FakeProvider(
        provider_module.ProviderResponse(
            content=_safe_output(material).model_dump_json(),
            attempt_count=1,
            latency_ms=12.5,
            usage=provider_module.ProviderUsage(total_tokens=123),
            trace_id="req-1",
        ),
        events,
    )
    store = RecordingStore(tmp_path, events)

    result = _call(material, provider=provider, evidence_store=store)

    assert result.status == "accepted"
    assert result.output == _safe_output(material)
    assert result.validation is not None
    assert result.validation.status == "accepted"
    assert result.invocation_id == "inv-fixed"
    assert result.invocation_path is not None
    assert result.invocation_path.exists()
    assert events == ["provider", "store"]
    record = store.delegate.load("inv-fixed")
    assert record.status == "accepted"
    assert record.canonical_input == store.records[0].canonical_input
    assert record.trace_id == "req-1"


@pytest.mark.parametrize(
    ("evidence", "max_prompt_bytes", "failure_code"),
    [([], 65_536, "invalid_review_input"), (None, 64, "prompt_too_large")],
)
def test_preflight_rejection_never_calls_provider_or_evidence_store(
    tmp_path: Path,
    null_spike_review_material: NullSpikeReviewMaterial,
    evidence: Sequence[Evidence] | None,
    max_prompt_bytes: int,
    failure_code: str,
) -> None:
    provider = FakeProvider(
        provider_module.ProviderResponse(
            content="{}",
            attempt_count=1,
            latency_ms=1,
        )
    )
    store = RecordingStore(tmp_path)

    result = _call(
        null_spike_review_material,
        provider=provider,
        evidence_store=store,
        settings=_settings(max_prompt_bytes=max_prompt_bytes),
        evidence=evidence,
    )

    assert result.status == "input_rejected"
    assert result.failure_code == failure_code
    assert result.invocation_id is None
    assert provider.calls == 0
    assert store.records == []
    assert not tmp_path.joinpath("agentic-review").exists()


def test_schema_and_guard_failures_are_persisted_without_exposing_output(
    tmp_path: Path,
    null_spike_review_material: NullSpikeReviewMaterial,
) -> None:
    material = null_spike_review_material
    cases = [
        ("not-json", "response_schema_invalid", None),
        (
            _safe_output(material)
            .model_copy(update={"evidence_used": ("ev-fabricated",)})
            .model_dump_json(),
            "deterministic_guard_failed",
            "fabricated_evidence",
        ),
    ]

    for index, (content, failure_code, violation) in enumerate(cases):
        root = tmp_path / str(index)
        store = RecordingStore(root)
        result = service_module.review_null_spike(
            incident=material.detection.incident,
            evidence=[material.detection.evidence],
            draft=material.draft,
            prompt_identity=contracts.PromptIdentity(),
            project_revision="e09c54b",
            settings=_settings(),
            provider=FakeProvider(
                provider_module.ProviderResponse(
                    content=content,
                    attempt_count=1,
                    latency_ms=5,
                )
            ),
            evidence_store=store,
            invocation_id_factory=lambda index=index: f"inv-{index}",
            clock=lambda: datetime(2026, 8, 27, 2, 0, tzinfo=UTC),
        )

        assert result.status == "validation_failed"
        assert result.output is None
        assert result.failure_code == failure_code
        record = store.delegate.load(f"inv-{index}")
        assert record.status == "validation_failed"
        if violation is None:
            assert record.parsed_output is None
            assert record.validation is None
            assert result.invocation_path is not None
            assert content not in result.invocation_path.read_text(encoding="utf-8")
        else:
            assert record.parsed_output is not None
            assert record.validation is not None
            assert violation in record.validation.violations


def test_unavailable_provider_is_typed_and_persisted(
    tmp_path: Path,
    null_spike_review_material: NullSpikeReviewMaterial,
) -> None:
    provider = FakeProvider(
        provider_module.ProviderUnavailableError(
            failure_code="provider_connection_error",
            attempt_count=2,
            latency_ms=75,
        )
    )
    store = RecordingStore(tmp_path)

    result = _call(
        null_spike_review_material,
        provider=provider,
        evidence_store=store,
    )

    assert result.status == "unavailable"
    assert result.output is None
    assert result.failure_code == "provider_connection_error"
    record = store.delegate.load("inv-fixed")
    assert record.status == "unavailable"
    assert record.attempt_count == 2
    assert record.parsed_output is None


def test_persistence_failure_blocks_an_otherwise_accepted_result(
    null_spike_review_material: NullSpikeReviewMaterial,
) -> None:
    provider = FakeProvider(
        provider_module.ProviderResponse(
            content=_safe_output(null_spike_review_material).model_dump_json(),
            attempt_count=1,
            latency_ms=5,
        )
    )

    result = _call(
        null_spike_review_material,
        provider=provider,
        evidence_store=FailingStore(),
    )

    assert result.status == "provenance_failed"
    assert result.output is None
    assert result.invocation_id == "inv-fixed"
    assert result.invocation_path is None
    assert result.failure_code == "invocation_evidence_write_failed"


def test_review_preserves_reliability_objects_and_target_state(
    tmp_path: Path,
    null_spike_review_material: NullSpikeReviewMaterial,
) -> None:
    material = null_spike_review_material
    before = {
        "incident": deepcopy(material.detection.incident.model_dump(mode="python")),
        "evidence": deepcopy(material.detection.evidence.model_dump(mode="python")),
        "draft": deepcopy(material.draft.model_dump(mode="python")),
    }
    target_state = tmp_path / "target-state.txt"
    target_state.write_text("unchanged", encoding="utf-8")
    provider = FakeProvider(
        provider_module.ProviderResponse(
            content=_safe_output(material).model_dump_json(),
            attempt_count=1,
            latency_ms=5,
        )
    )

    result = _call(
        material,
        provider=provider,
        evidence_store=RecordingStore(tmp_path / "artifacts"),
    )

    assert result.status == "accepted"
    assert material.detection.incident.model_dump(mode="python") == before["incident"]
    assert material.detection.evidence.model_dump(mode="python") == before["evidence"]
    assert material.draft.model_dump(mode="python") == before["draft"]
    assert target_state.read_text(encoding="utf-8") == "unchanged"


def test_service_returns_provenance_failed_on_real_store_directory_error(
    tmp_path: Path,
    null_spike_review_material: NullSpikeReviewMaterial,
) -> None:
    blocked_file = tmp_path / "blocked"
    blocked_file.write_text("file-not-dir", encoding="utf-8")
    provider = FakeProvider(
        provider_module.ProviderResponse(
            content=_safe_output(null_spike_review_material).model_dump_json(),
            attempt_count=1,
            latency_ms=5,
        )
    )

    result = service_module.review_null_spike(
        incident=null_spike_review_material.detection.incident,
        evidence=[null_spike_review_material.detection.evidence],
        draft=null_spike_review_material.draft,
        prompt_identity=contracts.PromptIdentity(),
        project_revision="e09c54b",
        settings=_settings(),
        provider=provider,
        artifact_root=blocked_file,
    )

    assert result.status == "provenance_failed"
    assert result.output is None
    assert result.failure_code == "invocation_evidence_write_failed"
