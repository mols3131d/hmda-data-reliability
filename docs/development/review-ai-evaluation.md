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

프롬프트 전달·입력 경계·원문 보존·코드 JSON 조립·예산·실패 기록과 native 사람 annotation의 연결·완비 검사를 검증한다. 합성 출력과 점수 fixture는 계약 검사용이며 실제 모델 품질이나 사람 평가를 대신하지 않는다.

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

## Native Langfuse Experiments

선택적 [실험 진입점](../../src/hmda_reliability/review_ai/evaluation/experiment.py)은 패키지에 포함된 합성 사례 3건을 기존 검토 함수로 직렬 실행한다. 성공 시 총 아홉 단계이며 retry 설정에 따라 실제 호출 수가 늘 수 있다. Dataset의 기대값·독립 oracle은 검토자 자료이며 모델 입력이나 history에 포함하지 않는다. 실제 HMDA 적재·dbt 실행은 하지 않는다.

```bash
uv sync --extra langfuse
uv run --extra langfuse --env-file .env python -m hmda_reliability.review_ai.evaluation.experiment
```

[환경 예시](../../.env.example)에서 `HMDA_LANGFUSE_ENABLED=true`, `HMDA_AGENTIC_REVIEW_LIVE=true`와 Langfuse base URL·public/secret key를 설정한다. 기존 제공자·모델·예산 설정을 함께 사용한다. SDK 4.15.6을 사용하며 최신 SDK 문서의 v5 예제를 그대로 적용하지 않는다.

Dataset item은 case/version·사례 payload digest로 고정하고 snapshot version을 선택한다. 기존 item·점수 Config·Queue가 기대 계약과 다르면 자동 덮어쓰지 않는다. 반복할 때마다 새 run을 만든다. `project_revision=auto`의 실제 HEAD 조건은 단일 실행과 같다.

검증된 로컬 manifest·checkpoint·원문·collection만 native 사례 관측과 세 단계 generation 관측의 input/output으로 보낸다. System prompt는 digest로만 연결한다. Metadata는 식별자·상태·digest·시도 횟수·기록된 latency/usage로 제한한다. 관측은 보존된 결과를 내보낸 기록이므로 관측 생성 시각을 실제 provider 실행 시각으로 해석하지 않는다.

stderr는 단계·대기 상태를, stdout은 core 결과와 외부 제출 상태·receipt 경로를 출력한다. Receipt는 `agentic-review/experiments/<run_name>/receipt.json`에 저장된다. credential·원문·개인 절대 경로·provider 예외를 콘솔이나 원격 metadata에 넣지 않는다.

### Independent External IO Budget

`HMDA_LANGFUSE_IO_TIMEOUT_SECONDS`는 기본 30초, 허용 범위 1–300초다. SDK 시작·등록·사례 사이·최종 flush 구간마다 적용한다. 실제 검토 함수 실행 구간은 기존 provider timeout·단계·workflow 예산을 사용한다. SDK는 별도 프로세스에서 실행해 무한 flush도 종료할 수 있다.

외부 I/O가 실패해도 이미 완료된 core workflow와 로컬 원문은 남는다. `core_results`와 외부 `failure_code`를 구분해 읽는다. 외부 실패를 복구하기 위해 모델을 자동 재호출하지 않는다. 재실행하면 새 모델 실행과 새 run이 만들어진다.

대기열은 native task 종료와 flush 반환 뒤 연결한다. `queue_attachment_failed`이면 원격 반영 지연·권한·대상을 먼저 확인하고 기존 receipt의 관측을 UI에서 평가할 수 있다. 이 오류를 고치려고 모델을 다시 호출하지 않는다. 원격 반영은 SDK 반환만으로 보장되지 않는다.

| State | 확인한 범위 |
| --- | --- |
| Core `completed` | 세 단계 수집·로컬 보존 완료 |
| `submitted_unverified` | SDK 실험 함수 반환; 실제 원격 적재·UI·사람 평가 미확인 |
| `unavailable` | 외부 실행 실패·timeout; 로컬 결과는 별도 확인 |
| Check `complete` | 실제 조회한 대상 관측과 특정 검토자의 다섯 annotation이 로컬 원문에 연결되고 완비됨 |

### Baseline And Candidate Comparison

Langfuse Dataset의 experiment와 compare 화면에서 실제 입력·세 원문을 읽는다. Annotation Queue `<dataset>-rubric-v1`은 다섯 기준을 제공한다. 지정 검토자는 각 항목에 categorical `0`·`1`·`2`와 공백이 아닌 comment를 입력한다. Queue 완료 표시만으로 평가가 완비되지는 않는다.

- `added_value`: 초안 재서술을 넘어 판단에 필요한 정보를 더했는가.
- `actionability`: 다음 확인의 대상·순서·조건이 구체적인가.
- `evidence_awareness`: 실제 제공 근거와 빈틈을 구별했는가.
- `uncertainty_handling`: 모르는 원인을 단정하지 않고 확인 조건을 제시했는가.
- `prioritization`: 중요한 위험과 조사 순서를 구별했는가.

점수의 의미는 사람이 판단한다. 숫자 합계나 자동 judge로 채택 결정을 만들지 않는다. 아래 명령의 경로는 stdout에 나온 실제 receipt로 바꾼다. 검토자 ID는 서버가 기록한 `authorUserId`다. 조회에는 Langfuse opt-in과 자격 증명·로컬 artifact가 필요하며 AI 제공자 자격 증명은 필요하지 않다.

```bash
uv run --extra langfuse --env-file .env python -m hmda_reliability.review_ai.evaluation.experiment \
  --check .local/artifacts/agentic-review/experiments/<run_name>/receipt.json \
  --reviewer-id <authorUserId>
```

조회는 원격 관측 metadata와 로컬 실제 workflow·원문·output digest, Config schema, annotation source·작성자·시각·사유를 검사한다. 다섯 항목이 각각 정확히 한 번이어야 한다. 누락·중복·잘못된 범주·연결은 `incomplete` 또는 조회 실패로 남긴다. API/자동 evaluator 점수는 사람 점수를 채우지 못한다. SDK/API 조회가 된 것과 UI에서 읽고 평가한 것은 별도 증거다.

비교할 baseline이 있으면 candidate 실행 때 `--baseline <baseline-receipt>`를 지정한다. 같은 사례 payload와 Config snapshot을 사용하고 양쪽 실제 SHA·run·workflow·canonical/output digest를 보존한다. 현재 canonical input에는 revision이 포함되지 않는다. 실제 SHA는 별도 provenance다. 의도한 코드 변경의 SHA 차이를 허용하며 값이 같아 보이도록 재작성하지 않는다. 모델·context·Thinking·예산 등 비교 조건은 실행 전에 정하고 양쪽 workflow 설정과 함께 확인한다.

사람은 candidate 관측에서 별도 `review_decision` Config의 `accept`·`reject`·`no_change`와 사유를 입력한다. 이 의견은 candidate 관측의 양쪽 run/output digest에 연결된다. 조회할 때도 `--baseline <baseline-receipt>`를 함께 제공한다. Baseline의 로컬 기록과 원격 관측도 확인한다. Baseline 없이 실행하면 단일 결과 평가만 가능하며 과거 결과에 비교 연결을 소급 합성하지 않는다.

실패·누락·미평가 사례를 전체 평가에서 제외해 개선을 주장하지 않는다. 사실성·효용 판단과 GitHub의 Ready·승인·병합은 각각 사람이 결정한다. 실제 원격/UI·사람 평가가 없으면 품질은 미검증이다.

## Related Guides

- [Prompt Composition](review-ai-prompts.md): 현재 모듈·조립·대화 이력·시간 예산
- [Testing Guide](testing.md): 일반 pytest 선택과 검사 결과 해석
- [Review AI](../domains/review-ai.md): 도메인 책임과 권한 경계
- [Runtime AI](../domains/runtime-ai.md): provider 설정과 전송 경계
