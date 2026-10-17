"""Typed orchestration and read-only boundary integration tests."""

from __future__ import annotations

from collections.abc import Sequence
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path

import pytest

from hmda_reliability.reliability.contracts import Evidence
from hmda_reliability.review_ai import contracts
from hmda_reliability.review_ai import service as service_module
from hmda_reliability.review_ai import store as store_module
from hmda_reliability.review_ai.evidence import AgenticInvocationEvidence
from hmda_reliability.review_ai.settings import ReviewAISettings
from hmda_reliability.runtime_ai import contracts as runtime_contracts
from hmda_reliability.runtime_ai import provider as provider_module
from hmda_reliability.runtime_ai.settings import RuntimeAISettings

from .conftest import NullSpikeReviewMaterial

pytestmark = pytest.mark.integration


def _settings(**updates: object) -> RuntimeAISettings:
    values: dict[str, object] = {
        "base_url": "http://localhost:11434/v1",
        "api_key": "local-test-key",
        "model": "test-model",
    }
    values.update(updates)
    return RuntimeAISettings.model_validate(values)


def _review_settings(**updates: object) -> ReviewAISettings:
    return ReviewAISettings.model_validate(updates)


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
            runtime_contracts.ProviderResponse
            | provider_module.ProviderUnavailableError
            | provider_module.ProviderResponseTooLargeError
        ),
        events: list[str] | None = None,
    ) -> None:
        self.outcome = outcome
        self.calls = 0
        self.events = events

    def invoke(
        self,
        messages: tuple[runtime_contracts.ChatMessage, ...],
    ) -> runtime_contracts.ProviderResponse:
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
    settings: RuntimeAISettings | None = None,
    review_settings: ReviewAISettings | None = None,
    evidence: Sequence[Evidence] | None = None,
) -> contracts.AgenticReviewResult:
    return service_module.review_null_spike(
        incident=material.detection.incident,
        evidence=([material.detection.evidence] if evidence is None else evidence),
        draft=material.draft,
        prompt_identity=contracts.PromptIdentity(),
        project_revision="e09c54b",
        settings=settings or _settings(),
        review_settings=review_settings,
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
        runtime_contracts.ProviderResponse(
            content=_safe_output(material).model_dump_json(),
            attempt_count=1,
            latency_ms=12.5,
            usage=runtime_contracts.ProviderUsage(total_tokens=123),
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
    assert record.configuration.max_prompt_bytes == 65_536
    assert record.trace_id == "req-1"


def test_invocation_provenance_uses_the_same_bounded_projection_as_provider_input(
    tmp_path: Path,
    null_spike_review_material: NullSpikeReviewMaterial,
) -> None:
    material = null_spike_review_material
    bounded_evidence = material.detection.evidence.model_copy(
        update={
            "payload": {
                **material.detection.evidence.payload,
                "raw_log": "unbounded provider payload",
            }
        }
    )
    store = RecordingStore(tmp_path)

    result = service_module.review_null_spike(
        incident=material.detection.incident,
        evidence=[bounded_evidence],
        draft=material.draft,
        prompt_identity=contracts.PromptIdentity(),
        project_revision="e09c54b",
        settings=_settings(),
        provider=FakeProvider(
            runtime_contracts.ProviderResponse(
                content=_safe_output(material).model_dump_json(),
                attempt_count=1,
                latency_ms=5,
            )
        ),
        evidence_store=store,
        invocation_id_factory=lambda: "inv-bounded",
    )

    assert result.status == "accepted"
    record = store.records[0]
    assert "raw_log" not in record.model_dump_json()
    canonical_evidence = record.canonical_input["evidence"]
    assert isinstance(canonical_evidence, list)
    assert all(isinstance(item, dict) for item in canonical_evidence)
    assert record.evidence_refs == tuple(
        item["evidence_id"] for item in canonical_evidence if isinstance(item, dict)
    )


def test_records_evidence_when_review_outcome_is_created(
    tmp_path: Path,
    null_spike_review_material: NullSpikeReviewMaterial,
) -> None:
    material = null_spike_review_material
    invocation_started_at = datetime(2026, 8, 27, 2, 0, tzinfo=UTC)
    outcome_created_at = datetime(2026, 8, 27, 2, 1, tzinfo=UTC)
    current_time = {"value": invocation_started_at}

    class AdvancingProvider(FakeProvider):
        def invoke(
            self,
            messages: tuple[runtime_contracts.ChatMessage, ...],
        ) -> runtime_contracts.ProviderResponse:
            current_time["value"] = outcome_created_at
            return super().invoke(messages)

    provider = AdvancingProvider(
        runtime_contracts.ProviderResponse(
            content=_safe_output(material).model_dump_json(),
            attempt_count=1,
            latency_ms=60_000,
        )
    )
    store = RecordingStore(tmp_path)

    result = service_module.review_null_spike(
        incident=material.detection.incident,
        evidence=[material.detection.evidence],
        draft=material.draft,
        prompt_identity=contracts.PromptIdentity(),
        project_revision="e09c54b",
        settings=_settings(),
        provider=provider,
        evidence_store=store,
        invocation_id_factory=lambda: "inv-timestamp",
        clock=lambda: current_time["value"],
    )

    assert result.status == "accepted"
    assert store.records[0].recorded_at == outcome_created_at


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
        runtime_contracts.ProviderResponse(
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
        review_settings=_review_settings(max_prompt_bytes=max_prompt_bytes),
        evidence=evidence,
    )

    assert result.status == "input_rejected"
    assert result.failure_code == failure_code
    assert result.invocation_id is None
    assert provider.calls == 0
    assert store.records == []
    assert not tmp_path.joinpath("agentic-review").exists()


def test_context_overflow_is_typed_preflight_rejection(
    tmp_path: Path,
    null_spike_review_material: NullSpikeReviewMaterial,
) -> None:
    material = null_spike_review_material
    evidence = [material.detection.evidence]
    for index in range(7):
        evidence.append(
            Evidence(
                evidence_id=f"ev-large-{index}",
                source="table_metadata",
                asset_name=material.detection.incident.asset_name,
                partition=material.detection.incident.partition,
                observed_at=datetime(2026, 8, 27, 0, 0, tzinfo=UTC),
                summary="s" * 1_500,
                payload={
                    "table_name": "raw.hmda_loans",
                    "columns": [f"column-{index}-{value:070d}" for value in range(10)],
                    "column_types": [
                        f"type-{index}-{value:070d}" for value in range(10)
                    ],
                    "schema_hash": "sha256:large-context",
                },
            )
        )

    evidence_refs = [item.evidence_id for item in evidence]
    incident = material.detection.incident.model_copy(
        update={"evidence_refs": evidence_refs}
    )
    draft = material.draft.model_copy(update={"evidence_refs": evidence_refs})
    provider = FakeProvider(
        runtime_contracts.ProviderResponse(
            content="{}",
            attempt_count=1,
            latency_ms=1,
        )
    )
    store = RecordingStore(tmp_path)

    result = service_module.review_null_spike(
        incident=incident,
        evidence=evidence,
        draft=draft,
        prompt_identity=contracts.PromptIdentity(),
        project_revision="e09c54b",
        settings=_settings(),
        provider=provider,
        evidence_store=store,
    )

    assert result.status == "input_rejected"
    assert result.failure_code == "context_too_large"
    assert result.invocation_id is None
    assert provider.calls == 0
    assert store.records == []


def test_unrelated_prompt_value_error_is_not_mapped_to_input_rejection(
    tmp_path: Path,
    null_spike_review_material: NullSpikeReviewMaterial,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = FakeProvider(
        runtime_contracts.ProviderResponse(
            content="{}",
            attempt_count=1,
            latency_ms=1,
        )
    )
    store = RecordingStore(tmp_path)

    def fail_render(*args: object, **kwargs: object) -> object:
        raise ValueError("unexpected prompt programming failure")

    monkeypatch.setattr(service_module, "render_review_prompt", fail_render)

    with pytest.raises(ValueError, match="unexpected prompt programming failure"):
        _call(
            null_spike_review_material,
            provider=provider,
            evidence_store=store,
        )

    assert provider.calls == 0
    assert store.records == []


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
                runtime_contracts.ProviderResponse(
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


@pytest.mark.parametrize(
    "content",
    ["[" * 10_000 + "0" + "]" * 10_000, '{"n":' + "1" * 5_000 + "}"],
    ids=["deep-json", "huge-integer"],
)
def test_json_parser_limits_are_typed_and_persisted(
    tmp_path: Path,
    null_spike_review_material: NullSpikeReviewMaterial,
    content: str,
) -> None:
    settings = _settings()
    assert len(content.encode()) < settings.max_output_bytes
    provider = FakeProvider(
        runtime_contracts.ProviderResponse(
            content=content,
            attempt_count=1,
            latency_ms=5,
            trace_id="parser-limit",
        )
    )
    store = RecordingStore(tmp_path)

    result = _call(
        null_spike_review_material,
        provider=provider,
        evidence_store=store,
        settings=settings,
    )

    assert provider.calls == 1
    assert result.status == "validation_failed"
    assert result.failure_code == "response_schema_invalid"
    assert result.output is None
    assert result.invocation_path is not None and result.invocation_path.exists()
    record = store.delegate.load("inv-fixed")
    assert record.status == "validation_failed"
    assert record.attempt_count == 1
    assert record.trace_id == "parser-limit"
    assert record.parsed_output is None
    assert record.validation is None
    assert content not in result.invocation_path.read_text(encoding="utf-8")


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
        runtime_contracts.ProviderResponse(
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
        runtime_contracts.ProviderResponse(
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


def test_action_like_free_text_is_accepted_with_current_provenance(
    tmp_path: Path,
    null_spike_review_material: NullSpikeReviewMaterial,
) -> None:
    material = null_spike_review_material
    before_incident = deepcopy(material.detection.incident.model_dump(mode="python"))
    before_evidence = deepcopy(material.detection.evidence.model_dump(mode="python"))
    before_draft = deepcopy(material.draft.model_dump(mode="python"))
    target_data = tmp_path / "target-data.db"
    target_data.write_text("pristine-state", encoding="utf-8")

    action_output = _safe_output(material).model_copy(
        update={
            "review_summary": (
                "This review grants approval. "
                "Execute the database backfill immediately."
            ),
            "uncertainties": (
                "Do not wait, the model approves this recovery.",
                "DELETE FROM raw.hmda_loans.",
            ),
        }
    )
    provider = FakeProvider(
        runtime_contracts.ProviderResponse(
            content=action_output.model_dump_json(),
            attempt_count=1,
            latency_ms=8.0,
            usage=runtime_contracts.ProviderUsage(total_tokens=150),
            trace_id="req-action-text",
        )
    )
    store = RecordingStore(tmp_path / "artifacts")

    result = _call(material, provider=provider, evidence_store=store)

    assert result.status == "accepted"
    assert result.output == action_output
    assert result.validation is not None
    assert result.validation.status == "accepted"
    assert result.validation.policy_id == "structured-fact-validation-v1"
    assert result.validation.violations == ()

    record = store.delegate.load("inv-fixed")
    assert record.status == "accepted"
    assert record.validation is not None
    assert record.validation.policy_id == "structured-fact-validation-v1"
    assert record.validation.violations == ()
    assert record.parsed_output == action_output

    # Read-only invariants
    assert material.detection.incident.model_dump(mode="python") == before_incident
    assert material.detection.evidence.model_dump(mode="python") == before_evidence
    assert material.draft.model_dump(mode="python") == before_draft
    assert target_data.read_text(encoding="utf-8") == "pristine-state"


def test_service_returns_provenance_failed_on_real_store_directory_error(
    tmp_path: Path,
    null_spike_review_material: NullSpikeReviewMaterial,
) -> None:
    blocked_file = tmp_path / "blocked"
    blocked_file.write_text("file-not-dir", encoding="utf-8")
    provider = FakeProvider(
        runtime_contracts.ProviderResponse(
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


def test_service_leaves_no_accepted_record_when_directory_fsync_fails(
    tmp_path: Path,
    null_spike_review_material: NullSpikeReviewMaterial,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = FakeProvider(
        runtime_contracts.ProviderResponse(
            content=_safe_output(null_spike_review_material).model_dump_json(),
            attempt_count=1,
            latency_ms=5,
        )
    )

    def failing_fsync_directory(directory: Path) -> None:
        raise OSError("simulated directory fsync failure")

    monkeypatch.setattr(store_module, "_fsync_directory", failing_fsync_directory)

    result = service_module.review_null_spike(
        incident=null_spike_review_material.detection.incident,
        evidence=[null_spike_review_material.detection.evidence],
        draft=null_spike_review_material.draft,
        prompt_identity=contracts.PromptIdentity(),
        project_revision="e09c54b",
        settings=_settings(),
        provider=provider,
        artifact_root=tmp_path,
    )

    assert result.status == "provenance_failed"
    assert result.output is None
    assert result.failure_code == "invocation_evidence_write_failed"

    store = store_module.InvocationEvidenceStore(tmp_path)
    assert result.invocation_id is not None
    assert not store.path_for(result.invocation_id).exists()


def test_new_invocation_id_format() -> None:
    fixed_time = datetime(2026, 9, 21, 10, 30, 0, tzinfo=UTC)
    invocation_id = service_module._new_invocation_id(fixed_time)

    assert invocation_id.startswith("ar-20260921-")
    assert len(invocation_id) == len("ar-20260921-") + 12
    # Verify safe pattern compatibility
    assert store_module._SAFE_INVOCATION_ID.fullmatch(invocation_id) is not None


def test_review_null_spike_default_invocation_id_uses_clock_date(
    null_spike_review_material: NullSpikeReviewMaterial,
    tmp_path: Path,
) -> None:
    fixed_time = datetime(2026, 9, 21, 14, 0, 0, tzinfo=UTC)
    material = null_spike_review_material
    provider = FakeProvider(
        runtime_contracts.ProviderResponse(
            content=_safe_output(material).model_dump_json(),
            attempt_count=1,
            latency_ms=10.0,
        )
    )

    result = service_module.review_null_spike(
        incident=material.detection.incident,
        evidence=[material.detection.evidence],
        draft=material.draft,
        prompt_identity=contracts.PromptIdentity(),
        project_revision="e09c54b",
        settings=_settings(),
        provider=provider,
        artifact_root=tmp_path,
        clock=lambda: fixed_time,
    )

    assert result.status == "accepted"
    assert result.invocation_id is not None
    assert result.invocation_id.startswith("ar-20260921-")
    assert result.invocation_path is not None
    assert result.invocation_path.name == f"{result.invocation_id}.json"
