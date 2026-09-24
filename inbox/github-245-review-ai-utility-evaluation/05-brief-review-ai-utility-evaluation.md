---
type: brief
title: "Review AI Utility Evaluation Branch Brief"
description: "PR #245 agent/feat/review-ai-utility-evaluation 브랜치의 구현 내용, 검증 결과, 현재 상태 및 잔여 과제를 정리한 요약 브리프입니다."
tags:
  - "domain:review-ai"
  - "capability:reliability-agentic-review"
  - "pull-request"
  - "brief"
---

# Review AI Utility Evaluation Branch Brief

## Executive Summary

- **결론:** `agent/feat/review-ai-utility-evaluation` 브랜치는 [docs/mvp.md](../../docs/mvp.md)의 4대 Utility Proofs를 구현하고 오프라인 검증 체계를 구축하여 코드베이스 수준의 단위·통합 테스트(113건)를 완료했습니다. 기존 리뷰([04-review-review-ai-utility-proof-current-status.md](04-review-review-ai-utility-proof-current-status.md))의 주요 차단 사유였던 F1(합성 증적 바운딩), F2(동일 사건 사실 바인딩) 및 G1(독립 dual-perspective 리뷰 및 피드백 반영)이 모두 해소되어 PR #245는 **Ready for Review 준비 완료** 상태입니다.
- **근거:** Bounded context projection, structured utility contributions, `rubric_v1` 기반 positive/negative control 평가 및 create-only evidence store가 모두 구현되었습니다. 또한 F2에 따른 동일 팩트(`incident_id`, `target_column`, `deterministic_facts`) 및 `quality_basis.project_revision` 일치 검증, 면책형(Hedging) negative control 판별 로직 및 F1 오프라인 계약 검증 명문화가 완료되었습니다.
- **행동:** 원자적 커밋 분리 후 원격 브랜치에 푸시하고, PR #245 본문 설명을 최신 검증 내역으로 갱신하여 Draft 상태를 해제합니다.

## ELI5 Overview: What Does This System Do?

복잡한 데이터 엔지니어링 및 AI 평가 용어를 일상적인 비유로 쉽게 풀어낸 핵심 안내입니다.

### 1. The Core Idea: What Is Review AI?

- **상황:** 데이터 파이프라인에 문제가 터졌을 때(예: 대출 데이터 정합성 오류), 엔지니어는 수많은 로그와 수십 개의 테이블을 뒤지며 원인을 찾느라 지치기 쉽습니다.
- **역할:** Review AI는 마치 **"노련한 수석 엔지니어 조수"**와 같습니다. 방대한 데이터 중 꼭 봐야 할 핵심 정보만 간추려주고, "이 부분이 이상하니 먼저 확인하세요", "현재 알 수 없는 부분은 이것입니다"라고 딱 짚어줍니다.

### 2. The 4 Utility Proofs: How Do We Prove It Really Helps?

단순히 "AI가 말을 잘한다"가 아니라, 사람에게 실제로 도움이 되는지 4단계로 증명합니다.

| Proof Name | 일상적 비유 | 실제 하는 일 |
| --- | --- | --- |
| **Review Context Proof** | **시험 범위 요약 노트** | 도서관 전체(방대한 DB 로그)를 주는 대신, 시험에 나올 핵심 페이지와 아직 빈칸인 부분을 깔끔하게 한 장으로 요약합니다. |
| **Agentic Utility Proof** | **앵무새 복창 방지 체크리스트** | "데이터가 틀렸습니다" 같은 당연한 사실만 앵무새처럼 반복하지 않고, 조사 우선순위와 불확실한 리스크를 조목조목 짚어줍니다. |
| **Quality Evaluation Proof** | **엄격한 채점 기준표 (루브릭)** | 다른 조교(외부 LLM)에게 매번 주관적으로 물어보지 않고, 5가지 객관적인 채점 기준표로 엉터리 답변(Negative)과 모범 답안(Positive)을 엄격히 가려냅니다. |
| **Change Comparison Proof** | **Before & After 성적표** | 이전 답변(Baseline)과 개선된 답변(Candidate)을 나란히 놓고 비교하여, 진짜 개선되었는지 점수표와 사람의 최종 확인 도장(`ACCEPT`)을 함께 금고에 보관합니다. |

### 3. Why Is This PR Blocked? (Understanding F1 & F2)

현재 109개의 모든 단위 테스트를 통과했음에도 PR이 잠시 멈춰 있는 이유입니다.

- **F1 (가짜 서명 문제):**
  - *비유:* 학생이 실제로 과외를 받고 "선생님 덕분에 성적이 올랐어요!"라고 직접 자필 서명을 해야 하는데, 자동 채점 프로그램이 학생 서명까지 혼자 대필해 버린 격입니다.
  - *해결책:* 이 스크립트가 만드는 것은 "실제 사람의 평가"가 아니라 "시스템 기능이 잘 돌아가는지 확인하는 모의고사(Fixture)"라고 명확히 선언하고, 진짜 사람의 평가는 별도로 주입받아야 합니다.
- **F2 (서로 다른 시험지 비교 문제):**
  - *비유:* 작년 중간고사 시험지와 올해 기말고사 시험지를 가져다 놓고 "올해 점수가 더 높으니 실력이 늘었다"고 비교하면 안 됩니다.
  - *해결책:* 비교하는 두 답안이 '정확히 똑같은 문제(동일 incident 파티션 및 동일 코드 리비전)'를 풀고 나온 결과인지 시스템 레벨에서 자물쇠(검증 로직)를 채워야 합니다.

## Background and Objectives

[docs/mvp.md](../../docs/mvp.md)는 단순한 파이프라인 성공이나 LLM 응답 생성이 아닌, 검증 가능한 데이터 신뢰성과 유용한 AI 위임 경계 입증을 요구합니다. 이에 따라 기존 6대 Foundation Proofs 외에 사람의 조사·복구 판단을 실질적으로 돕는 **4대 Utility Proofs**가 MVP 필수 조건으로 정의되었습니다.

| Proof | Description | Implementation Surface |
| --- | --- | --- |
| **Review Context Proof** | incident 주변 메타데이터, 연관 테이블, evidence gap을 식별하는 Bounded Review Context 제공 | [src/hmda_reliability/review_ai/context.py](../../src/hmda_reliability/review_ai/context.py) |
| **Agentic Utility Proof** | 단순 사실 재진술을 넘어 4대 영역(evidence gap, investigation priority, remediation critique, material uncertainty)에 기여 | [src/hmda_reliability/review_ai/contracts.py](../../src/hmda_reliability/review_ai/contracts.py) |
| **Quality Evaluation Proof** | 외부 LLM 판사 없이 5대 기준의 `rubric_v1`과 positive/negative control 판별 검증 수행 | [src/hmda_reliability/review_ai/evaluation.py](../../src/hmda_reliability/review_ai/evaluation.py) |
| **Change Comparison Proof** | 동일 representative case에서 baseline과 candidate를 비교하고 human decision 및 근거를 보존 | [src/hmda_reliability/review_ai/evaluation_store.py](../../src/hmda_reliability/review_ai/evaluation_store.py) |

## Key Implementations

[openspec/changes/review-ai-utility-evaluation/tasks.md](../../openspec/changes/review-ai-utility-evaluation/tasks.md)에 정의된 6개 구현 태스크가 모두 반영되었습니다.

### 1. Bounded Review Context

- 파일: [src/hmda_reliability/review_ai/context.py](../../src/hmda_reliability/review_ai/context.py)
- 원시 로그나 대규모 데이터베이스 전체를 노출하지 않고, incident partition 메타데이터, 연관 파티션, deterministic facts 및 미확인 context gap을 명시적으로 구분하는 불변 프로젝션 생성.
- 안정적인 context digest 및 바운딩 제약(최대 증적 수, 텍스트 길이 제한)을 통해 재현 가능한 프롬프트 입력을 보장.

### 2. Structured Utility Contribution & Reference Guard

- 파일: [src/hmda_reliability/review_ai/contracts.py](../../src/hmda_reliability/review_ai/contracts.py), [src/hmda_reliability/review_ai/validator.py](../../src/hmda_reliability/review_ai/validator.py)
- 에이전트 리뷰 결과(`AgenticReviewOutput`)에 4대 기여 항목(`evidence_gap`, `investigation_priority`, `remediation_critique`, `material_uncertainty`)을 구조화.
- 제공된 evidence subset에 속하지 않는 허위 참조(fabricated reference)를 거부하는 검증 경계 유지 및 레거시 출력 하위 호환성 보장.

### 3. Versioned Rubric & Control Discrimination

- 파일: [src/hmda_reliability/review_ai/evaluation.py](../../src/hmda_reliability/review_ai/evaluation.py)
- `rubric_v1`을 통해 5대 핵심 기준(added value, actionability, evidence awareness, uncertainty handling, prioritization) 정의.
- 의도된 결함이 포함된 negative control(재진술만 수행)에 대해 `FAIL`, 준수된 positive control에 대해 `PASS`를 도출하는 결정론적 판별 체계 구축.

### 4. Comparison Evidence & Create-Only Store

- 파일: [src/hmda_reliability/review_ai/evaluation_store.py](../../src/hmda_reliability/review_ai/evaluation_store.py)
- 동일 representative case 기준으로 baseline과 candidate 평가 결과를 비교하여 점수 delta와 인간 승인 결정(`HumanDecision.ACCEPT`)을 결합한 `UtilityComparisonEvidence` 생성.
- 파일 시스템 기반의 불변성(create-only, overwrite 거부), digest 변조 검증, JSON 직렬화/역직렬화 지원.

### 5. Proof Runner & Operational Script

- 파일: [scripts/run_review_ai_utility_proof.py](../../scripts/run_review_ai_utility_proof.py)
- 네트워크 및 외부 LLM 호출 없이 오프라인에서 representative case를 로드하고, control discrimination 및 baseline vs candidate 비교 리포트를 마크다운으로 출력하는 실행기 제공.

## Verification Evidence

브랜치 변경사항에 대한 결정론적 검증 및 스크립트 실행이 정상 완료되었습니다.

### Test Suite Execution

- 대상: [tests/review_ai/test_context.py](../../tests/review_ai/test_context.py), [tests/review_ai/test_utility_evaluation.py](../../tests/review_ai/test_utility_evaluation.py), [tests/scripts/test_review_ai_utility_proof.py](../../tests/scripts/test_review_ai_utility_proof.py) 등
- 결과: **113 passed** (1.99s)
  - `test_context.py`: context bounding, digest, gap projection 검증
  - `test_contracts.py`, `test_validator.py`: contribution validation 및 schema 호환성 검증
  - `test_utility_evaluation.py`: rubric completeness, control discrimination(echo 및 hedging), same-case attribution(팩트·리비전 불일치 차단), comparison contract, digest integrity 검증
  - `test_evidence_store.py`: create-only 저장소 불변성 및 reload 검증
  - `test_review_ai_utility_proof.py`: 오프라인 계약 검증 실행 및 번들 일관성 검증

### Offline Utility Proof Output

[scripts/run_review_ai_utility_proof.py](../../scripts/run_review_ai_utility_proof.py) 실행 결과 baseline(점수 0) 대비 candidate(점수 2)의 5개 기준 전반에서 +2 향상(총 +10 delta)과 `ACCEPT` 결정을 담은 오프라인 계약 및 픽스처 검증 리포트가 정상 생성됨을 확인했습니다.

## Current Status and Findings

현재 브랜치는 [PR #245](https://github.com/mols3131d/hmda-data-reliability/pull/245) (`feat(review-ai): prove MVP utility evaluation`)로 연결되어 있으며, 보정 조치 결과는 다음과 같습니다.

- **PR Status:** Ready for Review (Draft 해제 대상)
- **Review Verdict:** **Resolved** (F1, F2, G1 조치 완료)

### Remediated Findings

| ID | Severity | Finding | Resolution Summary |
| --- | --- | --- | --- |
| **F1** | 🟠 Major | **Synthetic Human Utility Proof** | [scripts/run_review_ai_utility_proof.py](../../scripts/run_review_ai_utility_proof.py)의 역할을 "오프라인 유틸리티 계약 및 픽스처 검증"으로 명문화하고, 실제 최종 인간 평가 증적과 명확히 경계를 분리함. |
| **F2** | 🟠 Major | **Incomplete Same-case Binding** | `compare_utility_evaluations`에 baseline/candidate의 `incident_id`, `target_column`, `deterministic_facts` 및 `quality_basis.project_revision` 일치 검증을 추가하고, 불일치 시 `same_case_fact_mismatch` / `quality_basis_revision_mismatch`로 차단하는 네거티브 테스트 구축 완료. |
| **G1** | 🟠 Major | **Formal Independent Review Pending** | 독립 `review-lead` formal review를 실행하여 도출된 Finding 1(Hedging Test Oracle) 및 Finding 2(네거티브 케이스 보강)을 모두 반영 완료. |

## Recommended Next Steps

1. **원자적 커밋 분리 및 푸시**:
   - `eli5` 스킬 도입과 `review-ai` 유틸리티 평가 보정을 논리적 단위 커밋으로 분리하여 원격에 푸시.
1. **PR #245 본문 설명 갱신 및 Draft 해제**:
   - PR 설명에 F1/F2/G1 해결 및 최신 113개 테스트 결과를 반영하고 `Ready for review`로 전환.
