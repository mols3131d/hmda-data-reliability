"""합성 사례를 Langfuse native 실험으로 실행하거나 사람 annotation을 조회한다."""

import argparse
import json
import math
import os
import queue
import re
import subprocess
import sys
import threading
import time
import uuid
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from hmda_reliability.review_ai.evaluation.live import load_live_configuration
from hmda_reliability.review_ai.evaluation.progress import LiveProgressReporter
from hmda_reliability.review_ai.staged.progress import StageProgress
from hmda_reliability.review_ai.store import write_review_json

_TRUE = {"1", "true", "yes", "on"}


def langfuse_settings(environment: Mapping[str, str]) -> dict[str, Any]:
    endpoint = environment["LANGFUSE_BASE_URL"]
    parsed = urlsplit(endpoint)
    if (
        parsed.scheme not in ("http", "https")
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("invalid_endpoint")
    timeout = float(environment.get("HMDA_LANGFUSE_IO_TIMEOUT_SECONDS", "30"))
    if not math.isfinite(timeout) or not 1 <= timeout <= 300:
        raise ValueError("invalid_io_timeout")
    dataset = environment.get("HMDA_LANGFUSE_DATASET", "hmda-review-ai-staged-v1")
    if not re.fullmatch(r"[A-Za-z0-9._-]{1,128}", dataset):
        raise ValueError("invalid_dataset_name")
    if (
        not environment["LANGFUSE_PUBLIC_KEY"].strip()
        or not environment["LANGFUSE_SECRET_KEY"].strip()
    ):
        raise ValueError("missing_credentials")
    return dict(
        base_url=endpoint,
        public_key=environment["LANGFUSE_PUBLIC_KEY"],
        secret_key=environment["LANGFUSE_SECRET_KEY"],
        io_timeout_seconds=timeout,
        dataset_name=dataset,
    )


def run_isolated(
    request: Mapping[str, Any],
    environment: Mapping[str, str],
    *,
    command: Sequence[str] | None = None,
) -> dict[str, Any]:
    allowed = {
        "PATH",
        "SYSTEMROOT",
        "TMPDIR",
        "TEMP",
        "SSL_CERT_FILE",
        "SSL_CERT_DIR",
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "NO_PROXY",
    }
    child_env = {
        k: v
        for k, v in environment.items()
        if k in allowed
        or k.startswith("HMDA_AGENTIC_REVIEW_")
        or k == "HMDA_RELIABILITY_ARTIFACTS_DIR"
    }
    child_env["LANGFUSE_MEDIA_UPLOAD_ENABLED"] = "false"
    io_timeout = request["langfuse"]["io_timeout_seconds"]
    proc = subprocess.Popen(
        command
        or [
            sys.executable,
            "-m",
            "hmda_reliability.review_ai.evaluation.experiment_worker",
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        env=child_env,
        text=True,
    )
    lines: queue.Queue[str | None] = queue.Queue()

    def consume() -> None:
        assert proc.stdout is not None
        try:
            while line := proc.stdout.readline(1_048_577):
                if len(line) > 1_048_576:
                    return
                lines.put(line)
        finally:
            lines.put(None)

    reader = threading.Thread(target=consume, daemon=True)
    reader.start()
    deadline = time.monotonic() + io_timeout
    remote = True
    receipt = None
    core = []

    def feed() -> None:
        assert proc.stdin is not None
        try:
            proc.stdin.write(json.dumps(request))
            proc.stdin.close()
        except (OSError, ValueError):
            pass

    writer = threading.Thread(target=feed, daemon=True)
    try:
        writer.start()
        with LiveProgressReporter() as report:
            while True:
                if remote and time.monotonic() >= deadline:
                    receipt = {
                        "status": "unavailable",
                        "failure_code": "external_io_timeout",
                    }
                    break
                try:
                    line = lines.get(timeout=0.1)
                except queue.Empty:
                    continue
                if line is None:
                    break
                try:
                    event = json.loads(line)
                except ValueError:
                    continue
                if not isinstance(event, dict):
                    continue
                if event.get("kind") == "phase" and event.get("phase") in (
                    "core",
                    "remote",
                ):
                    remote = event["phase"] == "remote"
                    if remote:
                        deadline = time.monotonic() + io_timeout
                elif event.get("kind") == "progress":
                    progress = event.get("event", {})
                    if (
                        progress.get("stage_id")
                        in ("evidence_review", "draft_critique", "synthesis")
                        and progress.get("phase")
                        in (
                            "stage_started",
                            "provider_started",
                            "provider_finished",
                            "stage_finished",
                        )
                        and type(progress.get("attempt_count")) is int
                    ):
                        report(StageProgress(**progress))
                elif event.get("kind") == "core_result":
                    core.append(event["result"])
                elif event.get("kind") == "receipt":
                    receipt = event["receipt"]
    finally:
        if proc.poll() is None:
            proc.kill()
        proc.wait(timeout=5)
        reader.join(timeout=1)
        writer.join(timeout=1)
        if proc.stdout is not None:
            proc.stdout.close()
    return dict(
        receipt or {"status": "unavailable", "failure_code": "worker_failed"},
        core_results=core,
    )


def _load_receipt(path: Path) -> dict[str, Any]:
    with path.open("rb") as stream:
        body = stream.read(2_097_153)
    if len(body) > 2_097_152:
        raise ValueError("receipt_too_large")
    value = json.loads(body)
    if not isinstance(value, dict) or not value.get("bindings"):
        raise ValueError("invalid_receipt")
    return value


def main(
    *, env: Mapping[str, str] | None = None, argv: Sequence[str] | None = None
) -> int:
    environment = dict(os.environ if env is None else env)
    parser = argparse.ArgumentParser(description="Langfuse native 한국어 검토 실험")
    parser.add_argument(
        "--check", type=Path, help="저장된 실험 receipt의 사람 평가 조회"
    )
    parser.add_argument("--reviewer-id")
    parser.add_argument("--baseline", type=Path, help="비교할 기존 baseline receipt")
    args = parser.parse_args(argv)
    if environment.get("HMDA_LANGFUSE_ENABLED", "").strip().lower() not in _TRUE:
        print(json.dumps({"status": "disabled"}))
        return 0
    try:
        settings = langfuse_settings(environment)
        if args.check:
            if not args.reviewer_id:
                raise ValueError("reviewer_required")
            request = dict(
                action="check",
                langfuse=settings,
                receipt=_load_receipt(args.check),
                reviewer_id=args.reviewer_id,
            )
            request["artifact_root"] = environment.get(
                "HMDA_RELIABILITY_ARTIFACTS_DIR", ".local/artifacts"
            )
            if args.baseline:
                request["baseline"] = _load_receipt(args.baseline)
            result = run_isolated(request, environment)
            print(json.dumps(result, ensure_ascii=False))
            return (
                0
                if result["status"] == "checked"
                and bool(result["annotations"])
                and all(a["status"] == "complete" for a in result["annotations"])
                else 1
            )
        if environment.get("HMDA_AGENTIC_REVIEW_LIVE", "").strip().lower() not in _TRUE:
            raise ValueError("live_opt_in_required")
        configuration = load_live_configuration(environment)
        environment["HMDA_AGENTIC_REVIEW_PROJECT_REVISION"] = (
            configuration.project_revision
        )
        cases = json.loads(Path(__file__).with_name("cases.json").read_text())
        run_name = "lf-" + uuid.uuid4().hex
        directory = (
            configuration.artifact_root / "agentic-review" / "experiments" / run_name
        )
        directory.mkdir(parents=True, exist_ok=False, mode=0o700)
        request = dict(action="run", langfuse=settings, cases=cases, run_name=run_name)
        if args.baseline:
            request["baseline"] = _load_receipt(args.baseline)
        result = run_isolated(request, environment)
        result["project_revision"] = configuration.project_revision
        path = write_review_json(
            directory / "receipt.json", result, max_record_bytes=2_097_152
        )
        print(
            json.dumps(
                dict(result, receipt_path=str(path)), ensure_ascii=False, indent=2
            )
        )
        return (
            0
            if result["status"] == "submitted_unverified"
            and len(result["core_results"]) == len(cases)
            and all(r["status"] == "completed" for r in result["core_results"])
            else 1
        )
    except (KeyError, ValueError, OSError):
        print("Langfuse 실험 설정 또는 로컬 자료 오류입니다.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
