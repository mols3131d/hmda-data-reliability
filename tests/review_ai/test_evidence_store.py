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
from hmda_reliability.review_ai import store as store_module
from hmda_reliability.review_ai.prompt import legacy as prompt_module
from hmda_reliability.review_ai.settings import ReviewAISettings
from hmda_reliability.runtime_ai import contracts as runtime_contracts
from hmda_reliability.runtime_ai.settings import RuntimeAISettings

from .conftest import NullSpikeReviewMaterial

pytestmark = pytest.mark.component


def test_historical_evidence_without_response_diagnostics_remains_readable(
    null_spike_review_material: NullSpikeReviewMaterial,
) -> None:
    payload = _record(null_spike_review_material).model_dump(mode="json")
    payload.pop("response_metadata")
    payload.pop("response_diagnostics")

    historical = evidence_module.AgenticInvocationEvidence.model_validate(payload)

    assert historical.prompt_identity.version == "v1"
    assert historical.response_metadata is None
    assert historical.response_diagnostics is None


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
            violations=["fabricated_evidence"],
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


@pytest.mark.parametrize(
    ("status", "legacy_violations"),
    [
        ("accepted", ()),
        ("validation_failed", ("forbidden_action",)),
    ],
)
def test_store_loads_legacy_validation_provenance(
    tmp_path: Path,
    null_spike_review_material: NullSpikeReviewMaterial,
    status: str,
    legacy_violations: tuple[str, ...],
) -> None:
    record = _record(null_spike_review_material, status=status)
    payload = record.model_dump(mode="json")
    validation = payload["validation"]
    assert isinstance(validation, dict)
    validation["policy_id"] = "forbidden-action-policy-v1"
    validation["violations"] = list(legacy_violations)
    store = store_module.InvocationEvidenceStore(tmp_path)
    path = store.path_for(record.invocation_id)
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(payload), encoding="utf-8")

    loaded = store.load(record.invocation_id)

    assert loaded.validation is not None
    assert loaded.validation.policy_id == "forbidden-action-policy-v1"
    assert loaded.validation.violations == legacy_violations


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


@pytest.mark.parametrize("content", ["", " \n ", '{"응답":"잘린 JSON 😀"'])
def test_response_store_preserves_exact_utf8_body_separately(
    tmp_path: Path, content: str
) -> None:
    store = store_module.InvocationResponseStore(tmp_path)

    path = store.write("inv-response", content, max_response_bytes=1024)

    assert path == tmp_path / "agentic-review" / "responses" / "inv-response.txt"
    assert path == store.path_for("inv-response")
    assert path.read_bytes() == content.encode("utf-8")
    assert path.stat().st_mode & 0o077 == 0
    assert not (tmp_path / "agentic-review" / "invocations").exists()


def test_response_store_rejects_duplicate_identity_without_replacing_body(
    tmp_path: Path,
) -> None:
    store = store_module.InvocationResponseStore(tmp_path)
    path = store.write("inv-response", "first response", max_response_bytes=1024)

    with pytest.raises(store_module.InvocationEvidenceExistsError):
        store.write("inv-response", "replacement response", max_response_bytes=1024)

    assert path.read_text(encoding="utf-8") == "first response"


def test_response_store_does_not_attach_body_to_an_existing_invocation(
    tmp_path: Path,
    null_spike_review_material: NullSpikeReviewMaterial,
) -> None:
    evidence_store = store_module.InvocationEvidenceStore(tmp_path)
    record = _record(null_spike_review_material)
    evidence_path = evidence_store.write(record, max_record_bytes=131_072)
    before = evidence_path.read_bytes()
    response_store = store_module.InvocationResponseStore(tmp_path)

    with pytest.raises(store_module.InvocationEvidenceExistsError):
        response_store.write(
            record.invocation_id, "unrelated response", max_response_bytes=1024
        )

    assert evidence_path.read_bytes() == before
    assert not response_store.path_for(record.invocation_id).exists()


def test_response_store_counts_utf8_bytes_and_accepts_exact_limit(
    tmp_path: Path,
) -> None:
    store = store_module.InvocationResponseStore(tmp_path)
    content = "한😀"

    path = store.write("inv-exact", content, max_response_bytes=7)
    with pytest.raises(store_module.InvocationEvidenceSizeError):
        store.write("inv-oversized", content, max_response_bytes=6)

    assert path.read_bytes() == b"\xed\x95\x9c\xf0\x9f\x98\x80"
    assert not store.path_for("inv-oversized").exists()


@pytest.mark.parametrize("invocation_id", ["../escape", "/absolute", "inv/response"])
def test_response_store_rejects_unsafe_identity(
    tmp_path: Path, invocation_id: str
) -> None:
    store = store_module.InvocationResponseStore(tmp_path)

    with pytest.raises(ValueError, match="unsafe invocation identity"):
        store.write(invocation_id, "body", max_response_bytes=1024)

    assert not (tmp_path / "agentic-review").exists()


def test_response_store_rolls_back_body_when_directory_fsync_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = store_module.InvocationResponseStore(tmp_path)

    def failing_fsync_directory(directory: Path) -> None:
        raise OSError("simulated directory fsync failure")

    monkeypatch.setattr(store_module, "_fsync_directory", failing_fsync_directory)

    with pytest.raises(store_module.InvocationEvidenceWriteError):
        store.write("inv-response", "body", max_response_bytes=1024)

    assert not store.path_for("inv-response").exists()
    assert list(store.path_for("inv-response").parent.iterdir()) == []
