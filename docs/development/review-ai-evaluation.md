---
title: "Review AI Evaluation"
description: "현재 단계별 검토의 offline 검사, 실제 실행, 실패 조사와 사람 평가 절차를 안내합니다."
categories:
  - software-engineering
tags:
  - evaluation
  - llmops
  - review-ai
  - testing
---

# Review AI Evaluation

Review AI의 실행 기록과 실제 답변을 확인하고 사람이 검토 가치를 평가할 때 사용한다. 일반 검증 명령은 [Testing Guide](testing.md), 책임과 권한 경계는 [Review AI](../domains/review-ai.md), 정본 요구사항은 [reliability-agentic-review](../../openspec/specs/reliability-agentic-review/spec.md)를 따른다.

## Offline Suite

기본 suite는 fake transport와 temporary artifact root를 사용하며 실제 provider를 호출하지 않는다.

```bash
uv run pytest tests/review_ai tests/runtime_ai
```

프롬프트 전달·입력 경계·원문 보존·코드 JSON 조립·예산·실패 기록과 다섯 human rubric 항목을 검증한다. 합성 출력과 점수 fixture는 계약 검사용이며 실제 모델 품질이나 사람 평가를 대신하지 않는다.

## Live Provider Proof

PR을 시험할 때는 해당 PR checkout의 repository root에서 실행한다. 이전 revision의 별도 `main` checkout에서 같은 환경 파일로 실행해도 PR 구현을 사용하지 않는다.

[`.env.example`](../../.env.example)을 참고해 로컬 환경에 `HMDA_AGENTIC_REVIEW_LIVE=true`와 비어 있지 않은 base URL·API key·model을 설정한다. 자격 증명은 기록이나 로그에 복사하지 않는다. 현재 프롬프트 하나만 실행하며 모드나 version을 선택하지 않는다.

```bash
uv run --env-file .env python -m hmda_reliability.review_ai.evaluation.live
```

이 [패키지 진입점](../../src/hmda_reliability/review_ai/evaluation/live.py)은 실제 제공자 호출부터 원문 저장·collection 조립·출처 재검증까지 확인하는 통합 검증 도구다. 고정된 합성 사례 한 건을 실행하며 아래 품질 corpus 세 건을 순회하지 않는다. 실제 답변을 사람이 평가할 자료를 만들지만 품질 점수나 승인 판단은 생성하지 않는다.

`HMDA_AGENTIC_REVIEW_PROJECT_REVISION=auto`는 현재 Git HEAD를 사용하고 clean tracked tree를 요구한다. 개발 중에는 명시적인 로컬 revision 표식을 사용할 수 있지만 clean commit의 품질 증거로 취급하지 않는다.

### Progress Output

stderr에는 workflow와 단계의 시작·종료를 표시하고, provider 호출을 기다리는 동안 5초 간격으로 대기 로그를 표시한다. 현재 실행은 `가상 사례로 실제 모델 통합 검증 시작 (staged-v1)`로 식별한다. stdout에는 원문을 제외한 결과 JSON을 출력하므로 진행 로그와 분리해 수집할 수 있다.

대기 로그의 단계·전체 경과시간은 로컬 실행 시계를 기준으로 측정한 값이다. Provider 내부 retry·backoff도 대기에 포함될 수 있다. 모델의 토큰 생성량·진행률이나 서버 내부 상태를 관측한 값이 아니다. 로그가 계속 출력돼도 모델 응답이나 완료를 보장하지 않으며 timeout·실행 예산을 연장하지 않는다. 원문·credential·제공자 예외 본문은 진행 로그에 넣지 않는다.

### Staged Text Review

일반 API [review_null_spike()](../../src/hmda_reliability/review_ai/service.py)와 CLI는 같은 사례에 근거 검토 → 초안 비판 → 종합을 요청한다. 모델은 한국어 일반 텍스트로 답하도록 지시받고, 코드가 원입력 식별자·수치와 세 원문을 [StagedReviewOutput](../../src/hmda_reliability/review_ai/staged/contracts.py) JSON으로 조립한다.

`status=completed`는 수집·저장 완료이며 문장의 사실성·검토 가치·사람 승인이 아니다. 콘솔에는 원문 대신 상태와 다음 경로를 출력한다.

| Result field | Content |
| --- | --- |
| `output_path` | `agentic-review/staged/<workflow_id>/output.json`: 코드가 직렬화한 facts와 단계별 원문 |
| `workflow_path` | 같은 디렉터리의 `workflow.json`: 원입력·설정·revision·단계 기록과 최종 digest |
| `stages[].response_path` | `agentic-review/responses/<workflow_id>-<stage_id>.txt`: Runtime이 반환한 exact 원문 |
| `stages[].record_path` | 단계별 원문 없는 checkpoint |

원문 파일은 UTF-8 공백·개행을 그대로 보존한다. Raw는 모델이 반환한 단계 텍스트이고 collection은 코드 생성 JSON이다. 전체 HTTP 응답이나 내부 추론 내용을 보존한다는 뜻이 아니다. Runtime이 본문을 반환하기 전에 차단한 실패에는 원문 파일이 없다.

각 호출에는 원래 canonical input과 완료된 이전 답변을 유지하고 누적 메시지 전체의 byte 한도를 검사한다. 물리 호출 상한은 `3 * (MAX_RETRIES + 1)`이며 모델 수정 대화는 추가하지 않는다. Token context와 byte cap은 다른 한도다. Timeout·단계·전체 예산과 측정 범위는 [운영 안내](review-ai-prompts.md#timeouts-and-execution-budgets)를 따른다.

### Diagnose A Failed Stage

실패하면 workflow의 `failure_code`, 단계 상태·시도 횟수·종료 이유·원문 경로를 함께 확인한다. 실패 전에 완료된 단계와 반환된 실패 응답은 보존하고 이후 단계는 호출하지 않는다.

| Evidence | Meaning / next action |
| --- | --- |
| `provider_timeout` / `provider_connection_error` | 읽기·연결 설정과 서버 상태를 구분해 확인한다. 본문이 반환되지 않으면 raw가 없다. |
| `stage_budget_exhausted` / `workflow_budget_exhausted` | 후속 실행 또는 응답 채택 예산이 소진됐다. 늦게 반환된 bounded raw는 보존한다. |
| `stage_response_empty` / `stage_response_incomplete` | 빈/공백 응답 또는 알려진 length·filter·tool 종료다. 저장된 본문과 종료 이유를 확인한다. |
| `response_too_large` / `prompt_too_large` | 응답 또는 누적 입력 상한 초과다. Byte 한도와 실제 모델 context를 따로 확인한다. |
| `provenance_failed` | 원문·checkpoint·collection·manifest 중 어떤 저장이 실패했는지 코드와 남은 경로를 확인한다. |

최종 collection 저장 중 예산이 끝나면 이미 생성한 output 경로·digest는 진단용으로 남지만 `completed`로 채택하지 않는다. 저장된 경로가 있다는 사실만으로 성공을 판단하지 않는다. 예산은 진행 중 호출의 강제 종료 보장이 아니며 제한을 늘린 것만으로 품질 문제가 해결됐다고 판단하지 않는다.

### Output Quality Cases

[output_quality_staged_v1.json](../../tests/review_ai/evaluation/fixtures/output_quality_staged_v1.json)은 합성 입력·독립 oracle·합성 단계 답변을 담는다. Oracle와 controls는 모델에게 주는 정답이나 실제 모델 응답이 아니다.

| Case | Independent numeric oracle | Context / draft |
| --- | --- | --- |
| 정보 부족 | 1% → 21%, 증가 20%p, 기준 10%p, 상대 증가율 2000% | Profile만 제공, backfill 없음 |
| 기준값 0 | 0% → 12%, 증가 12%p, 기준 5%p, 상대 증가율 정의 불가 | Profile만 제공, backfill 없음 |
| 정보 추가 | 1% → 21%, 증가 20%p, 기준 10%p | metadata/catalog/dbt 근거와 조건부 backfill 제안; 원인은 미확정 |

잘못된 수치·근거 없는 원인·초안 반복 같은 합성 출력도 collection 구조에는 맞을 수 있다. 코드가 prose를 의미적으로 판정하거나 수치를 교정하지 않는다. 사람이 실제 제공 근거와 비교해 판단한다.

### Baseline and Candidate Comparison

현재 [사람 평가 계약](../../src/hmda_reliability/review_ai/evaluation/value.py)은 `StagedReviewOutput`을 대상으로 한다. 점수와 decision은 사람이 제공하며 helper는 연결·형식·일관성만 검증한다.

1. 호출 전에 사례, 실제 revision, 모델·양자화, active context·Thinking, 출력 상한·timeout·retry·전체 예산과 반복 횟수를 정한다. 모든 시도와 실패·exclusion을 기록한다.
1. 각 실행의 workflow ID, 실제 revision, 상태·failure, prompt/output digest, 실제 호출 수·usage·시간을 연결한다. 원문과 원입력은 로컬 artifact에서 확인한다. 성공한 단계만 골라 전체 성공으로 집계하지 않는다.
1. 세 원문을 독립 oracle와 실제 evidence/draft에 대조한다. 비율·단위·기준값 0, 원인·검증 완료의 근거, 실제 초안에 없는 조치 비판, 앞선 답변의 오류 반복을 확인한다.
1. 사람이 `added_value`, `actionability`, `evidence_awareness`, `uncertainty_handling`, `prioritization` 순서로 각각 0–2점과 rationale을 작성한다. `ReviewValueAssessment`에는 case/rubric/revision/workflow와 exact output digest를 연결한다.
1. `compare_review_value()`에는 같은 사례·평가 기준·revision·facts의 baseline과 candidate 및 사람의 `accept`, `reject`, `no_change` 결정을 제공한다. 조건이 다르면 `blocked`이며 실제 조건을 맞추려고 식별자를 임의 변경하지 않는다.
1. 실패율·정확성·utility와 전체 비용을 함께 보고한다. 사람 평가가 없으면 미검증이고 offline tests·collection 완료만으로 개선을 주장하지 않는다.

동일 입력·설정·실행 조건에서 현재 프롬프트의 변경 영향을 평가한다. 과거 기록은 당시 revision의 자료로 구분하며 현재 성공으로 재해석하거나 원문·digest를 다시 쓰지 않는다. 외부 전송과 자동 의미 채점은 이 실행 절차에 포함하지 않는다.

## Related Guides

- [Prompt Composition](review-ai-prompts.md): 현재 모듈·조립·대화 이력·시간 예산
- [Testing Guide](testing.md): 일반 pytest 선택과 검사 결과 해석
- [Review AI](../domains/review-ai.md): 도메인 책임과 권한 경계
- [Runtime AI](../domains/runtime-ai.md): provider 설정과 전송 경계
