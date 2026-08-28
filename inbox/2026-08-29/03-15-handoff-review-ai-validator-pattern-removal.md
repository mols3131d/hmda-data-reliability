---
type: handoff
title: "Review AI validator 자연어 패턴 제거 검토"
description: "Review AI deterministic validator의 자연어 regex guard 제거를 검토하고 structured fact validation으로 책임을 축소하기 위한 후속 작업 handoff."
tags:
  - review-ai
  - validator
  - openspec
---

# Review AI validator 자연어 패턴 제거 검토

## 결론

`src/hmda_reliability/review_ai/validator.py`의 자연어 regex guard는 제거를 우선 검토한다.

현재 validator는 structured fact consistency와 자연어 의미 휴리스틱을 함께 소유한다. 후자는 `authority_escalation`, `forbidden_action`을 판정하기 위해 영어·한국어 표현, command pattern과 punctuation segmentation을 코드에 직접 열거한다. 이 방식은 패턴을 늘릴수록 false positive/negative와 상호작용이 커지고, deterministic validator가 작은 NLP parser처럼 확장될 위험이 있다.

권장 방향은 deterministic validator를 **구조적으로 확실하게 검증할 수 있는 사실과 Evidence consistency에 한정**하고, free-text advisory semantics를 blocking safety boundary로 취급하지 않는 것이다.

> 이 문서는 후속 설계 handoff다. PR #181의 현재 ownership refactor와 validator regression fix를 다시 변경하라는 지시가 아니다.

## 현재 상태

PR #181 head에서 `validator.py`는 다음 violation을 deterministic하게 생성한다.

- `fabricated_evidence`
- `incident_mismatch`
- `deterministic_contradiction`
- `authority_escalation`
- `forbidden_action`

이 중 앞의 세 항목은 structured input/output을 직접 비교할 수 있다. 반면 뒤의 두 항목은 다음 hard-coded natural-language policy에 의존한다.

- `_AUTHORITY_PATTERNS`
- `_FORBIDDEN_ACTION_PATTERNS`
- `_SEGMENT_SPLIT_PATTERN`
- `_review_segments()`
- `_has_authority_escalation()`
- `_has_forbidden_action()`
- `_review_text()`

`AgenticReviewValidation.policy_id`도 현재 `forbidden-action-policy-v1`로 고정되어 있고, tests는 해당 policy와 두 violation의 blocking behavior를 직접 계약한다.

## 문제

### 자연어 의미를 regex safety boundary로 다루고 있다

현재 guard는 단순 keyword 검사가 아니다. command/descriptive distinction, punctuation boundary, approval·authority 표현, 한국어와 영어 표현을 조합해 자연어 의미를 근사한다.

이 접근은 다음 특성을 가진다.

- 패턴으로 열거하지 않은 표현은 쉽게 우회한다.
- 정상적인 quote, negation, approval-condition도 false positive가 될 수 있다.
- 한 패턴을 보완하면 segmentation과 다른 패턴의 상호작용이 생긴다.
- 지원 언어와 표현이 늘수록 정책 코드와 regression corpus가 계속 커진다.
- regex 통과 여부가 실제 recovery/backfill/mutation 권한을 부여하거나 차단하는 execution boundary는 아니다.

### deterministic validator의 책임이 불명확해진다

Validator가 가장 강하게 보장할 수 있는 것은 다음과 같은 deterministic consistency다.

- output이 실제 제공된 Evidence만 참조하는가
- incident identity가 input과 같은가
- canonical target과 numeric facts가 deterministic source와 같은가

반면 아래 질문은 structured equality check가 아니라 자연어 semantic classification이다.

- 이 문장은 실행 명령인가
- 이 문장은 model-granted approval인가
- negation이나 quote의 scope가 어디까지인가
- approval-condition 뒤의 action은 command인가 description인가

이 둘을 같은 `validate_agentic_review()`에 두지 않는 방향을 우선 검토한다.

## 목표 상태

Working hypothesis는 deterministic validation을 다음 세 violation 중심으로 축소하는 것이다.

```text
fabricated_evidence
incident_mismatch
deterministic_contradiction
```

후속 설계에서 타당성이 확인되면 다음 subsystem을 제거한다.

```text
_AUTHORITY_PATTERNS
_FORBIDDEN_ACTION_PATTERNS
_SEGMENT_SPLIT_PATTERN
_review_segments()
_has_authority_escalation()
_has_forbidden_action()
_review_text()
```

그리고 `ReviewViolationCode.AUTHORITY_ESCALATION`, `ReviewViolationCode.FORBIDDEN_ACTION`, `AgenticReviewValidation.policy_id="forbidden-action-policy-v1"`의 필요성도 함께 재검토한다.

단순히 regex만 삭제하고 dead contract를 남기지 않는다.

## 안전 경계 재확인

패턴 제거 여부는 "안전을 포기할지"가 아니라 **어떤 boundary가 실제 authority를 소유하는지**를 기준으로 판단한다.

다음 가정을 코드와 spec에서 직접 검증하라.

1. `AgenticReviewOutput`은 approval, recovery 또는 mutation을 수행하는 executable field를 제공하지 않는다.
2. `review_ai`의 accepted free text 자체가 recovery/backfill/mutation 호출 권한으로 변환되지 않는다.
3. 실제 mutation path가 존재한다면 review output과 분리된 typed proposal/approval boundary를 거친다.
4. prompt는 model에게 advisory-only 역할을 명시하되, prompt adherence를 deterministic security oracle로 취급하지 않는다.
5. provenance에는 accepted output과 deterministic validation 결과를 충분히 남겨 사후 evaluation이 가능하다.

이 중 하나라도 성립하지 않으면 regex 제거 전에 실제 authority boundary부터 보강해야 한다.

## Spec 영향

이 변경은 behavior-preserving refactor가 아니다.

현재 active Agentic Review spec은 다음을 명시적으로 계약한다.

- `authority_escalation`
- `forbidden_action`
- `forbidden-action-policy-v1`
- conservative bounded regex guard
- explicit dangerous output rejection

따라서 PR #181의 `skip_specs: true` ownership migration에 조용히 섞지 않는다.

실행한다면 별도 OpenSpec Change에서 다음 원칙을 명시적으로 설계한다.

> Deterministic review validation은 structured input과 직접 비교 가능한 claims와 facts만 authoritative하게 검증한다. Free-text advisory semantics는 deterministic blocking safety boundary로 취급하지 않는다.

기존 active capability contract와 충돌하지 않도록 delta spec, design과 migration scope를 명확히 한다.

## 예상 변경 범위

설계가 승인된 뒤 implementation은 최소한 다음 surface를 함께 다룬다.

- `src/hmda_reliability/review_ai/validator.py`
- `src/hmda_reliability/review_ai/contracts.py`
- `tests/review_ai/test_validator.py`
- Agentic Review active OpenSpec contract
- `authority_escalation`, `forbidden_action`, `forbidden-action-policy-v1`을 참조하는 관련 tests/docs/provenance consumer

검색으로 실제 consumer를 먼저 확인하고, 발견되지 않은 호환성 요구를 추측해 shim을 만들지 않는다.

## 테스트 방향

패턴 subsystem을 제거한다면 regex corpus를 다른 형태로 그대로 옮기지 않는다.

남길 deterministic tests는 다음 observable contract에 집중한다.

- fabricated Evidence reference는 reject
- incident identity mismatch는 reject
- canonical target/facts contradiction은 reject
- violation은 deterministic order와 uniqueness를 유지
- valid structured advisory output은 free-text wording과 무관하게 accepted
- Evidence 안의 prompt-injection-like text는 instruction이 아니라 untrusted input data로 유지
- validation은 side effect가 없다

free-text advisory quality나 action-like language 감지는 필요하면 blocking validator가 아니라 별도 evaluation/observability concern으로 설계한다. 필요성이 입증되지 않으면 YAGNI에 따라 추가하지 않는다.

## 작업 순서

1. 현재 Agentic Review spec과 실제 authority/mutation path를 조사한다.
2. regex guard가 제거되었을 때 새로 생기는 실제 capability 또는 privilege가 있는지 확인한다.
3. structured deterministic validation만 남기는 방향의 OpenSpec Change를 작성한다.
4. contract에서 obsolete violation/policy identity를 함께 정리한다.
5. validator와 tests를 최소 구현으로 축소한다.
6. affected review/service/provenance tests와 전체 relevant test closure를 실행한다.
7. diff를 다시 읽고 자연어 semantic judge가 다른 위치에 우회적으로 재생성되지 않았는지 review한다.

## 하지 말 것

- regex를 YAML, `.env` 또는 runtime configuration으로 옮기는 것
- regex subsystem을 generic `RuleEngine`/plugin framework로 재포장하는 것
- deterministic guard를 LLM classifier로 단순 치환하는 것
- 패턴 제거와 무관한 `review_ai` / `runtime_ai` ownership 재설계
- PR #181의 behavior-preserving migration과 별도 semantic change를 암묵적으로 섞는 것

## 완료 기준

후속 작업은 다음이 모두 설명될 때 완료로 본다.

- deterministic validator가 무엇을 authoritative하게 검증하는지 한 문장으로 설명 가능하다.
- free text가 실제 mutation authority를 획득하지 못하는 이유가 코드 boundary로 확인된다.
- obsolete natural-language regex, violation code와 policy identity가 일관되게 제거되거나 명확한 이유로 유지된다.
- spec, implementation과 tests가 같은 safety model을 표현한다.
- 관련 validation이 통과하고 남은 risk가 명시되어 있다.

## References

- `src/hmda_reliability/review_ai/validator.py`
- `src/hmda_reliability/review_ai/contracts.py`
- `tests/review_ai/test_validator.py`
- `openspec/changes/reliability-agentic-review/specs/reliability-agentic-review/spec.md`
- `openspec/changes/review-ai-extract-runtime/`
