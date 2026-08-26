"""Opt-in live harness configuration and network-isolation tests."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import cast

import pytest

from hmda_reliability.reliability import Evidence, Incident, RemediationDraft
from hmda_reliability.reliability.agentic_review import (
    AgenticReviewInput,
    AgenticReviewOutput,
    AgenticReviewResult,
    AgenticReviewSettings,
    AgenticReviewValidation,
    PromptIdentity,
)
from scripts import run_agentic_review_live as live_module

pytestmark = pytest.mark.unit


def _live_environment(tmp_path: Path) -> dict[str, str]:
    return {
        "HMDA_AGENTIC_REVIEW_LIVE": "true",
        "HMDA_AGENTIC_REVIEW_BASE_URL": "http://localhost:11434/v1",
        "HMDA_AGENTIC_REVIEW_API_KEY": "live-test-secret",
        "HMDA_AGENTIC_REVIEW_MODEL": "local-model",
        "HMDA_AGENTIC_REVIEW_PROJECT_REVISION": "revision-123",
        "HMDA_AGENTIC_REVIEW_TIMEOUT_SECONDS": "15",
        "HMDA_AGENTIC_REVIEW_MAX_RETRIES": "0",
        "HMDA_AGENTIC_REVIEW_MAX_OUTPUT_TOKENS": "512",
        "HMDA_AGENTIC_REVIEW_MAX_PROMPT_BYTES": "32768",
        "HMDA_AGENTIC_REVIEW_MAX_OUTPUT_BYTES": "16384",
        "HMDA_RELIABILITY_ARTIFACTS_DIR": str(tmp_path / "artifacts"),
    }


def test_default_harness_is_disabled_and_never_calls_review(
    capsys: pytest.CaptureFixture[str],
) -> None:
    calls: list[dict[str, object]] = []

    def fail_if_called(**kwargs: object) -> AgenticReviewResult:
        calls.append(kwargs)
        raise AssertionError("live review must remain disabled")

    exit_code = live_module.main(env={}, reviewer=fail_if_called)

    assert exit_code == 0
    assert calls == []
    assert "disabled" in capsys.readouterr().out.lower()


def test_opt_in_requires_all_provider_identity_and_revision_values(
    capsys: pytest.CaptureFixture[str],
) -> None:
    calls: list[dict[str, object]] = []

    def fail_if_called(**kwargs: object) -> AgenticReviewResult:
        calls.append(kwargs)
        raise AssertionError("incomplete live configuration must not call provider")

    exit_code = live_module.main(
        env={"HMDA_AGENTIC_REVIEW_LIVE": "true"},
        reviewer=fail_if_called,
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert calls == []
    assert "HMDA_AGENTIC_REVIEW_BASE_URL" in captured.err
    assert "HMDA_AGENTIC_REVIEW_MODEL" in captured.err
    assert "HMDA_AGENTIC_REVIEW_PROJECT_REVISION" in captured.err


def test_live_harness_passes_explicit_settings_and_deterministic_material(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    calls: list[dict[str, object]] = []

    def capture_review(**kwargs: object) -> AgenticReviewResult:
        calls.append(kwargs)
        return AgenticReviewResult(
            status="input_rejected",
            failure_code="simulated_typed_result",
        )

    exit_code = live_module.main(
        env=_live_environment(tmp_path),
        reviewer=capture_review,
    )

    assert exit_code == 1
    assert len(calls) == 1
    call = calls[0]
    settings = cast(AgenticReviewSettings, call["settings"])
    incident = cast(Incident, call["incident"])
    draft = cast(RemediationDraft, call["draft"])
    evidence = cast(Sequence[Evidence], call["evidence"])
    assert str(settings.base_url) == "http://localhost:11434/v1"
    assert settings.api_key.get_secret_value() == "live-test-secret"
    assert settings.model == "local-model"
    assert settings.timeout_seconds == 15
    assert settings.max_retries == 0
    assert settings.max_output_tokens == 512
    assert settings.max_prompt_bytes == 32_768
    assert settings.max_output_bytes == 16_384
    assert call["project_revision"] == "revision-123"
    assert call["artifact_root"] == tmp_path / "artifacts"
    assert incident.incident_type == "null_spike"
    assert draft.incident_type == "null_spike"
    assert len(evidence) == 1
    assert evidence[0].payload["rule"] == "null_spike"
    output = capsys.readouterr().out
    assert '"status": "input_rejected"' in output
    assert "live-test-secret" not in output


def test_invalid_numeric_live_configuration_fails_before_review(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    environment = _live_environment(tmp_path)
    environment["HMDA_AGENTIC_REVIEW_TIMEOUT_SECONDS"] = "not-a-number"
    calls: list[dict[str, object]] = []

    def fail_if_called(**kwargs: object) -> AgenticReviewResult:
        calls.append(kwargs)
        raise AssertionError("invalid configuration must not call provider")

    exit_code = live_module.main(env=environment, reviewer=fail_if_called)

    assert exit_code == 2
    assert calls == []
    assert "configuration" in capsys.readouterr().err.lower()


def test_accepted_live_result_requires_verified_invocation_evidence(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def accepted_without_evidence(**kwargs: object) -> AgenticReviewResult:
        incident = cast(Incident, kwargs["incident"])
        evidence = cast(Sequence[Evidence], kwargs["evidence"])
        draft = cast(RemediationDraft, kwargs["draft"])
        review_input = AgenticReviewInput(
            incident=incident,
            evidence=evidence,
            draft=draft,
            prompt_identity=cast(PromptIdentity, kwargs["prompt_identity"]),
            project_revision=cast(str, kwargs["project_revision"]),
        )
        output = AgenticReviewOutput(
            incident_id=incident.incident_id,
            incident_type="null_spike",
            target_column=review_input.target_column,
            deterministic_facts=review_input.deterministic_facts,
            review_summary="The deterministic evidence is consistent.",
            evidence_used=[evidence[0].evidence_id],
            findings=[],
            uncertainties=[],
            advisory_recommendation="support",
        )
        return AgenticReviewResult(
            status="accepted",
            output=output,
            validation=AgenticReviewValidation(status="accepted", violations=[]),
            invocation_id="inv-missing",
            invocation_path=tmp_path / "missing.json",
        )

    exit_code = live_module.main(
        env=_live_environment(tmp_path),
        reviewer=accepted_without_evidence,
    )

    captured = capsys.readouterr()
    assert exit_code == 3
    assert "provenance validation failed" in captured.err.lower()
