---
type: review
title: Review AI Test Design Review
description: Review AI의 입력·prompt·service·validator·provenance·evaluation 테스트와 실제 provider 연결 공백을 검토합니다.
---

# Review AI Test Design Review

> [!NOTE]
> 실제 validation·저장·compatibility oracle은 강하다. 개별 evidence 크기 오류는 public 결과로 변환되지 않으며, 두 service 연결 회귀가 기존 테스트를 통과함을 격리 실험으로 확인했다.

- **Target**: Review AI domain과 evaluation 하위 패키지.
- **Revision**: `3ab899100fc0b35e23d464bd761f3b144a978ae7`.
- **Scope**: test 12개·support 3개 전체를 두 관점 독립 검토. Source·Spec은 관련 계약과 후보 경로를 대조했다.

## Findings

| ID | Severity | Finding | Action |
| --- | --- | --- | --- |
| AI1 | Major | 개별 evidence facts 한도 초과가 raw ValidationError로 노출됨 | 정상 referenced input의 typed preflight 거부 검사 |
| AI2 | Minor | 실제 provider 메시지를 빼도 저장 provenance test가 통과함 | service provider 입력 capture와 record replay 비교 |
| AI3 | Minor | prompt에서 제외된 evidence 인용의 거부 연결을 놓침 | 작은 evidence 9개와 제외 ID 응답으로 검증 |
| AI4 | Minor | 균일한 rubric 점수가 criterion 귀속 오류를 숨김 | [Evaluation F1](evaluation.md#f1--minor-heterogeneous-score-attribution) |

AI1은 현재 동작의 재현이다. AI2·AI3은 현재 구현은 정상이며 격리 복사본의 잘못된 구현이 통과하는 반례다. AI4는 정적 oracle 공백이다. 전부 후속 제안이며 이번 보고에서 source·test를 수정하지 않았다.

## Subdomain Assessment

| Area | Scenario And Independent Oracle | Boundary And Limit |
| --- | --- | --- |
| Contracts/settings | 고정 facts·identity, closed output·typed result, nested input mutation, 명시 설정 | 실제 모델 validation; 외부 권한 부여 없음 |
| Bounded context | 고정 ID/facts/provenance, missing/unconfirmed 구분, count/bytes, canonical target 우선 | 전체 context overflow와 개별 evidence overflow는 다른 분기 |
| Prompt | exact allowlist·raw payload 배제·system/user 분리·replay | 반복 equality만으로 모든 digest 민감도를 증명하지 않음 |
| Service/validator | typed failure·실제 store·output 비노출·고정 violation 순서 | provider 응답은 fake; 실제 전달 tuple 관측은 AI2 |
| Evidence store | 실제 JSON I/O·create-only·동시 충돌·legacy load·fsync rollback | round trip 외의 경로·권한·기존 record 보존도 확인 |
| Public/import | 고정 export set·AST import 방향 | 모든 dynamic import의 부재까지 증명하지 않음 |
| Live harness | 기본 비활성·explicit settings·revision 실패·verified provenance | reviewer/subprocess는 통제됨; 실제 model 호출 증거 아님 |
| Evaluation | static golden·score 비교·Langfuse projection | [Evaluation 하위 리뷰](evaluation.md); 실제 AI 품질은 범위 밖 |

근거 파일은 [contracts](../../../../tests/review_ai/test_contracts.py), [context](../../../../tests/review_ai/test_context.py), [prompt/provider](../../../../tests/review_ai/test_prompt_provider.py), [service](../../../../tests/review_ai/test_service.py), [validator](../../../../tests/review_ai/test_validator.py), [store](../../../../tests/review_ai/test_evidence_store.py), [public surface](../../../../tests/review_ai/test_public_surface.py), [dependency](../../../../tests/review_ai/test_dependency_boundaries.py), [live harness](../../../../tests/review_ai/test_live_harness.py), [settings](../../../../tests/review_ai/test_settings.py)다.

### AI1 — Major: Per-Evidence Preflight Failure

#### Locations: AI1

- [test_service.py](../../../../tests/review_ai/test_service.py)
  - 303행 이후는 여러 evidence의 전체 context overflow를 검사한다.
- [context.py](../../../../src/hmda_reliability/review_ai/context.py)
  - `BoundedReviewEvidence._validate_fact_size`, `_project_evidence`.
- [service.py](../../../../src/hmda_reliability/review_ai/service.py)
  - prompt/context 전용 예외만 typed preflight 결과로 변환한다.

#### Evidence: AI1

정상 referenced metadata의 허용 key 5개에 각각 999 UTF-8 bytes를 넣은 [D1 probe](../validation.md#d1-per-evidence-preflight-limit)에서 `AgenticReviewInput`까지 정상 검증됐다. Public service는 개별 facts의 4,096-byte 한도에서 raw `ValidationError`를 노출했고 provider/store는 0회였다. 개별 값과 전체 context 한도 사이에 별도 실패 지점이 있다.

#### Impact: AI1

Caller가 정해진 `input_rejected` 결과로 처리할 수 없다. 전송·mutation에 도달했다는 문제가 아니라 typed 입력 거부 계약의 누락이다.

#### Action: AI1

유효한 references를 유지한 개별 evidence overflow에 typed rejection과 provider/store 미호출을 요구한다. 알려진 크기 초과를 domain error로 표현하되 무관한 `ValueError`를 전파하는 기존 test는 보존한다.

### AI2 — Minor: Provider And Provenance Handoff

#### Locations: AI2

- [test_service.py](../../../../tests/review_ai/test_service.py)
  - `FakeProvider.invoke`는 messages를 관측하지 않는다.
  - 180행의 provenance test는 저장된 필터링·refs를 검사한다.
- [test_prompt_provider.py](../../../../tests/review_ai/test_prompt_provider.py)
  - adapter 직접 호출은 service handoff를 통과하지 않는다.

#### Evidence: AI2

격리 복사본에서 `invoke(rendered.messages[:1])`로 user message를 빼도 관련 4module의 기존 **58개가 통과**했다. 실제 tuple을 capture하는 witness는 baseline 통과, mutant 실패였다. [D2 실험](../validation.md#d2-service-handoff-negative-controls)의 import guard·원본 hash 보존을 확인했다. 독립 reviewer는 정적으로 도출했고 추가 mutation은 caller가 실행했다.

#### Impact: AI2

실제로 전달한 입력과 다른 정상 입력의 provenance를 기록하는 회귀를 놓칠 수 있다. 현재 service는 같은 rendered 값을 사용해 정상이다.

#### Action: AI2

Provider 대역에서 actual messages를 capture하고 저장 record의 canonical projection으로 replay한 messages·digest와 비교한다.

### AI3 — Minor: Prompt-Visible Evidence Binding

#### Locations: AI3

- [service.py](../../../../src/hmda_reliability/review_ai/service.py)
  - selected evidence ID 집합을 validator에 전달한다.
- [validator.py](../../../../src/hmda_reliability/review_ai/validator.py)
  - 인자가 없으면 원래 input의 전체 evidence로 fallback한다.
- [test_validator.py](../../../../tests/review_ai/test_validator.py)
  - original input에도 없는 fabricated ID는 보호하지만 provided-but-omitted ID와 다르다.

#### Evidence: AI3

Selected allowlist 전달만 제거한 격리 mutant에서도 기존 **58개가 통과**했다. 정상 references의 작은 evidence 9개 중 8개만 prompt에 선택시키고, 빠진 ID를 인용한 응답의 거부를 요구하는 witness는 baseline 통과·mutant 실패였다. Mutant 결과는 `accepted`였다. 전체 context overflow로 미리 거부되는 다수 evidence 사례는 이 연결을 보호하지 않는다.

#### Action: AI3

동일한 작은 사례로 `validation_failed`, fabricated-evidence violation과 선택된 provenance를 확인한다. 현재 allowlist 전달을 제거하거나 input 전체 허용으로 넓히는 제안이 아니다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | 독립 full-body 검토 | Batch D 두 관점, 15파일과 source·계약 대조 |
| ✅ Pass | 현재 전체 suite | [954 passed / 2 skipped](../validation.md#test-execution), 전체 기준 |
| ❌ Fail | 정상 입력의 typed preflight containment | D1 current-source probe |
| ✅ Pass | 격리 반례 실험의 구별력 | D2 baseline 58+2 통과, 두 mutant 모두 기존 58 통과·witness 1개 실패 |
| ⚪ Not Verified | Rubric permutation mutant | 정적 분석만 수행 |

## Risks And Limits

실제 모델 리뷰의 유용성·정확성 점수·judge/tuning·외부 ingestion/UI/human proof는 평가하지 않았다. Advisory output이 권한을 부여하지 않는다는 결정론적 경계와 모델의 실제 품질은 구분한다.
