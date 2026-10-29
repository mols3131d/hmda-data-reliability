---
title: "Review AI: Evidence-Bound Advisory Review"
description: "근거 범위 안의 단계별 텍스트 검토, 코드 JSON 취합과 사람 평가를 소유하는 도메인입니다."
categories:
  - reliability
  - artificial-intelligence
tags:
  - ai-delegation
  - deterministic-validation
  - evidence-first
  - provenance
---

# Review AI: Evidence-Bound Advisory Review

**Review AI는 Reliability truth를 바꾸지 않고 제공된 근거 안에서 검토를 돕는다.** 현재 한국어 단계별 프롬프트로 일반 텍스트를 요청하고 코드가 결과 JSON을 만든다. 실행·입력·collection 구조와 provenance는 코드가 검증하며, 설명문의 사실성과 효용은 사람이 평가한다.

## Scope

| In scope | Out of scope |
| --- | --- |
| 불변 입력, bounded context와 현재 프롬프트 | incident detection·recovery 정책 |
| 고정된 세 단계의 텍스트 수집과 코드 JSON 취합 | provider SDK·credential 관리 |
| 입력·collection 구조 검증과 로컬 provenance | approval·mutation authority |
| 사람이 제공한 utility 평가와 비교 계약 | 자동 의미 채점·외부 관측 전송 |

실행 요구사항은 [reliability-agentic-review](../../openspec/specs/reliability-agentic-review/spec.md), 프롬프트 작성·변경은 [review-ai-prompt-engineering](../../openspec/specs/review-ai-prompt-engineering/spec.md) Spec이 소유한다. Source는 구현을, tests는 실행 가능한 기대를 제공한다. Passing evidence는 실제로 검사한 revision과 command에 연결한다.

## Dependency Boundary

`review_ai`는 Reliability의 Incident·Evidence·RemediationDraft를 받고 provider 호출 mechanics를 `runtime_ai`에 위임한다. Source 의존 방향은 `review_ai -> reliability`, `review_ai -> runtime_ai`다. Reliability는 Review AI를 import하지 않고 Runtime AI는 도메인 판단을 소유하지 않는다.

## Review Boundary

일반 API [review_null_spike()](../../src/hmda_reliability/review_ai/service.py)와 CLI는 [같은 단계 실행](../../src/hmda_reliability/review_ai/staged/service.py)을 사용한다. 모드나 프롬프트 version을 선택하지 않는다. 같은 canonical input에서 근거 검토 → 초안 비판 → 종합을 진행하며, 완료된 이전 답변은 assistant 자료로만 다음 요청에 포함한다.

[AgenticReviewInput](../../src/hmda_reliability/review_ai/contracts.py)은 Incident·Evidence·Draft를 깊게 복사하고 식별자·근거 참조·canonical target과 수치의 입력 일관성을 확인한다. [Bounded context](../../src/hmda_reliability/review_ai/context.py)는 관련 근거의 제한된 projection과 missing/unconfirmed gap을 제공한다. 사례 데이터와 이전 답변이 system 지시나 단계를 선택하지 않는다.

모델에는 한국어 일반 텍스트를 요청한다. 코드가 원입력 식별자·수치와 고정 순서의 세 원문을 [StagedReviewOutput](../../src/hmda_reliability/review_ai/staged/contracts.py)으로 직렬화한다. Prose에서 finding·priority·근거 참조를 추측하거나 설명문의 잘못된 수치를 자동 교정하지 않는다. `completed`는 수집·저장 완료이며 사실성·검토 가치·사람 승인을 의미하지 않는다.

빈/공백 답변, 알려진 length·filter·tool 종료, provider·저장 실패와 한도 초과는 후속 단계를 멈춘다. 누적 입력 byte, per-call 출력 cap·timeout·retry와 단계·전체 시간 예산을 적용한다. 시간 예산은 진행 중 호출의 강제 취소가 아니라 후속 시작·결과 채택의 경계다.

## Provenance

각 단계의 exact UTF-8 텍스트는 검증 전에 로컬 raw 파일로 저장하고 `stages[].response_path`로 연결한다. 공백·개행을 보존하며 실패 시 이미 저장한 raw와 checkpoint를 덮어쓰지 않는다. Runtime이 본문을 반환하기 전에 실패하면 원문 파일은 없다.

원문 없는 단계 checkpoint와 workflow manifest에는 canonical input·설정·revision·요청/응답 digest·상태·시도 횟수·usage·시간과 최종 output 경로·digest를 기록한다. Credential·provider exception 원문·자동 raw 로그는 metadata나 콘솔에 넣지 않는다. 코드 생성 collection과 모델 원문은 다른 출처다.

파일은 bounded create-only atomic private 저장을 사용한다. Identity 충돌은 호출 전에 거부하고 저장 실패는 성공으로 반환하지 않는다. 늦게 생성된 collection 경로가 진단용으로 남아도 `completed`를 뜻하지 않는다. 실제 모델 완료나 품질은 테스트 fixture와 구별한다.

## Human Evaluation

[rubric_v1](../../src/hmda_reliability/review_ai/evaluation/value.py)은 현재 `StagedReviewOutput`과 exact output digest·workflow·revision·case를 연결한다. 사람이 added_value·actionability·evidence_awareness·uncertainty_handling·prioritization에 각각 점수와 rationale을 제공하고 비교 결정도 직접 내린다.

평가 helper는 형식·대상·합계·비교 조건을 검증하며 판단을 대신하지 않는다. 합성 positive/negative 출력과 점수는 계약 테스트용이다. 수집 완료·offline 검사 통과는 사람 평가나 실제 효용을 증명하지 않는다. 실행과 원문 확인·평가 절차는 [Evaluation Guide](../development/review-ai-evaluation.md)를 따른다.

## Package Root API

[공개 API](../../src/hmda_reliability/review_ai/__init__.py)는 현재 실행과 사람 평가에 필요한 surface를 제공한다.

- `AgenticReviewInput`, `BoundedReviewContext`, `build_bounded_review_context()`
- `review_null_spike()`와 같은 실행의 명시 이름 `review_null_spike_staged()`
- `StageAnswer`, `StagedExecutionSettings`, `StagedReviewOutput`, `StagedReviewResult`
- `RUBRIC_V1`, `HumanDecision`, `ReviewValueAssessment`, `ReviewValueComparisonEvidence`, `compare_review_value()`

프롬프트 렌더링, provenance 저장소와 오류 계약은 owning module에서 확인한다. 두 번째 실제 consumer의 요구 없이 package root를 넓히지 않는다.

## Safety Boundaries

- 모델 출력은 승인·복구·데이터 변경 권한이 아니다.
- 입력 근거와 이전 모델 답변은 지시가 아닌 검토 자료다.
- 코드가 facts를 복사해도 설명문의 사실성을 검증한 것은 아니다.
- 최초 입력 거부는 provider를 호출하지 않고, 후속 단계 거부는 이전 raw와 checkpoint를 보존한다.
- 품질과 실패 격리의 실제 근거 없이 AI 권한을 확대하지 않는다.

## Contracts And Evidence

- [Canonical capability](../../openspec/specs/reliability-agentic-review/spec.md)
- [Current implementation](../../src/hmda_reliability/review_ai/)
- [Executable specification](../../tests/review_ai/)

## Reading Order

1. 정본 Spec에서 요구사항을 확인한다.
1. [공개 진입점](../../src/hmda_reliability/review_ai/__init__.py), [입력 계약](../../src/hmda_reliability/review_ai/contracts.py), [context](../../src/hmda_reliability/review_ai/context.py)를 읽는다.
1. [현재 프롬프트 조립](../../src/hmda_reliability/review_ai/staged/prompt.py)과 [단계 실행](../../src/hmda_reliability/review_ai/staged/service.py), [저장소](../../src/hmda_reliability/review_ai/staged/store.py)를 확인한다.
1. [사람 평가 계약](../../src/hmda_reliability/review_ai/evaluation/value.py)을 확인한다.
1. Provider mechanics는 [Runtime AI](runtime-ai.md)를 따른다.
