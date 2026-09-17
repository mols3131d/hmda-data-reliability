---
type: brief
title: "Implement MVP Review AI Utility Proofs"
description: "Handoff brief for designing, implementing, and proving the 4 redefined MVP utility proofs for Review AI."
tags:
  - review-ai
  - mvp
  - evaluation
  - handoff
---

# Implement MVP Review AI Utility Proofs

## Context and Goal

- `main` 브랜치가 PR #243(`docs: redefine MVP around useful agentic review`, `1cff755`)으로 갱신되었습니다.
- [docs/mvp.md](../../docs/mvp.md)의 MVP 수용 기준에 기존 6대 Foundation Proofs 외에 **4대 Utility Proofs**가 필수 게이트로 추가되었습니다:
  - 단순 정형 검증(schema/facts validation) 통과를 넘어, 사람의 조사 및 복구 판단에 실질적인 가치를 제공해야 합니다.
  - 외부 자동 판사(LLM judge)나 복잡한 플랫폼에 의존하지 않고, 버전 관리형 human rubric과 통제 fixture로 재현 가능하게 평가해야 합니다.

## Required Proofs

1. **Review context proof:** 단일 incident의 최소 정형 사실뿐 아니라 판단에 필요한 주변 evidence를 선택하고, 각 evidence의 출처 및 미확인 context를 구분하는 Bounded Review Context 제공
1. **Agentic utility proof:** 단순 deterministic facts나 `RemediationDraft` 재진술을 넘어 사람의 판단을 개선하는 실질적 기여(evidence gap 식별, 조사 우선순위, 복구 초안 비판, 핵심 불확실성 명시) 생성
1. **Quality evaluation proof:** 5대 항목(added value, actionability, evidence awareness, uncertainty handling, prioritization)을 평가하는 버전 관리형 human rubric(`rubric_v1`) 및 판별 검증(positive/negative control) 체계 구축
1. **Change comparison proof:** 동일 representative case와 rubric 기준에서 baseline과 candidate를 비교 평가하고 채택 근거를 사람이 검토 가능한 evidence로 보존

## Relevant Prior Art

- [inbox/2026-09-06/15-30-discuss-ai-llmops-minimum-operational-criteria/README.md](../2026-09-06/15-30-discuss-ai-llmops-minimum-operational-criteria/README.md)의 합의 기준을 직접 계승합니다:
  - 평가 대상 output 생성 전에 버전 고정된 case/rubric 사전 확정 (precommit)
  - Rubric이 bounded negative control을 `FAIL`, compliant control을 `PASS`로 구별하는 비자명성 판별력 증명
  - Baseline과 candidate 간 same-rubric 비교 및 human decision 보존

## Execution Plan

### Step 1: Branch and OpenSpec Change Setup

1. 작업 브랜치 생성: `agent/feat/review-ai-utility-evaluation`
1. OpenSpec change 초기화: `openspec new change review-ai-utility-evaluation`
1. [openspec/specs/reliability-agentic-review/spec.md](../../openspec/specs/reliability-agentic-review/spec.md)에 Bounded Context 및 Utility evaluation 요구사항 delta 반영

### Step 2: TDD Implementation

1. **Bounded Context Builder:** incident 주변 맥락(partition 메타데이터, 연관 테이블, 미확인 gap 구분)을 결정론적으로 추출·투영하는 모듈 구현
1. **Rubric and Controls Fixture:** 5대 기준의 `rubric_v1` 및 의도된 결함(negative control) / 준수(positive control) fixture 작성
1. **Evaluation Engine:** 모델 응답에 대해 rubric 기반 판별 검증을 수행하고 baseline/candidate 비교 레코드를 생성하는 경량 러너 구현

### Step 3: Verification and Proof Capture

1. 단위 테스트 및 회귀 테스트 전체 통과 확인
1. Representative case 기반 baseline vs candidate 비교 실행 및 Utility Proof evidence 기록
1. 독립 리뷰 수행 후 Pull Request 발행

## Invariants and Safeguards

- **Deterministic truth first:** 탐지 및 핵심 안전성 판단은 LLM에 위임하지 않으며, AI review는 advisory 역할로 제한됩니다.
- **Proposal-bound approval:** 복구 변경 권한은 검증된 `RecoveryProposal`에 결합된 사람의 명시적 승인에 의해서만 부여됩니다.
- **No unbounded context:** raw logs나 전체 데이터베이스를 덤프하지 않고 엄밀하게 바운딩된 provenance-aware context만 제공합니다.
