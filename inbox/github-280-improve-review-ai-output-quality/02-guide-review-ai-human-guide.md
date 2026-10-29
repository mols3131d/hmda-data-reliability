---
type: guide
title: Review AI Human Review Guide
description: PR 280의 가상 컨텍스트와 현재 한국어 3단계 모델 답변을 대조하고 사람이 품질을 평가하는 실행·검토 안내서입니다.
tags:
  - review-ai
  - output-quality
  - human-review
---

# Review AI Human Review Guide

**검토할 것은 가상의 사고 정보를 받은 실제 모델의 답변이다.** 입력과 세 단계 원문을 나란히 읽고, 사실을 정확히 해석했는지와 다음 판단에 도움이 되는지를 평가한다. Profile·dbt 결과와 대응 초안은 합성 상황의 자료이며 이 검토를 위해 데이터를 적재하거나 실제 dbt 검사를 실행할 필요는 없다.

검토자는 **실제 답변 확보 → 수치·근거·초안 대조 → 다섯 항목 점수와 판단 기록** 순서로 진행한다. 현재 프롬프트는 근거 검토 → 초안 비판 → 종합의 한국어 텍스트를 요청하고 코드가 JSON을 만든다. `completed`는 수집·저장 완료다. 문장의 정확성·검토 가치·승인은 사람이 따로 판단한다.

## Review Basis

- Target: [PR #280](https://github.com/mols3131d/hmda-data-reliability/pull/280), `agent/feat/improve-review-ai-output-quality`.
- Execution source: 이 PR의 현재 checkout을 사용하고 실행할 때 실제 HEAD를 기록한다. 새 실행 모듈과 진행 표시는 [후속 검증 보고서](09-report-review-ai-live-progress.md)를 참고한다.
- Historical automated evidence: `3507558c9460e0579cd4a4ee78bd65ceadfd7a79`에서 관련 로컬 테스트 261개 통과. [CI](https://github.com/mols3131d/hmda-data-reliability/actions/runs/40830024998)는 통합 commit `efd70eb163fd7e68c7da6e1757726c9638cd08cc`에서 1,222개 통과·2개 생략이다. 새 실행 모듈을 검증한 CI 기록은 아니다.
- Human evidence: 현재 프롬프트의 실제 세 단계 완료와 사람의 품질 점수는 미검증이다. 이 문서는 평가 절차이며 실제 평가 결과를 기입하지 않았다.

이 문서는 같은 번호의 이전 안내서를 현재 실행에 맞춰 갱신한 것이다. 삭제한 버전 선택·옛 JSON 검증 경로를 사용하지 않는다. 상세 실행 계약은 [현재 평가 가이드](../../docs/development/review-ai-evaluation.md), 프롬프트 조립은 [Prompt Composition](../../docs/development/review-ai-prompts.md)을 따른다.

## Start With One Run

이 PR의 브랜치를 체크아웃한 저장소 최상위 디렉터리에서 [환경 파일 예제](../../.env.example)를 참고해 로컬 설정을 확인한다. 사용 중인 `.env`를 예제로 덮어쓰지 않는다.

- `HMDA_AGENTIC_REVIEW_LIVE=true`로 설정한다.
- 예시 모델은 `qwen3.5:4b-8k-local`이다. 호출할 서버에 설치된 태그·base URL·API key가 맞는지 확인한다. 실제 context·Thinking 설정은 모델 태그에서 추정하지 말고 실행 조건으로 기록한다.
- 로컬 시작값은 연결 10초·읽기 300초·단계 360초·전체 1,200초·retry 0회다. 예산은 진행 중 호출을 즉시 강제 종료하는 보장이 아니다.
- `HMDA_AGENTIC_REVIEW_PROJECT_REVISION=auto`는 추적 파일이 깨끗해야 한다. 미커밋 실행을 하면 로컬 표식과 변경 내용을 기록하고 clean commit 증거와 구분한다.

```bash
git status --short
git rev-parse HEAD
uv run --env-file .env python -m hmda_reliability.review_ai.evaluation.live
```

**이 CLI는 정보가 부족한 합성 시나리오 한 건만 실행한다.** 아래 corpus 세 건을 순회하지 않으며 corpus의 첫 입력과 식별자까지 같은 자료도 아니다. CLI 실행은 연결과 전체 흐름을 먼저 확인하는 용도다. 세 사례의 품질 검토에는 마지막의 선택 실행 예제를 사용한다.

표준 오류에는 단계 시작·수집 및 저장 결과, provider 호출 중에는 기본 5초마다 응답 대기와 단계·전체 경과시간이 표시된다. 이 시간에는 내부 retry·backoff가 포함될 수 있으며 모델의 생성률을 뜻하지 않는다. 표준 출력은 최종 JSON을 유지하므로 `> result.json`으로 저장하면서 진행 로그를 터미널에서 볼 수 있다. 원문은 진행 로그 대신 로컬 파일로 확인한다.

## Open These Artifacts

콘솔 결과에 표시된 경로를 VS Code에서 연다. 저장 루트는 `.env`의 `HMDA_RELIABILITY_ARTIFACTS_DIR`를 따른다.

| Field | 사람이 확인할 내용 |
| --- | --- |
| `workflow_path` | `workflow.json`의 실제 revision·모델/설정·`canonical_input`·단계 상태·시도 수·digest. `canonical_input`이 모델에게 제공한 근거의 기준이다. |
| `stages[].response_path` | 각 단계의 실제 UTF-8 답변. 공백·개행을 보존한 원문이며 실패한 응답도 반환된 범위에서 남는다. |
| `stages[].record_path` | 단계별 완료 이유·실패 코드·시간·원문 경로가 있는 checkpoint. |
| `output_path` | 세 단계가 모이면 코드가 만든 `output.json`. `stages[].text`와 원문 파일이 일치하는지 본다. |

먼저 `evidence_review` → `draft_critique` → `synthesis` 순서와 세 답변을 확인한다. `deterministic_facts`는 코드가 입력에서 복사한다. 이 값이 맞더라도 모델 문장의 비율·원인·권고는 틀릴 수 있으므로 반드시 `stages[].text`를 읽는다.

실패하면 `failure_code`와 마지막 단계의 기록·원문부터 확인한다. 첫째 단계가 성공했어도 둘째 단계가 실패하면 전체 성공으로 집계하지 않는다. `provider_timeout`·`provider_connection_error`처럼 본문 없이 끝난 호출에는 원문 파일이 없을 수 있다. 늦게 반환된 응답이나 저장된 output 경로가 있어도 완료로 채택되지 않을 수 있다. 실패 원인별 해석은 [진단 안내](../../docs/development/review-ai-evaluation.md#diagnose-a-failed-stage)를 따른다.

## Compare Input And Answer

[현재 corpus](../../tests/review_ai/evaluation/fixtures/output_quality_staged_v1.json)의 `review_input`만 모델 입력으로 사용한다. `profile_pair`·`oracle`·`controls`는 검토자용 합성 자료이며 실제 모델의 정답·응답·사람 점수가 아니다. 사례의 Evidence 중 실제 전달 범위는 `workflow.json`의 bounded `canonical_input`에서 확인한다.

| Case | 수치 기대값 | 근거·초안에서 확인할 점 |
| --- | --- | --- |
| `null-spike-missing-context` | 1% → 21%, 증가 20%p, 탐지 기준 10%p. 상대 증가율은 2000%. | Profile만 주어졌다. 원인·dbt 검사 완료를 단정하지 않아야 한다. 원천 점검은 이미 초안에 있고 backfill 제안은 없다. |
| `null-spike-zero-baseline` | 0% → 12%, 증가 12%p, 탐지 기준 5%p. 상대 증가율은 정의되지 않는다. | 기준값 0으로 나누거나 임의의 상대 증가율을 만들지 않아야 한다. |
| `null-spike-supplied-context-backfill` | 1% → 21%, 증가 20%p, 탐지 기준 10%p. | Metadata·관계·실패한 not-null 검사 자료가 있다. 원인은 여전히 미확정이며 backfill은 원인 확인·사람 승인을 전제로 필요성·범위를 검토하자는 초안이다. |

`delta=0.19999999999999998`은 입력의 부동소수점 값을 보존한 표현이다. 설명에서 20%p로 읽을 수 있다. 20%p 증가, baseline 대비 2000% 증가와 탐지 기준 10%p를 서로 섞지 않는지 확인한다.

1. **근거 검토:** 관측 사실·추정·누락 정보를 구분하는가? 주어지지 않은 원인이나 검증 완료를 만들지 않는가?
1. **초안 비판:** 실제 초안의 조치를 읽었는가? 이미 있는 원천 점검을 새 제안처럼 반복하거나 없는 backfill을 전제하지 않는가?
1. **종합:** 앞선 오류를 그대로 반복하지 않는가? 무엇부터 확인하며 결과에 따라 다음 판단이 어떻게 달라지는가?
1. **공통:** 설명은 한국어인가? 근거 ID·대상 컬럼과 원본 수치를 보존하는가? 실행·승인이 이미 이뤄진 것처럼 주장하지 않는가?

“원인을 확인하라”에서 멈추는지, 원천에도 결측이 늘었을 때와 원천은 온전할 때의 조사 순서를 구별하는지 살핀다. 이 설명용 예문을 모델에게 정답으로 주거나 실제 응답처럼 채점하지 않는다.

## Score And Decide

[rubric_v1](../../src/hmda_reliability/review_ai/evaluation/value.py)은 다음 다섯 항목을 **정해진 순서로 각각 0–2점과 근거**로 기록한다. 아래 설명은 검토를 돕는 채점 안내다. 합계나 테스트 통과가 사람의 결정을 자동으로 만들지 않는다.

| Criterion | 0 | 1 | 2 |
| --- | --- | --- | --- |
| `added_value` | 입력·초안 반복에 그친다. | 유용한 누락이나 관찰을 하나 짚는다. | 사례에 맞는 추가 분석이 다음 판단을 바꾼다. |
| `actionability` | 막연한 확인 요청이다. | 확인 대상을 특정한다. | 확인 방법과 결과별 다음 행동을 연결한다. |
| `evidence_awareness` | 없는 근거·원인을 단정한다. | 제공 근거와 한계를 인정한다. | 실제 근거를 활용하고 부족한 근거를 구체적으로 구분한다. |
| `uncertainty_handling` | 미확정 내용을 사실로 쓴다. | 불확실하다고 표시한다. | 확인된 사실·가설과 판단에 미치는 영향을 구별한다. |
| `prioritization` | 순서 없는 나열이다. | 먼저 볼 항목을 정한다. | 우선순위의 이유와 확인 결과에 따른 분기를 설명한다. |

숫자·근거 오류를 발견하면 해당 단계·문장과 올바른 근거를 함께 기록한다. 높은 총점으로 사실 오류를 숨기지 않는다. 출력 실패나 평가 자료 누락이면 품질 판단을 보류한다.

비교 가능한 baseline/candidate가 있으면 [비교 함수](../../src/hmda_reliability/review_ai/evaluation/value.py)에 같은 case/version·revision·facts와 정확한 workflow·output digest를 연결하고 사람이 `accept`·`reject`·`no_change`를 결정한다. 비교 조건이 맞지 않으면 blocked로 남긴다. Baseline이 없으면 단일 출력의 평가만 기록하고 개선·비교 채택을 주장하지 않는다. 과거 버전을 복원하거나 revision·ID를 임의 변경해 비교 조건을 맞추지 않는다.

## Review Record

다음 양식을 **사례·실행별로 복사해 별도의 검토 결과에 작성**한다. 빈 점수와 판단은 미검토 상태다. 원문 전체나 credential을 Git에 붙여 넣지 않고 로컬 경로·digest와 판단에 필요한 짧은 근거만 연결한다.

```text
Reviewer / reviewed_at:
Case ID / case_version:
Project revision:
Workflow ID / status / failure_code:
Model / active context / Thinking / execution settings:
Workflow path / output path / output digest:
Stage response paths:
Physical attempts / elapsed time / usage if available:

added_value:          score=  rationale=
actionability:       score=  rationale=
evidence_awareness:   score=  rationale=
uncertainty_handling: score=  rationale=
prioritization:      score=  rationale=

Numeric / evidence / draft / Korean-language findings:
Comparison baseline workflow / digest, if available:
Human decision and rationale, or reason to defer:
Required correction / next action:
```

문서 결과에는 성공뿐 아니라 실패·제외한 실행과 이유도 남긴다. 실제 평가를 마친 뒤 PR 검토 여부를 판단하며, 품질 판단과 GitHub의 Ready 전환·승인·병합 결정은 별개다.

## Run All Three Cases

<details>
<summary>선택 실행 예제: 합성 입력 3건을 현재 모델에 전달</summary>

아래 명령은 **실제로 모델을 호출**한다. 세 사례를 각 한 번, 성공 시 총 아홉 단계 호출하며 retry를 설정하면 더 늘어날 수 있다. Workflow 예산 1,200초는 사례별 예산이다. CLI 연결을 확인한 뒤 반복 횟수·실행 조건을 정하고 사용한다. 이 문서를 작성하면서 이 명령의 실제 모델 실행은 수행하지 않았다.

Repository root에서 실행한다. `.env`의 provider·한도·예산을 읽고 깨끗한 실제 HEAD를 revision으로 사용한다. Fixture의 revision 표식과 환경의 수동 revision 표식은 사용하지 않는다. Stdout에는 사례·상태·경로만, stderr에는 단계·대기 진행을 출력하며 원문은 로컬 artifact에서 읽는다.

```bash
uv run --env-file .env python - <<'PY'
import json
import os
import subprocess
from pathlib import Path

from hmda_reliability.review_ai import review_null_spike
from hmda_reliability.review_ai.contracts import AgenticReviewInput
from hmda_reliability.review_ai.evaluation.progress import LiveProgressReporter
from hmda_reliability.review_ai.settings import ReviewAISettings
from hmda_reliability.review_ai.staged.settings import StagedExecutionSettings
from hmda_reliability.runtime_ai import RuntimeAISettings

prefix = "HMDA_AGENTIC_REVIEW_"
if os.environ.get(prefix + "LIVE", "").strip().lower() not in {"1", "true", "yes", "on"}:
    raise SystemExit("HMDA_AGENTIC_REVIEW_LIVE=true로 명시한 뒤 실행하세요.")
git_env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
if subprocess.check_output(
    ["git", "status", "--porcelain", "--untracked-files=no"], text=True, env=git_env
).strip():
    raise SystemExit("추적 파일을 먼저 커밋하고 깨끗한 HEAD에서 실행하세요.")
revision = subprocess.check_output(
    ["git", "rev-parse", "HEAD"], text=True, env=git_env
).strip()

try:
    settings = RuntimeAISettings(
        base_url=os.environ[prefix + "BASE_URL"],
        api_key=os.environ[prefix + "API_KEY"],
        model=os.environ[prefix + "MODEL"],
        timeout_seconds=float(os.environ.get(prefix + "TIMEOUT_SECONDS", "30")),
        connect_timeout_seconds=float(os.environ.get(prefix + "CONNECT_TIMEOUT_SECONDS", "10")),
        read_timeout_seconds=float(os.environ.get(
            prefix + "READ_TIMEOUT_SECONDS", os.environ.get(prefix + "TIMEOUT_SECONDS", "300")
        )),
        max_retries=int(os.environ.get(prefix + "MAX_RETRIES", "0")),
        max_output_tokens=int(os.environ.get(prefix + "MAX_OUTPUT_TOKENS", "1024")),
        max_output_bytes=int(os.environ.get(prefix + "MAX_OUTPUT_BYTES", "32768")),
    )
    limits = ReviewAISettings(
        max_prompt_bytes=int(os.environ.get(prefix + "MAX_PROMPT_BYTES", "65536"))
    )
    budgets = StagedExecutionSettings(
        stage_budget_seconds=float(os.environ.get(prefix + "STAGE_BUDGET_SECONDS", "360")),
        workflow_budget_seconds=float(os.environ.get(prefix + "WORKFLOW_BUDGET_SECONDS", "1200")),
    )
except (KeyError, ValueError):
    raise SystemExit("모델 연결 정보와 숫자 설정을 확인하세요.") from None
root = Path(os.environ.get("HMDA_RELIABILITY_ARTIFACTS_DIR", ".local/artifacts"))
corpus = json.loads(Path(
    "tests/review_ai/evaluation/fixtures/output_quality_staged_v1.json"
).read_text(encoding="utf-8"))

failed = False
for case in corpus["cases"]:
    material = AgenticReviewInput.model_validate(
        case["review_input"] | {"project_revision": revision}
    )
    with LiveProgressReporter() as progress:
        result = review_null_spike(
            incident=material.incident, evidence=material.evidence, draft=material.draft,
            project_revision=revision, settings=settings, review_settings=limits,
            execution_settings=budgets, artifact_root=root, on_progress=progress,
        )
    print(json.dumps({
        "case_id": case["case_id"], "case_version": case["case_version"],
        "result": result.model_dump(mode="json", exclude={"output"}),
    }, ensure_ascii=False))
    failed |= result.status != "completed"

raise SystemExit(int(failed))
PY
```

각 사례는 별도 workflow다. 한 사례가 typed failure를 반환해도 다른 사례를 계속 기록하고, 하나라도 수집에 실패하면 종료 코드 1을 반환한다. 각 `result.status`, 실패 코드와 경로를 확인한다. 모델에 전달되는 사례는 `review_input`의 bounded projection이며 oracle·합성 control·이 안내서는 주입하지 않는다.

</details>
