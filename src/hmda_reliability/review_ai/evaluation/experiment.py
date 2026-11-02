"""Langfuse tutorial 방식의 Dataset 실험: task, run_experiment, format.

python -m hmda_reliability.review_ai.evaluation.experiment
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path
from typing import Any

from langfuse import get_client
from pydantic import ValidationError

from hmda_reliability.review_ai import review_null_spike
from hmda_reliability.review_ai.contracts import AgenticReviewInput
from hmda_reliability.review_ai.staged.progress import StageProgress
from hmda_reliability.review_ai.staged.prompt import load_stage_prompts
from hmda_reliability.runtime_ai import RuntimeAISettings


def _progress(event: StageProgress) -> None:
    if event.phase in {"stage_started", "stage_finished"}:
        print(
            f"{event.stage_id}: {event.phase} {event.status or ''}",
            file=sys.stderr,
            flush=True,
        )


def main(*, argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Langfuse Dataset 한국어 세 단계 검토")
    parser.add_argument("--dataset", default="hmda-review-ai-staged-v1")
    parser.add_argument("--name", default="한국어 단계별 검토")
    parser.add_argument("--dataset-version", type=datetime.fromisoformat)
    parser.add_argument("--prompt-label", default="production")
    args = parser.parse_args(argv)
    try:
        if args.dataset_version is not None and args.dataset_version.tzinfo is None:
            raise ValueError("dataset version requires a timezone")
        langfuse = get_client()
        prompts = load_stage_prompts(client=langfuse, label=args.prompt_label)
        config = prompts["evidence_review"].config
        settings = RuntimeAISettings(
            base_url=os.environ["OPENAI_BASE_URL"],
            api_key=os.environ["OPENAI_API_KEY"],
            model=config["model"],
            max_output_tokens=config.get("max_tokens", 1024),
            connect_timeout_seconds=10,
            read_timeout_seconds=config.get("timeout", 300),
            max_retries=0,
        )
        revision = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip()
        if subprocess.check_output(
            ["git", "diff", "HEAD", "--name-only"], text=True
        ).strip():
            revision += "-dirty"
        dataset = langfuse.get_dataset(args.dataset, version=args.dataset_version)

        def task(*, item: Any, **_: Any) -> dict[str, Any]:
            try:
                payload = item.input
                if isinstance(payload, dict):
                    payload = {**payload, "project_revision": revision}
                review_input = AgenticReviewInput.model_validate(payload)
            except ValidationError:
                return {
                    "status": "input_rejected",
                    "failure_code": "invalid_review_input",
                }
            result = review_null_spike(
                incident=review_input.incident,
                evidence=review_input.evidence,
                draft=review_input.draft,
                project_revision=revision,
                settings=settings,
                prompts=prompts,
                langfuse_client=langfuse,
                on_progress=_progress,
                artifact_root=Path(
                    os.getenv("HMDA_RELIABILITY_ARTIFACTS_DIR", ".local/artifacts")
                ),
            )
            # SDK task output에는 개인 로컬 경로를 복제하지 않는다.
            return {
                "status": result.status,
                "failure_code": result.failure_code,
                "workflow_id": result.workflow_id,
                "output": result.output.model_dump(mode="json")
                if result.output
                else None,
            }

        result = dataset.run_experiment(
            name=args.name,
            task=task,
            max_concurrency=1,
            metadata={
                "project_revision": revision,
                "prompts": [
                    {"name": prompt.name, "version": prompt.version}
                    for prompt in prompts.values()
                ],
            },
        )
        print(result.format())
        return (
            0
            if result.item_results
            and all(
                isinstance(item.output, dict)
                and item.output.get("status") == "completed"
                for item in result.item_results
            )
            else 1
        )
    except Exception:
        print(
            "실험을 완료하지 못했습니다. "
            "연결 설정과 Langfuse Dataset·프롬프트를 확인하세요.",
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
