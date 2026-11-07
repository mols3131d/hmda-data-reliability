"""Langfuse Dataset 기반 신뢰성 AI 에이전트 실험 러너 모듈.

python -m hmda_reliability.reliability_ai.evaluation.experiment
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from collections import Counter
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path
from typing import Any, cast

from langfuse import get_client
from langfuse.api import DatasetItem
from pydantic import ValidationError

from hmda_reliability.reliability_ai import (
    AgenticReviewInput,
    ReliabilityAISettings,
    investigate_incident,
)
from hmda_reliability.runtime_ai import RuntimeAISettings


def main(*, argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Langfuse Dataset 신뢰성 AI 조사 실험")
    parser.add_argument("--dataset", default="hmda-reliability-ai-v1")
    parser.add_argument("--name", default="신뢰성 AI 조사 실험")
    parser.add_argument("--dataset-version", type=datetime.fromisoformat)
    parser.add_argument("--model", default="qwen3.5:4b-8k-local")
    args = parser.parse_args(argv)
    try:
        if args.dataset_version is not None and args.dataset_version.tzinfo is None:
            raise ValueError("dataset version requires a timezone")
        langfuse = get_client()
        settings = RuntimeAISettings(
            base_url=os.environ.get("OPENAI_BASE_URL", "http://localhost:11434/v1"),
            api_key=os.environ.get("OPENAI_API_KEY", "local"),
            model=args.model,
            max_output_tokens=1024,
            connect_timeout_seconds=10,
            read_timeout_seconds=300,
            max_retries=0,
        )
        ai_settings = ReliabilityAISettings()
        revision = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip()
        if subprocess.check_output(
            ["git", "diff", "HEAD", "--name-only"], text=True
        ).strip():
            revision += "-dirty"
        dataset = langfuse.get_dataset(args.dataset, version=args.dataset_version)
        expected_items = Counter(item.id for item in dataset.items)

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
            result = investigate_incident(
                review_input,
                settings=settings,
                ai_settings=ai_settings,
                artifact_root=Path(
                    os.getenv("HMDA_RELIABILITY_ARTIFACTS_DIR", ".local/artifacts")
                ),
            )
            return {
                **result.model_dump(mode="json"),
                "tool_calls_count": len(result.tool_calls),
            }

        result = dataset.run_experiment(
            name=args.name,
            task=task,
            max_concurrency=1,
            metadata={"project_revision": revision, "model": args.model},
        )
        print(result.format())
        actual_items = Counter(
            cast(DatasetItem, item.item).id for item in result.item_results
        )
        if actual_items != expected_items:
            print(
                "실험 결과에 누락되거나 중복된 Dataset 항목이 있습니다.",
                file=sys.stderr,
            )
            return 1
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
            "실험을 완료하지 못했습니다. 연결 설정과 Langfuse Dataset을 확인하세요.",
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
