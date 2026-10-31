"""한국어 prompt 모듈과 합성 Dataset을 명시적으로 최초 등록한다.

python -m hmda_reliability.review_ai.evaluation.setup
반복 실험에서는 실행하지 않는다. 이후 편집과 사람 평가는 Langfuse UI를 사용한다.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from importlib.resources import files

from langfuse import get_client

from hmda_reliability.review_ai.staged.contracts import STAGE_IDS

_COMMON = (
    "tasks/null_spike",
    "policies/language",
    "output/prose",
    "guidance/numeric_fidelity",
    "guidance/evidence_review",
    "policies/advisory",
)


def main(*, argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Langfuse 한국어 프롬프트·합성 Dataset 최초 등록"
    )
    parser.add_argument("--dataset", default="hmda-review-ai-staged-v1")
    parser.add_argument("--model", default="qwen3.5:4b-8k-local")
    parser.add_argument("--label", default="production")
    args = parser.parse_args(argv)
    try:
        langfuse = get_client()
        resources = files("hmda_reliability.review_ai.prompt")
        references = {}
        for part in (*_COMMON, *(f"staged/{stage}" for stage in STAGE_IDS)):
            prompt = langfuse.create_prompt(
                name=f"hmda-review-ai/{part}",
                type="text",
                prompt=resources.joinpath(f"{part}.md").read_text(encoding="utf-8"),
                labels=[args.label],
            )
            references[part] = (
                f"@@@langfusePrompt:name={prompt.name}|version={prompt.version}@@@"
            )
        for stage in STAGE_IDS:
            parts = [
                part
                for part in _COMMON
                if stage != "draft_critique" or part != "guidance/numeric_fidelity"
            ]
            langfuse.create_prompt(
                name=f"hmda-review-ai/{stage}",
                type="chat",
                labels=[args.label],
                prompt=[
                    {
                        "role": "system",
                        "content": "\n".join(references[part] for part in parts),
                    },
                    {"type": "placeholder", "name": "history"},
                    {"role": "system", "content": references[f"staged/{stage}"]},
                ],
                config={"model": args.model, "max_tokens": 1024, "timeout": 300}
                if stage == "evidence_review"
                else {},
            )
        langfuse.create_dataset(
            name=args.dataset, description="가상 컨텍스트의 한국어 단계별 검토"
        )
        cases = json.loads(
            files("hmda_reliability.review_ai.evaluation")
            .joinpath("cases.json")
            .read_text(encoding="utf-8")
        )
        for case in cases:
            langfuse.create_dataset_item(
                dataset_name=args.dataset,
                input=case["review_input"],
                expected_output=case["oracle"],
                metadata={
                    "case_id": case["case_id"],
                    "case_version": case["case_version"],
                    "synthetic": True,
                },
            )
        print(
            "프롬프트와 합성 Dataset을 등록했습니다. "
            "이후 편집·평가는 Langfuse UI에서 진행하세요."
        )
        return 0
    except Exception:
        print(
            "등록을 완료하지 못했습니다. 연결 설정과 서버 상태를 확인하세요.",
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
