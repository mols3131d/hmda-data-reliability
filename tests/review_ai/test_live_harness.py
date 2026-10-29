"""Opt-in live harness configuration and network-isolation tests."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Literal, cast

import pytest

from hmda_reliability.reliability import Evidence, Incident, RemediationDraft
from hmda_reliability.review_ai.evaluation import live as live_module
from hmda_reliability.review_ai.evidence import (
    SanitizedAgenticReviewConfiguration,
)
from hmda_reliability.review_ai.settings import ReviewAISettings
from hmda_reliability.review_ai.staged import service as staged_service
from hmda_reliability.review_ai.staged.evidence import StagedReviewResult
from hmda_reliability.review_ai.staged.progress import ProgressCallback
from hmda_reliability.review_ai.staged.service import review_null_spike_staged
from hmda_reliability.review_ai.staged.settings import StagedExecutionSettings
from hmda_reliability.runtime_ai import RuntimeAISettings
from hmda_reliability.runtime_ai.contracts import ChatMessage, ProviderResponse
from hmda_reliability.runtime_ai.provider import ProviderUnavailableError

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
        budget_seconds: float | None = None,
    ) -> ProviderResponse:
        assert output_format == "text"
        self.messages.append(messages)
        return ProviderResponse(content=self.text, attempt_count=1, latency_ms=1)


def _run_staged_review(
    kwargs: dict[str, object],
    provider: StagedTextProvider,
    *,
    clock: Callable[[], float] = time.monotonic,
) -> StagedReviewResult:
    return review_null_spike_staged(
        incident=cast(Incident, kwargs["incident"]),
        evidence=cast(Sequence[Evidence], kwargs["evidence"]),
        draft=cast(RemediationDraft, kwargs["draft"]),
        project_revision=cast(str, kwargs["project_revision"]),
        settings=cast(RuntimeAISettings, kwargs["settings"]),
        review_settings=cast(ReviewAISettings, kwargs["review_settings"]),
        execution_settings=cast(StagedExecutionSettings, kwargs["execution_settings"]),
        artifact_root=cast(Path, kwargs["artifact_root"]),
        provider=provider,
        workflow_id_factory=lambda: "workflow-cli-test",
        clock=clock,
        on_progress=cast(ProgressCallback | None, kwargs.get("on_progress")),
    )


def test_default_entrypoint_executes_the_current_api(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    provider = StagedTextProvider()
    monkeypatch.setattr(
        staged_service, "OpenAICompatibleAdapter", lambda settings, **kwargs: provider
    )
    assert live_module.main(env=_live_environment(tmp_path)) == 0
    captured = capsys.readouterr()
    assert json.loads(captured.out)["status"] == "completed"
    assert len(provider.messages) == 3
    assert "가상 사례로 실제 모델 통합 검증 시작" in captured.err
    assert "단계 1/3 근거 검토 시작" in captured.err
    assert "단계 3/3 종합 검토 수집·저장 완료" in captured.err
    assert provider.text not in captured.out + captured.err


def test_unrelated_environment_cannot_select_another_workflow(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    environment = _live_environment(tmp_path)
    environment.update(
        {
            "HMDA_AGENTIC_REVIEW_MODE": "PRIVATE_UNUSED_MODE",
            "HMDA_AGENTIC_REVIEW_PROMPT_VERSION": "PRIVATE_UNUSED_VERSION",
            "HMDA_AGENTIC_REVIEW_LEGACY_PROMPT_VERSION": "PRIVATE_UNUSED_VERSION",
            "HMDA_LANGFUSE_EXPORT": "true",
        }
    )
    provider = StagedTextProvider()

    def review(**kwargs: object) -> StagedReviewResult:
        return _run_staged_review(kwargs, provider)

    assert live_module.main(env=environment, reviewer=review) == 0
    captured = capsys.readouterr()
    assert len(provider.messages) == 3
    assert "가상 사례로 실제 모델 통합 검증 시작" in captured.err
    assert "PRIVATE_UNUSED" not in captured.out + captured.err
    assert "Langfuse" not in captured.out + captured.err


def test_disabled_staged_live_mode_never_calls_the_reviewer(
    capsys: pytest.CaptureFixture[str],
) -> None:
    def unexpected_review(**kwargs: object) -> StagedReviewResult:
        pytest.fail("disabled live mode must not call the staged reviewer")

    exit_code = live_module.main(env={}, reviewer=unexpected_review)

    assert exit_code == 0
    assert "disabled" in capsys.readouterr().out.lower()


def test_invalid_staged_configuration_never_calls_the_reviewer(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    environment = _live_environment(tmp_path)
    environment["HMDA_AGENTIC_REVIEW_TIMEOUT_SECONDS"] = "not-a-number"

    def unexpected_review(**kwargs: object) -> StagedReviewResult:
        pytest.fail("invalid settings must not call the staged reviewer")

    exit_code = live_module.main(env=environment, reviewer=unexpected_review)

    assert exit_code == 2
    assert "configuration" in capsys.readouterr().err.lower()


@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        ({}, (30, 10, 300, 0)),
        ({"TIMEOUT_SECONDS": "17"}, (17, 10, 17, 0)),
        (
            {
                "TIMEOUT_SECONDS": "17",
                "READ_TIMEOUT_SECONDS": "23",
                "CONNECT_TIMEOUT_SECONDS": "4",
                "MAX_RETRIES": "2",
            },
            (17, 4, 23, 2),
        ),
        (
            {
                "READ_TIMEOUT_SECONDS": "19",
                "CONNECT_TIMEOUT_SECONDS": "3",
                "MAX_RETRIES": "1",
                "STAGE_BUDGET_SECONDS": "11",
                "WORKFLOW_BUDGET_SECONDS": "33",
            },
            (30, 3, 19, 1),
        ),
    ],
)
def test_live_timing_environment_precedence_and_defaults(
    tmp_path: Path, overrides: dict[str, str], expected: tuple[int, int, int, int]
) -> None:
    environment = _live_environment(tmp_path)
    environment.pop("HMDA_AGENTIC_REVIEW_TIMEOUT_SECONDS")
    environment.pop("HMDA_AGENTIC_REVIEW_MAX_RETRIES")
    environment.update(
        {f"HMDA_AGENTIC_REVIEW_{name}": value for name, value in overrides.items()}
    )
    calls: list[dict[str, object]] = []

    def review(**kwargs: object) -> StagedReviewResult:
        calls.append(kwargs)
        return StagedReviewResult(status="input_rejected", failure_code="test_only")

    assert live_module.main(env=environment, reviewer=review) == 1
    assert len(calls) == 1
    actual = cast(RuntimeAISettings, calls[0]["settings"]).model_dump()
    assert (
        actual["timeout_seconds"],
        actual["connect_timeout_seconds"],
        actual["read_timeout_seconds"],
        actual["max_retries"],
    ) == expected
    execution = cast(StagedExecutionSettings, calls[0]["execution_settings"])
    assert execution.model_dump() == {
        "stage_budget_seconds": float(overrides.get("STAGE_BUDGET_SECONDS", 360)),
        "workflow_budget_seconds": float(
            overrides.get("WORKFLOW_BUDGET_SECONDS", 1200)
        ),
    }
    assert "prompt_identity" not in calls[0]


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("CONNECT_TIMEOUT_SECONDS", "0"),
        ("CONNECT_TIMEOUT_SECONDS", "nan"),
        ("READ_TIMEOUT_SECONDS", "0"),
        ("READ_TIMEOUT_SECONDS", "not-a-number"),
        ("READ_TIMEOUT_SECONDS", "inf"),
        ("STAGE_BUDGET_SECONDS", "0"),
        ("STAGE_BUDGET_SECONDS", "7201"),
        ("WORKFLOW_BUDGET_SECONDS", "-1"),
        ("WORKFLOW_BUDGET_SECONDS", "nan"),
        ("WORKFLOW_BUDGET_SECONDS", "21601"),
    ],
)
def test_invalid_live_timing_environment_is_rejected_before_review(
    tmp_path: Path, name: str, value: str, capsys: pytest.CaptureFixture[str]
) -> None:
    environment = _live_environment(tmp_path)
    environment[f"HMDA_AGENTIC_REVIEW_{name}"] = value

    def unexpected_review(**kwargs: object) -> StagedReviewResult:
        pytest.fail("invalid timing configuration must not start a workflow")

    assert live_module.main(env=environment, reviewer=unexpected_review) == 2
    assert "configuration" in capsys.readouterr().err.lower()


@pytest.mark.parametrize(
    ("recorded_url", "configured_url", "matches"),
    [
        ("https://provider.invalid", "https://provider.invalid/", True),
        ("https://provider.invalid/v1", "https://provider.invalid/v2", False),
        ("https://other.invalid/", "https://provider.invalid/", False),
        ("not-a-url", "https://provider.invalid/", False),
    ],
)
def test_configuration_comparison_normalizes_root_urls_without_changing_the_record(
    recorded_url: str, configured_url: str, matches: bool
) -> None:
    settings = RuntimeAISettings(
        base_url=configured_url,
        api_key="unused-test-key",
        model="comparison-model",
    )
    configuration = SanitizedAgenticReviewConfiguration.model_validate(
        {
            **settings.sanitized_configuration(),
            **ReviewAISettings().sanitized_configuration(),
            "base_url": recorded_url,
        }
    )

    assert (
        live_module._configuration_matches(
            configuration, settings=settings, review_settings=ReviewAISettings()
        )
        is matches
    )
    assert configuration.base_url == recorded_url


@pytest.mark.parametrize("remove_manifest", [False, True])
def test_staged_live_verifies_the_workflow_and_keeps_answers_off_the_console(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    remove_manifest: bool,
) -> None:
    environment = _live_environment(tmp_path)
    provider = StagedTextProvider()

    def staged_review(**kwargs: object) -> StagedReviewResult:
        result = _run_staged_review(kwargs, provider)
        assert result.workflow_path is not None
        if remove_manifest:
            result.workflow_path.unlink()
        return result

    exit_code = live_module.main(env=environment, reviewer=staged_review)

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


def test_partial_provider_failure_keeps_the_first_stage_and_verified_manifest(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    class FailingProvider(StagedTextProvider):
        def invoke(self, messages, *, output_format="json_object", budget_seconds=None):
            response = super().invoke(
                messages, output_format=output_format, budget_seconds=budget_seconds
            )
            if len(self.messages) == 2:
                raise ProviderUnavailableError(
                    failure_code="provider_timeout", attempt_count=1, latency_ms=1
                )
            return response

    provider = FailingProvider()

    def review(**kwargs: object) -> StagedReviewResult:
        return _run_staged_review(kwargs, provider)

    assert live_module.main(env=_live_environment(tmp_path), reviewer=review) == 1
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["failure_code"] == "provider_timeout"
    assert len(provider.messages) == 2
    assert payload["output_path"] is None
    assert (
        Path(payload["stages"][0]["response_path"]).read_text(encoding="utf-8")
        == provider.text
    )
    assert payload["stages"][1]["response_path"] is None
    assert "provenance validation failed" not in captured.err.lower()


def test_late_body_is_preserved_without_being_adopted_or_calling_the_next_stage(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    elapsed = [0.0]

    class LateProvider(StagedTextProvider):
        def invoke(self, messages, *, output_format="json_object", budget_seconds=None):
            response = super().invoke(
                messages, output_format=output_format, budget_seconds=budget_seconds
            )
            elapsed[0] = 2.0
            return response

    environment = _live_environment(tmp_path)
    environment["HMDA_AGENTIC_REVIEW_STAGE_BUDGET_SECONDS"] = "1"
    provider = LateProvider()

    def review(**kwargs: object) -> StagedReviewResult:
        return _run_staged_review(kwargs, provider, clock=lambda: elapsed[0])

    assert live_module.main(env=environment, reviewer=review) == 1
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["failure_code"] == "stage_budget_exhausted"
    assert len(provider.messages) == 1
    assert (
        Path(payload["stages"][0]["response_path"]).read_text(encoding="utf-8")
        == provider.text
    )
    assert payload["output_path"] is None
    assert "provenance validation failed" not in captured.err.lower()


def test_staged_live_verifies_a_collection_persisted_after_budget_exhaustion(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    environment = _live_environment(tmp_path)
    environment["HMDA_AGENTIC_REVIEW_WORKFLOW_BUDGET_SECONDS"] = "10"
    provider = StagedTextProvider()
    elapsed = [0.0]
    original_write = live_module.StagedReviewStore.write_output

    def write_after_budget(self, workflow_id, output, *, max_bytes):
        path = original_write(self, workflow_id, output, max_bytes=max_bytes)
        elapsed[0] = 11.0
        return path

    monkeypatch.setattr(
        live_module.StagedReviewStore, "write_output", write_after_budget
    )

    def staged_review(**kwargs: object) -> StagedReviewResult:
        result = _run_staged_review(kwargs, provider, clock=lambda: elapsed[0])
        assert result.status == "unavailable"
        assert result.failure_code == "workflow_budget_exhausted"
        assert result.output is None
        assert result.output_path is not None and result.output_path.is_file()
        return result

    exit_code = live_module.main(env=environment, reviewer=staged_review)

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "provenance validation failed" not in captured.err.lower()
    assert provider.text not in captured.out + captured.err


@pytest.mark.parametrize(
    "tamper",
    [
        "status",
        "revision",
        "configuration",
        "phase_configuration",
        "timeout_configuration",
        "execution_settings",
        "missing_execution_settings",
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
        elif tamper == "timeout_configuration":
            manifest["configuration"]["timeout_seconds"] = 9
        elif tamper == "phase_configuration":
            manifest["configuration"]["read_timeout_seconds"] = 1
        elif tamper == "execution_settings":
            manifest["execution_settings"] = {
                "stage_budget_seconds": 9,
                "workflow_budget_seconds": 27,
            }
        elif tamper == "missing_execution_settings":
            manifest.pop("execution_settings")
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

    exit_code = live_module.main(env=environment, reviewer=staged_review)

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "provenance validation failed" in captured.err.lower()
    assert "PRIVATE_STAGED_ANSWER" not in captured.out + captured.err


def test_opt_in_requires_provider_identity_values(
    capsys: pytest.CaptureFixture[str],
) -> None:
    calls: list[dict[str, object]] = []

    def fail_if_called(**kwargs: object) -> StagedReviewResult:
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

    def capture_review(**kwargs: object) -> StagedReviewResult:
        calls.append(kwargs)
        return StagedReviewResult(
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
    assert "prompt_identity" not in call
    assert call["artifact_root"] == tmp_path / "artifacts"
    assert incident.incident_type == "null_spike"
    assert draft.incident_type == "null_spike"
    assert len(evidence) == 1
    assert evidence[0].payload["rule"] == "null_spike"
    output = capsys.readouterr().out
    assert '"status": "input_rejected"' in output
    assert "live-test-secret" not in output


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

    def capture_review(**kwargs: object) -> StagedReviewResult:
        calls.append(kwargs)
        return StagedReviewResult(
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
    calls: list[list[str]] = []

    def git_from_source(command: list[str], **kwargs: object):
        calls.append(command)
        return next(results)

    monkeypatch.setattr(live_module.subprocess, "run", git_from_source)
    monkeypatch.chdir(Path(live_module.__file__).parent)

    assert live_module._current_git_revision() == "git-head-123"
    assert all(command[2] == str(live_module._REPOSITORY_ROOT) for command in calls)


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


def test_auto_revision_rejects_a_checkout_that_did_not_supply_the_loaded_module(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "pyproject.toml").touch()
    (tmp_path / ".git").touch()
    monkeypatch.setattr(live_module, "_REPOSITORY_ROOT", tmp_path)

    def unexpected_git(*args: object, **kwargs: object) -> None:
        pytest.fail("an unrelated checkout cannot supply revision proof")

    monkeypatch.setattr(live_module.subprocess, "run", unexpected_git)
    with pytest.raises(ValueError, match="loaded source checkout"):
        live_module._current_git_revision()


@pytest.mark.component
def test_auto_revision_ignores_inherited_git_repository_overrides(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    git_environment = {
        key: value for key, value in os.environ.items() if not key.startswith("GIT_")
    }

    def git(directory: Path, *args: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(directory), *args],
            env=git_environment,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()

    source = tmp_path / "source"
    other = tmp_path / "other"
    source_file = source / "src/hmda_reliability/review_ai/evaluation/live.py"
    source_file.parent.mkdir(parents=True)
    source_file.touch()
    (source / "pyproject.toml").touch()
    other.mkdir()
    for directory in (source, other):
        git(directory, "init", "--quiet")
        git(directory, "add", ".")
        git(
            directory,
            "-c",
            "user.name=Review Test",
            "-c",
            "user.email=review-test@example.invalid",
            "-c",
            "commit.gpgsign=false",
            "commit",
            "--quiet",
            "--allow-empty",
            "-m",
            directory.name,
        )
    expected = git(source, "rev-parse", "HEAD")
    assert expected != git(other, "rev-parse", "HEAD")
    monkeypatch.setattr(live_module, "__file__", str(source_file))
    monkeypatch.setattr(live_module, "_REPOSITORY_ROOT", source)
    monkeypatch.setenv("GIT_DIR", str(other / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(other))
    monkeypatch.setenv("GIT_INDEX_FILE", str(other / ".git/index"))

    assert live_module._current_git_revision() == expected


def test_module_entrypoint_stays_opt_in_from_another_working_directory(
    tmp_path: Path,
) -> None:
    environment = dict(os.environ, HMDA_AGENTIC_REVIEW_LIVE="false")
    result = subprocess.run(
        [sys.executable, "-m", "hmda_reliability.review_ai.evaluation.live"],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "disabled" in result.stdout
    assert result.stderr == ""


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

    def fail_if_called(**kwargs: object) -> StagedReviewResult:
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

    def fail_if_called(**kwargs: object) -> StagedReviewResult:
        calls.append(kwargs)
        raise AssertionError("invalid configuration must not call provider")

    exit_code = live_module.main(env=environment, reviewer=fail_if_called)

    assert exit_code == 2
    assert calls == []
    assert "configuration" in capsys.readouterr().err.lower()
