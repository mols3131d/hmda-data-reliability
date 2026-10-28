"""Opt-in live harness configuration and network-isolation tests."""

from __future__ import annotations

import json
import subprocess
from collections.abc import Sequence
from pathlib import Path
from typing import Literal, cast

import pytest

from hmda_reliability.reliability import Evidence, Incident, RemediationDraft
from hmda_reliability.review_ai import (
    AgenticReviewInput,
    AgenticReviewOutput,
    AgenticReviewResult,
    PromptIdentity,
)
from hmda_reliability.review_ai.contracts import AgenticReviewValidation
from hmda_reliability.review_ai.settings import ReviewAISettings
from hmda_reliability.review_ai.staged.evidence import StagedReviewResult
from hmda_reliability.review_ai.staged.service import review_null_spike_staged
from hmda_reliability.runtime_ai import RuntimeAISettings
from hmda_reliability.runtime_ai.contracts import ChatMessage, ProviderResponse
from scripts import run_agentic_review_live as live_module

pytestmark = pytest.mark.unit


def _live_environment(tmp_path: Path) -> dict[str, str]:
    return {
        "HMDA_AGENTIC_REVIEW_LIVE": "true",
        "HMDA_AGENTIC_REVIEW_MODE": "structured",
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


class StagedTextProvider:
    def __init__(self) -> None:
        self.text = (
            "PRIVATE_STAGED_ANSWER: 원인은 제공된 근거만으로 확정할 수 없습니다.\n"
        )
        self.messages: list[tuple[ChatMessage, ...]] = []

    def invoke(
        self,
        messages: tuple[ChatMessage, ...],
        *,
        output_format: Literal["json_object", "text"] = "json_object",
    ) -> ProviderResponse:
        assert output_format == "text"
        self.messages.append(messages)
        return ProviderResponse(content=self.text, attempt_count=1, latency_ms=1)


def _run_staged_review(
    kwargs: dict[str, object], provider: StagedTextProvider
) -> StagedReviewResult:
    return review_null_spike_staged(
        incident=cast(Incident, kwargs["incident"]),
        evidence=cast(Sequence[Evidence], kwargs["evidence"]),
        draft=cast(RemediationDraft, kwargs["draft"]),
        project_revision=cast(str, kwargs["project_revision"]),
        settings=cast(RuntimeAISettings, kwargs["settings"]),
        review_settings=cast(ReviewAISettings, kwargs["review_settings"]),
        artifact_root=cast(Path, kwargs["artifact_root"]),
        provider=provider,
        workflow_id_factory=lambda: "workflow-cli-test",
    )


def test_default_live_mode_is_staged_and_ignores_structured_prompt_version(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    environment = _live_environment(tmp_path)
    environment.pop("HMDA_AGENTIC_REVIEW_MODE")
    environment["HMDA_AGENTIC_REVIEW_PROMPT_VERSION"] = "unsupported"
    calls: list[dict[str, object]] = []

    def staged_review(**kwargs: object) -> StagedReviewResult:
        calls.append(kwargs)
        return StagedReviewResult(
            status="input_rejected", failure_code="test_preflight"
        )

    def unexpected_structured_review(**kwargs: object) -> AgenticReviewResult:
        pytest.fail("mode omission must use the staged reviewer")

    exit_code = live_module.main(
        env=environment,
        reviewer=unexpected_structured_review,
        staged_reviewer=staged_review,
    )

    assert exit_code == 1
    assert len(calls) == 1
    assert "prompt_identity" not in calls[0]
    assert calls[0]["project_revision"] == "revision-123"
    assert calls[0]["artifact_root"] == tmp_path / "artifacts"
    assert cast(RuntimeAISettings, calls[0]["settings"]).model == "local-model"
    assert (
        cast(ReviewAISettings, calls[0]["review_settings"]).max_prompt_bytes == 32_768
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "input_rejected"
    assert "output" not in payload


def test_disabled_staged_live_mode_never_calls_the_reviewer(
    capsys: pytest.CaptureFixture[str],
) -> None:
    def unexpected_review(**kwargs: object) -> StagedReviewResult:
        pytest.fail("disabled live mode must not call the staged reviewer")

    exit_code = live_module.main(env={}, staged_reviewer=unexpected_review)

    assert exit_code == 0
    assert "disabled" in capsys.readouterr().out.lower()


def test_invalid_live_mode_is_rejected_before_review(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    environment = _live_environment(tmp_path)
    environment["HMDA_AGENTIC_REVIEW_MODE"] = "unsupported"

    def unexpected_structured_review(**kwargs: object) -> AgenticReviewResult:
        pytest.fail("invalid mode must not call the structured reviewer")

    def unexpected_staged_review(**kwargs: object) -> StagedReviewResult:
        pytest.fail("invalid mode must not call the staged reviewer")

    exit_code = live_module.main(
        env=environment,
        reviewer=unexpected_structured_review,
        staged_reviewer=unexpected_staged_review,
    )

    assert exit_code == 2
    assert "mode" in capsys.readouterr().err.lower()


def test_invalid_staged_configuration_never_calls_the_reviewer(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    environment = _live_environment(tmp_path)
    environment["HMDA_AGENTIC_REVIEW_MODE"] = "staged"
    environment["HMDA_AGENTIC_REVIEW_TIMEOUT_SECONDS"] = "not-a-number"

    def unexpected_review(**kwargs: object) -> StagedReviewResult:
        pytest.fail("invalid settings must not call the staged reviewer")

    exit_code = live_module.main(env=environment, staged_reviewer=unexpected_review)

    assert exit_code == 2
    assert "configuration" in capsys.readouterr().err.lower()


@pytest.mark.parametrize("remove_manifest", [False, True])
def test_staged_live_verifies_the_workflow_and_keeps_answers_off_the_console(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    remove_manifest: bool,
) -> None:
    environment = _live_environment(tmp_path)
    environment["HMDA_AGENTIC_REVIEW_MODE"] = "staged"
    provider = StagedTextProvider()

    def staged_review(**kwargs: object) -> StagedReviewResult:
        result = _run_staged_review(kwargs, provider)
        assert result.workflow_path is not None
        if remove_manifest:
            result.workflow_path.unlink()
        return result

    exit_code = live_module.main(env=environment, staged_reviewer=staged_review)

    captured = capsys.readouterr()
    assert exit_code == (1 if remove_manifest else 0)
    assert provider.text not in captured.out + captured.err
    assert "PRIVATE_STAGED_ANSWER" not in captured.out + captured.err
    assert "live-test-secret" not in captured.out + captured.err
    payload = json.loads(captured.out)
    assert "output" not in payload
    assert len(provider.messages) == 3
    assert any(message.role == "assistant" for message in provider.messages[-1])
    output = json.loads(Path(payload["output_path"]).read_text(encoding="utf-8"))
    assert [stage["text"] for stage in output["stages"]] == [provider.text] * 3
    if remove_manifest:
        assert "provenance validation failed" in captured.err.lower()
    else:
        assert payload["status"] == "completed"


def test_staged_live_explicitly_skips_langfuse_projection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    environment = _live_environment(tmp_path)
    environment["HMDA_AGENTIC_REVIEW_MODE"] = "staged"
    environment["HMDA_LANGFUSE_EXPORT"] = "true"

    def staged_review(**kwargs: object) -> StagedReviewResult:
        return StagedReviewResult(
            status="input_rejected", failure_code="test_preflight"
        )

    def unexpected_export(*args: object, **kwargs: object) -> str:
        pytest.fail("staged text must not use the structured projection")

    monkeypatch.setattr(live_module, "_export_live_projection", unexpected_export)

    exit_code = live_module.main(env=environment, staged_reviewer=staged_review)

    assert exit_code == 1
    assert "skipped_staged_mode" in capsys.readouterr().err


@pytest.mark.parametrize(
    "tamper",
    [
        "status",
        "revision",
        "configuration",
        "input",
        "input_scalar_type",
        "output_path",
        "output_digest",
        "output",
    ],
)
def test_staged_live_rejects_mismatched_manifest_or_output(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    tamper: str,
) -> None:
    environment = _live_environment(tmp_path)
    environment["HMDA_AGENTIC_REVIEW_MODE"] = "staged"
    provider = StagedTextProvider()

    def staged_review(**kwargs: object) -> StagedReviewResult:
        result = _run_staged_review(kwargs, provider)
        assert result.workflow_path is not None
        assert result.output_path is not None
        manifest = json.loads(result.workflow_path.read_text(encoding="utf-8"))
        if tamper == "status":
            manifest["status"] = "unavailable"
        elif tamper == "revision":
            manifest["project_revision"] = "different-revision"
        elif tamper == "configuration":
            manifest["configuration"]["model"] = "different-model"
        elif tamper == "input":
            manifest["canonical_input"]["incident"]["incident_id"] = (
                "different-incident"
            )
        elif tamper == "output_path":
            manifest["output_path"] = str(tmp_path / "different-output.json")
        elif tamper == "input_scalar_type":
            draft = manifest["canonical_input"]["draft"]
            draft["requires_approval"] = int(draft["requires_approval"])
        elif tamper == "output_digest":
            manifest["output_digest"] = "sha256:" + "0" * 64
        else:
            output = json.loads(result.output_path.read_text(encoding="utf-8"))
            output["stages"][0]["text"] = "변조된 답변"
            result.output_path.write_text(json.dumps(output), encoding="utf-8")
        result.workflow_path.write_text(json.dumps(manifest), encoding="utf-8")
        return result

    exit_code = live_module.main(env=environment, staged_reviewer=staged_review)

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "provenance validation failed" in captured.err.lower()
    assert "PRIVATE_STAGED_ANSWER" not in captured.out + captured.err


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


def test_opt_in_requires_provider_identity_values(
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
    settings = cast(RuntimeAISettings, call["settings"])
    review_settings = cast(ReviewAISettings, call["review_settings"])
    incident = cast(Incident, call["incident"])
    draft = cast(RemediationDraft, call["draft"])
    evidence = cast(Sequence[Evidence], call["evidence"])
    assert str(settings.base_url) == "http://localhost:11434/v1"
    assert settings.api_key.get_secret_value() == "live-test-secret"
    assert settings.model == "local-model"
    assert settings.timeout_seconds == 15
    assert settings.max_retries == 0
    assert settings.max_output_tokens == 512
    assert review_settings.max_prompt_bytes == 32_768
    assert settings.max_output_bytes == 16_384
    assert call["project_revision"] == "revision-123"
    assert call["prompt_identity"] == PromptIdentity(version="v2")
    assert call["artifact_root"] == tmp_path / "artifacts"
    assert incident.incident_type == "null_spike"
    assert draft.incident_type == "null_spike"
    assert len(evidence) == 1
    assert evidence[0].payload["rule"] == "null_spike"
    output = capsys.readouterr().out
    assert '"status": "input_rejected"' in output
    assert "live-test-secret" not in output


@pytest.mark.parametrize("version", ["v1", "v2", "v3", "unsupported"])
def test_live_prompt_version_is_explicit_and_invalid_version_never_calls_provider(
    tmp_path: Path,
    version: str,
) -> None:
    environment = _live_environment(tmp_path)
    environment["HMDA_AGENTIC_REVIEW_PROMPT_VERSION"] = version
    calls: list[dict[str, object]] = []

    def capture_review(**kwargs: object) -> AgenticReviewResult:
        calls.append(kwargs)
        return AgenticReviewResult(
            status="input_rejected", failure_code="test_preflight"
        )

    exit_code = live_module.main(env=environment, reviewer=capture_review)

    if version == "unsupported":
        assert exit_code == 2 and calls == []
    else:
        assert exit_code == 1 and len(calls) == 1
        assert calls[0]["prompt_identity"] == PromptIdentity.model_validate(
            {"version": version}
        )


@pytest.mark.parametrize("configured_revision", [None, "", "auto"])
def test_live_harness_auto_resolves_project_revision(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    configured_revision: str | None,
) -> None:
    environment = _live_environment(tmp_path)
    if configured_revision is None:
        environment.pop("HMDA_AGENTIC_REVIEW_PROJECT_REVISION")
    else:
        environment["HMDA_AGENTIC_REVIEW_PROJECT_REVISION"] = configured_revision
    calls: list[dict[str, object]] = []

    monkeypatch.setattr(live_module, "_current_git_revision", lambda: "git-head-123")

    def capture_review(**kwargs: object) -> AgenticReviewResult:
        calls.append(kwargs)
        return AgenticReviewResult(
            status="input_rejected",
            failure_code="simulated_typed_result",
        )

    exit_code = live_module.main(env=environment, reviewer=capture_review)

    assert exit_code == 1
    assert len(calls) == 1
    assert calls[0]["project_revision"] == "git-head-123"


def test_auto_project_revision_uses_clean_git_head(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    results = iter(
        [
            subprocess.CompletedProcess([], 0, stdout="git-head-123\n", stderr=""),
            subprocess.CompletedProcess([], 0, stdout="", stderr=""),
        ]
    )
    monkeypatch.setattr(
        live_module.subprocess,
        "run",
        lambda *args, **kwargs: next(results),
    )

    assert live_module._current_git_revision() == "git-head-123"


def test_auto_project_revision_rejects_dirty_tracked_worktree(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    results = iter(
        [
            subprocess.CompletedProcess([], 0, stdout="git-head-123\n", stderr=""),
            subprocess.CompletedProcess(
                [],
                0,
                stdout=" M src/hmda_reliability/review_ai/prompt.py\n",
                stderr="",
            ),
        ]
    )
    monkeypatch.setattr(
        live_module.subprocess,
        "run",
        lambda *args, **kwargs: next(results),
    )

    with pytest.raises(ValueError, match="clean tracked worktree"):
        live_module._current_git_revision()


def test_auto_project_revision_failure_stops_before_review(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    environment = _live_environment(tmp_path)
    environment["HMDA_AGENTIC_REVIEW_PROJECT_REVISION"] = "auto"
    calls: list[dict[str, object]] = []

    def fail_revision() -> str:
        raise ValueError("git unavailable")

    def fail_if_called(**kwargs: object) -> AgenticReviewResult:
        calls.append(kwargs)
        raise AssertionError("unresolved revision must not call provider")

    monkeypatch.setattr(live_module, "_current_git_revision", fail_revision)

    exit_code = live_module.main(env=environment, reviewer=fail_if_called)

    assert exit_code == 2
    assert calls == []
    assert "configuration" in capsys.readouterr().err.lower()


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
