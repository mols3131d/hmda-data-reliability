"""Durable, create-only logical invocation provenance tests."""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from hmda_reliability.review_ai import contracts
from hmda_reliability.review_ai import evidence as evidence_module
from hmda_reliability.review_ai import prompt as prompt_module
from hmda_reliability.review_ai import store as store_module
from hmda_reliability.review_ai.settings import ReviewAISettings
from hmda_reliability.runtime_ai import contracts as runtime_contracts
from hmda_reliability.runtime_ai.settings import RuntimeAISettings

from .conftest import NullSpikeReviewMaterial

pytestmark = pytest.mark.component


def _review_input(material: NullSpikeReviewMaterial) -> contracts.AgenticReviewInput:
    return contracts.AgenticReviewInput(
        incident=material.detection.incident,
        evidence=[material.detection.evidence],
        draft=material.draft,
        prompt_identity=contracts.PromptIdentity(),
        project_revision="e09c54b",
    )


def _output(
    review_input: contracts.AgenticReviewInput,
) -> contracts.AgenticReviewOutput:
    evidence_id = review_input.evidence[0].evidence_id
    return contracts.AgenticReviewOutput(
        incident_id=review_input.incident.incident_id,
        incident_type="null_spike",
        target_column=review_input.target_column,
        deterministic_facts=review_input.deterministic_facts,
        review_summary="Canonical facts와 draft가 일치한다.",
        evidence_used=[evidence_id],
        findings=[],
        uncertainties=["Root cause는 human review 대상이다."],
        advisory_recommendation="needs_human_review",
    )


def _settings() -> RuntimeAISettings:
    return RuntimeAISettings(
        base_url="http://localhost:11434/v1",
        api_key="local-test-key",
        model="test-model",
    )


def _sanitized_configuration() -> dict[str, str | float | int]:
    configuration = _settings().sanitized_configuration()
    configuration.update(ReviewAISettings().sanitized_configuration())
    return configuration


def _record(
    material: NullSpikeReviewMaterial,
    *,
    status: str = "accepted",
    invocation_id: str = "inv-1",
) -> evidence_module.AgenticInvocationEvidence:
    review_input = _review_input(material)
    rendered = prompt_module.render_review_prompt(
        review_input,
        max_prompt_bytes=65_536,
    )
    output = _output(review_input)
    parsed_output = output if status in {"accepted", "validation_failed"} else None
    validation = None
    failure_code = None
    if status == "accepted":
        validation = contracts.AgenticReviewValidation(
            status="accepted",
            violations=[],
        )
    elif status == "validation_failed":
        validation = contracts.AgenticReviewValidation(
            status="rejected",
            violations=["forbidden_action"],
        )
        failure_code = "deterministic_guard_failed"
    elif status == "unavailable":
        failure_code = "provider_connection_error"

    return evidence_module.AgenticInvocationEvidence(
        invocation_id=invocation_id,
        recorded_at=datetime(2026, 8, 27, 1, 2, 3, tzinfo=UTC),
        status=status,
        configuration=evidence_module.SanitizedAgenticReviewConfiguration.model_validate(
            _sanitized_configuration()
        ),
        prompt_identity=review_input.prompt_identity,
        prompt_digest=rendered.prompt_digest,
        project_revision=review_input.project_revision,
        incident_id=review_input.incident.incident_id,
        evidence_refs=[item.evidence_id for item in review_input.evidence],
        canonical_input=rendered.canonical_input,
        parsed_output=parsed_output,
        validation=validation,
        failure_code=failure_code,
        latency_ms=125.5,
        attempt_count=2 if status == "unavailable" else 1,
        usage=runtime_contracts.ProviderUsage(
            prompt_tokens=100,
            completion_tokens=25,
            total_tokens=125,
        ),
        trace_id="req-1",
    )


@pytest.mark.parametrize("status", ["accepted", "validation_failed", "unavailable"])
def test_store_round_trips_logical_invocation_records(
    tmp_path: Path,
    null_spike_review_material: NullSpikeReviewMaterial,
    status: str,
) -> None:
    record = _record(null_spike_review_material, status=status)
    store = store_module.InvocationEvidenceStore(tmp_path)

    path = store.write(record, max_record_bytes=131_072)
    loaded = store.load(record.invocation_id)

    assert path == tmp_path / "agentic-review" / "invocations" / "inv-1.json"
    assert loaded == record
    assert path.stat().st_mode & 0o077 == 0


def test_stored_record_replays_digest_without_raw_prompt_or_credentials(
    tmp_path: Path,
    null_spike_review_material: NullSpikeReviewMaterial,
) -> None:
    record = _record(null_spike_review_material)
    store = store_module.InvocationEvidenceStore(tmp_path)

    path = store.write(record, max_record_bytes=131_072)
    loaded = store.load(record.invocation_id)
    replay = prompt_module.render_canonical_input(
        loaded.canonical_input,
        loaded.prompt_identity,
        max_prompt_bytes=65_536,
    )
    raw_record = path.read_text(encoding="utf-8")
    payload = json.loads(raw_record)

    assert replay.prompt_digest == loaded.prompt_digest
    assert payload["canonical_input"] == loaded.canonical_input
    assert payload["configuration"]["model"] == "test-model"
    assert payload["configuration"]["max_prompt_bytes"] == 65_536
    assert "api_key" not in raw_record
    assert "local-test-key" not in raw_record
    assert "raw_prompt" not in raw_record
    assert "raw_provider" not in raw_record
    assert "provider exception" not in raw_record


def test_store_rejects_duplicate_identity_and_preserves_first_record(
    tmp_path: Path,
    null_spike_review_material: NullSpikeReviewMaterial,
) -> None:
    first = _record(null_spike_review_material, status="accepted")
    second = _record(
        null_spike_review_material,
        status="validation_failed",
        invocation_id=first.invocation_id,
    )
    store = store_module.InvocationEvidenceStore(tmp_path)
    store.write(first, max_record_bytes=131_072)

    with pytest.raises(store_module.InvocationEvidenceExistsError):
        store.write(second, max_record_bytes=131_072)

    assert store.load(first.invocation_id) == first


def test_concurrent_duplicate_create_has_exactly_one_winner(
    tmp_path: Path,
    null_spike_review_material: NullSpikeReviewMaterial,
) -> None:
    record = _record(null_spike_review_material)
    store = store_module.InvocationEvidenceStore(tmp_path)

    def write_once() -> str:
        try:
            store.write(record, max_record_bytes=131_072)
        except store_module.InvocationEvidenceExistsError:
            return "collision"
        return "created"

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: write_once(), range(2)))

    assert sorted(results) == ["collision", "created"]
    assert store.load(record.invocation_id) == record


def test_store_rejects_unsafe_identity_and_oversized_record(
    tmp_path: Path,
    null_spike_review_material: NullSpikeReviewMaterial,
) -> None:
    with pytest.raises(ValidationError):
        _record(null_spike_review_material, invocation_id="../escape")

    record = _record(null_spike_review_material)
    store = store_module.InvocationEvidenceStore(tmp_path)
    with pytest.raises(store_module.InvocationEvidenceSizeError):
        store.write(record, max_record_bytes=32)
    assert not store.path_for(record.invocation_id).exists()


def test_store_write_normalizes_directory_creation_failure(
    tmp_path: Path,
    null_spike_review_material: NullSpikeReviewMaterial,
) -> None:
    blocked_root = tmp_path / "blocked"
    blocked_root.write_text("not-a-directory", encoding="utf-8")
    store = store_module.InvocationEvidenceStore(blocked_root)
    record = _record(null_spike_review_material)

    with pytest.raises(store_module.InvocationEvidenceWriteError):
        store.write(record, max_record_bytes=131_072)


def test_store_write_handles_cleanup_error_gracefully(
    tmp_path: Path,
    null_spike_review_material: NullSpikeReviewMaterial,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = store_module.InvocationEvidenceStore(tmp_path)
    record = _record(null_spike_review_material)

    original_unlink = Path.unlink

    def failing_unlink(self: Path, missing_ok: bool = False) -> None:
        if self.name.endswith(".tmp"):
            raise OSError("simulated unlink failure")
        original_unlink(self, missing_ok=missing_ok)

    monkeypatch.setattr(Path, "unlink", failing_unlink)

    path = store.write(record, max_record_bytes=131_072)
    assert path.exists()
    assert store.load(record.invocation_id) == record


def test_store_write_rolls_back_final_link_on_directory_fsync_failure(
    tmp_path: Path,
    null_spike_review_material: NullSpikeReviewMaterial,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = store_module.InvocationEvidenceStore(tmp_path)
    record = _record(null_spike_review_material)

    def failing_fsync_directory(directory: Path) -> None:
        raise OSError("simulated directory fsync failure")

    monkeypatch.setattr(store_module, "_fsync_directory", failing_fsync_directory)

    with pytest.raises(store_module.InvocationEvidenceWriteError):
        store.write(record, max_record_bytes=131_072)

    final_path = store.path_for(record.invocation_id)
    assert not final_path.exists()
