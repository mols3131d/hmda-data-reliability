"""Langfuse 합성 Dataset 등록 모듈.

python -m hmda_reliability.reliability_ai.evaluation.setup
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from importlib.resources import files

from langfuse import get_client


def main(*, argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Langfuse 합성 Dataset 등록")
    parser.add_argument("--dataset", default="hmda-reliability-ai-v1")
    parser.add_argument("--prompts-only", action="store_true")
    args = parser.parse_args(argv)
    try:
        langfuse = get_client()
        resources = files("hmda_reliability.reliability_ai.prompt")
        references: list[str] = []
        for path in (
            "investigation.md",
            "guidance/numeric_fidelity.md",
            "guidance/evidence_review.md",
            "policies/language.md",
            "policies/advisory.md",
        ):
            name = "hmda-reliability-ai/components/" + path.removesuffix(".md")
            component = langfuse.create_prompt(
                name=name,
                type="text",
                prompt=resources.joinpath(path).read_text(encoding="utf-8"),
                labels=["production"],
            )
            references.append(
                f"@@@langfusePrompt:name={name}|version={component.version}@@@"
            )
        langfuse.create_prompt(
            name="hmda-reliability-ai/investigation",
            type="chat",
            prompt=[
                {"role": "system", "content": "\n\n".join(references)},
                {"role": "user", "content": "{{canonical_input}}"},
                {"type": "placeholder", "name": "history"},
            ],
            labels=["production"],
        )
        if args.prompts_only:
            print("조사용 native Prompt를 등록했습니다.")
            return 0
        langfuse.create_dataset(
            name=args.dataset, description="신뢰성 AI 조사 합성 Dataset"
        )
        cases = json.loads(
            files("hmda_reliability.reliability_ai.evaluation")
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
        print("합성 Dataset을 등록했습니다.")
        return 0
    except Exception:
        print(
            "등록을 완료하지 못했습니다. 연결 설정과 서버 상태를 확인하세요.",
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
