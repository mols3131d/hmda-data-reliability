---
type: plan
title: "Review AI Evaluation Subdomain Refactor"
description: "Review AI의 평가 책임을 하위 도메인으로 정리하고 utility 용어의 의미 혼선을 줄이기 위한 후속 리팩터링 계획입니다."
tags:
  - review-ai
  - evaluation
  - refactor
  - langfuse
---

# Review AI Evaluation Subdomain Refactor

## Summary

`review_ai`의 평가 책임을 top-level `evaluation` 도메인으로 승격하지 않고 **`review_ai.evaluation` 하위 도메인으로 응집**한다. 현재 `evaluation.py`와 Langfuse projection이 Review AI 실행 코드와 같은 package level에 놓여 있어 평가 계약, 비교, annotation, 외부 projection의 경계가 한눈에 드러나지 않는다.

이 리팩터링의 목표는 평가 기능의 ownership을 분명히 하고 탐색 비용을 줄이는 것이다. Reliability의 recovery/replay evaluation은 계속 `reliability`가 소유하며, 이름이 같다는 이유로 서로 다른 평가 의미론을 하나의 공통 도메인으로 합치지 않는다.

> [!IMPORTANT]
> 이 문서는 PR #248 이후의 후속 리팩터링 계획이다. PR #248의 Langfuse projection acceptance를 확대하거나 현재 구현 완료 조건을 변경하지 않는다.

## Problem

현재 `review_ai`는 다음 책임을 같은 package level에 노출한다.

- review input/output와 provider-facing contract
- bounded context와 prompt rendering
- deterministic validation과 orchestration
- invocation provenance
- human rubric과 baseline/candidate 평가
- evaluation comparison projection
- Langfuse projection, annotation validation과 optional export

특히 `evaluation.py`는 rubric, score, assessment, comparison, Markdown rendering과 output digest를 함께 소유한다. `langfuse_projection.py`도 evaluation의 rubric, score와 output digest를 직접 사용한다. 이 구조는 동작 자체보다 **어디까지가 Review AI 실행이고 어디부터가 평가인지** 이해하는 비용을 키운다.

평가 책임은 이미 독립적인 의미를 갖지만 아직 Review AI 외의 두 번째 AI consumer가 없다. 따라서 지금 top-level `hmda_reliability.evaluation`을 만드는 것은 공통화 근거보다 추상화 비용이 크다.

## Decision

### Domain Boundary

다음 경계를 목표로 한다.

```text
hmda_reliability/
├── reliability/
│   └── evaluation/
│       └── ...                  # recovery/replay evaluation; unchanged
│
└── review_ai/
    ├── contracts.py
    ├── context.py
    ├── evidence.py
    ├── prompt.py
    ├── service.py
    ├── validator.py
    └── evaluation/
        ├── __init__.py
        ├── value.py
        └── langfuse.py
```

`review_ai.evaluation`은 **Review AI output의 평가와 평가 도구 integration**만 소유한다. Review 생성, provider invocation, deterministic review validation과 provenance ownership은 기존 위치에 남긴다.

첫 리팩터링에서는 `rubric.py`, `assessment.py`, `comparison.py`처럼 작은 파일을 미리 늘리지 않는다. 현재 규모에서는 `value.py`가 rubric, assessment와 comparison의 cohesive owner가 될 수 있다. 각 책임이 독립적으로 성장할 때만 추가 분리를 검토한다.

### Responsibility Map

| Owner | Responsibility |
| --- | --- |
| `review_ai.contracts` | Review AI input/output와 provider-facing structured contract |
| `review_ai.service` | Review orchestration |
| `review_ai.validator` | Provider output에 대한 deterministic review validation |
| `review_ai.evidence` | Invocation provenance |
| `review_ai.evaluation.value` | Review value rubric, assessment, baseline/candidate comparison과 review output identity |
| `review_ai.evaluation.langfuse` | Evaluation-oriented Langfuse projection, annotation binding과 optional export |
| `reliability.evaluation` | Recovery/replay와 deterministic reliability outcome evaluation |

Langfuse는 평가 의미론의 owner가 아니다. `review_ai.evaluation.langfuse`는 Review AI evaluation contract를 외부 backend에 projection하는 adapter로만 유지한다.

## Terminology

현재 `HumanUtilityEvaluation`의 `utility`는 경제학적 효용, 일반적인 usefulness, Review AI의 추가 가치가 섞여 읽힐 수 있다. 실제 rubric은 `added_value`, `actionability`, `evidence_awareness`, `uncertainty_handling`, `prioritization`을 통해 **review가 baseline을 넘어 의사결정에 주는 가치**를 평가한다.

따라서 evaluation subdomain의 기본 용어는 **Review Value**로 정리하는 것을 권장한다.

| Current | Proposed | Note |
| --- | --- | --- |
| `UtilityRubric` | `ReviewValueRubric` | 평가 대상이 review value임을 명시 |
| `HumanUtilityEvaluation` | `ReviewValueAssessment` | 평가 대상과 artifact 역할을 명확히 함 |
| `UtilityComparisonStatus` | `ReviewValueComparisonStatus` | comparison 상태 |
| `UtilityComparisonEvidence` | `ReviewValueComparison` | baseline/candidate 비교 artifact |
| `compare_utility_evaluations()` | `compare_review_value()` | 비교 행위의 목적을 직접 표현 |
| `render_utility_comparison_markdown()` | `render_review_value_comparison_markdown()` | projection naming 정리 |
| `utility_output_digest()` | `review_output_digest()` | digest는 utility가 아니라 exact review output identity에 결합됨 |

문서 표현은 필요할 때 **human-rated review value**를 사용해 사람이 rubric을 적용한다는 평가 방식을 설명한다. 코드의 핵심 개념명에는 평가자보다 평가 대상을 우선한다.

### Terminology Boundary

`AgenticReviewUtilityContribution`과 serialized `utility_contributions`는 Review AI output contract에 속하며 evaluation-only naming이 아니다. 이 리팩터링에서 자동으로 이름을 바꾸지 않는다.

해당 이름도 `value` 계열로 바꿀 필요가 있다면 provider prompt, output schema, validator, fixtures, canonical Spec과 replay compatibility에 영향을 주는 별도 contract 변경으로 판단한다. 구조 정리와 wire contract 변경을 한 번에 섞지 않는다.

## Migration Strategy

### 1. Extract the Subdomain

`review_ai/evaluation.py`를 `review_ai/evaluation/value.py`로 이동하고 package `__init__.py`에서 의도한 evaluation surface를 export한다.

`review_ai/langfuse_projection.py`는 `review_ai/evaluation/langfuse.py`로 이동한다. child-process isolation, environment allowlist, timeout, payload size 제한과 sanitized status는 그대로 보존한다.

이 단계에서는 executable behavior와 serialized data contract를 변경하지 않는다.

### 2. Preserve or Intentionally Change the Public Surface

현재 `hmda_reliability.review_ai` package root가 evaluation type 일부를 public API로 export한다. 구조 이동만 수행하는 단계에서는 기존 root import가 깨지지 않도록 re-export를 유지한다.

`Utility*` symbol을 `ReviewValue*`로 바꾸는 변경을 같은 후속 작업에서 수행한다면 canonical Spec, domain guide와 public-surface tests를 함께 갱신한다. 외부 consumer 근거가 없다면 old/new alias를 장기간 병렬 유지하지 않는다. Compatibility alias는 실제 consumer가 요구할 때만 추가한다.

### 3. Update Internal Imports and Tests

다음 consumer를 새 ownership에 맞춘다.

- Review AI package root exports
- Langfuse projection imports
- evaluation tests
- Langfuse projection tests
- public-surface tests
- canonical Review AI Spec과 domain guide의 경로·용어

과거 Inbox artifact는 historical working evidence이므로 새 naming에 맞추기 위해 일괄 수정하지 않는다.

### 4. Keep Reliability Evaluation Separate

`src/hmda_reliability/reliability/evaluation/`은 이동하거나 공통 base로 추출하지 않는다. 두 영역은 모두 evaluation이라는 단어를 사용하지만 평가 대상, contract와 failure semantics가 다르다.

공통 evaluation infrastructure는 Review AI 외에 실제 두 번째 AI capability가 생기고 dataset/run/annotation/comparison lifecycle을 공유할 때 다시 검토한다.

## Non-Goals

- top-level `hmda_reliability.evaluation` 도메인 도입
- generic eval framework 설계
- Reliability recovery evaluation 통합
- 자동 LLM judge 도입
- rubric scoring 방식 변경
- Langfuse를 canonical evaluation store로 승격
- PR #248의 remote ingestion 또는 human annotation proof 요구 확대
- `utility_contributions` provider wire contract의 암묵적 rename
- 새로운 Tach boundary를 디렉터리 구조만을 이유로 추가

## Validation

리팩터링 완료 후 최소한 다음이 유지되어야 한다.

1. 기존 Review AI accepted/unavailable/validation-failed behavior가 변하지 않는다.
1. `rubric_v1`의 다섯 criterion, score 범위와 rationale validation이 동일하다.
1. baseline/candidate same-case 검증, output digest binding과 fail-closed comparison이 동일하다.
1. Langfuse export disabled 상태에서는 SDK import/init/external call이 발생하지 않는다.
1. Langfuse child process의 timeout, environment isolation, media upload disable과 sanitized failure semantics가 동일하다.
1. Annotation은 동일한 `invocation_id`, exact `output_digest`, `rubric_id`에 계속 결합된다.
1. `reliability.evaluation`의 public surface와 tests에는 변경이 없다.
1. package public-surface test가 의도한 export만 허용한다.
1. canonical Spec과 `docs/domains/review-ai.md`가 새 ownership과 terminology를 정확히 설명한다.

## Acceptance Criteria

- `review_ai` package root에서 실행 책임과 평가 책임의 물리적 경계가 디렉터리 구조만으로 식별된다.
- Review AI evaluation 관련 구현은 `review_ai/evaluation/`에서 찾을 수 있다.
- `reliability.evaluation`과 Review AI evaluation 사이에 불필요한 공통 abstraction이 생기지 않는다.
- 구조 이동으로 runtime behavior, serialized projection, provenance 또는 validation semantics가 달라지지 않는다.
- `utility`에서 `review value`로 용어를 바꾸는 범위와 바꾸지 않는 output contract 범위가 명시적으로 구분된다.
- 새 alias, wrapper, registry 또는 generic framework는 실제 consumer 근거 없이 추가하지 않는다.

## Suggested Work Order

1. PR #248의 현재 Langfuse projection 범위를 먼저 닫는다.
1. 별도 후속 change에서 `review_ai.evaluation` package extraction을 수행한다.
1. 구조 이동을 검증한 뒤 Review AI evaluation symbol의 `utility` → `review value` rename을 적용한다.
1. canonical Spec, domain guide와 tests를 같은 revision에서 맞춘다.
1. 이후 두 번째 AI evaluation consumer가 실제로 생길 때만 top-level evaluation domain 필요성을 재검토한다.

이 순서는 현재의 난잡함을 줄이면서도 architecture redesign이나 범용 eval abstraction을 미리 도입하지 않는 가장 작은 coherent change를 목표로 한다.
