---
type: report
title: "Review AI Limitations and Evaluation Gaps Archive"
description: "PR #245 기준 리비전 정보와 함께 Review AI 및 유틸리티 평가 체계의 미해결 블로커, 설계 경계 결함, 런타임 한계를 종합 정리합니다."
status: "archived"
tags:
  - "domain:review-ai"
  - "capability:reliability-agentic-review"
  - "pull-request"
  - "report"
  - "archive"
  - "limitations"
---

# Review AI Limitations and Evaluation Gaps Archive

## Executive Summary

- **결론:** [PR #245](https://github.com/mols3131d/hmda-data-reliability/pull/245)의 유틸리티 평가 인프라 구축으로 에이전틱 리뷰의 검증 방향은 크게 전진했으나, **현재 리비전(`9355814`)은 아직 merge-ready 상태가 아닙니다.** 동일 입력 귀속(F1), 컨텍스트 초과 예외 처리(F2), 프롬프트-검증기 증적 불일치(F3)의 3대 블로커와 모델 자가선언 유틸리티 혼재 및 런타임 파서 취약성이 존재합니다.
- **근거:** 현재 헤드 독립 리뷰([09 review](09-review-review-ai-utility-evaluation-current-head.md)), 설계 경계 보고서([10 report](10-report-review-ai-decision-support-boundary.md)), 과잉 엔지니어링 진단([11 report](11-report-review-ai-overengineering-assessment.md)), 그리고 실측 라이브 아티팩트(`.local/artifacts/agentic-review/invocations/ar-20260921-35d06c89229c.json`)를 종합 대조하여 에이전트 리뷰의 구체적 부족점을 도출했습니다.
- **행동:** 본 문서는 향후 리비전 개선 및 MVP 통합 증명 단계에서 누락 없이 해소해야 할 에이전트 리뷰의 한계점 목록을 PR 아카이브로 보존하며, 후속 작업은 [12 proposal](12-proposal-review-ai-utility-evaluation-remediation-and-simplification.md)의 순서에 따라 단계적으로 진행합니다.

## Revision and Baseline Context

현재 아카이브가 작성된 시점의 기술적 기준 정보입니다.

| Field | Value | Description |
| --- | --- | --- |
| **Target PR** | [PR #245](https://github.com/mols3131d/hmda-data-reliability/pull/245) | `feat(review-ai): prove MVP utility evaluation` |
| **Working Branch** | `agent/feat/review-ai-utility-evaluation` | 작업 브랜치 |
| **Base Revision** | `2a793f4c23745abd485f26b15421b17c744760fa` | PR #245 기준 머지 대상 베이스 |
| **Reviewed Head (09 Review)** | `aaf9743d2adf8b654743bc3609fa248cc0a797c7` | 독립 리뷰어가 정적 경로 분석을 수행한 리비전 |
| **Current Git HEAD** | `9355814bce347535395950e69fd69d681976744a` | 본 아카이브 작성 시점의 최신 커밋 |
| **Live Run Artifact** | `ar-20260921-35d06c89229c.json` | 리비전 `c7ceedd`에서 실측된 라이브 호출 아티팩트 |
| **Recorded Timestamp** | 2026-09-21 21:10 KST | 아카이빙 시각 |

## Key Limitations and Gaps

현재 에이전트 리뷰 시스템의 부족한 부분을 5개 영역으로 분류하여 기록합니다.

### 1. Verification Blocker Findings (F1 to F3)

독립 리뷰에서 식별되어 머지를 차단하고 있는 3대 주요 결함입니다.

- **F1: Same-Case Attribution 불완전 (동일 입력 귀속 결여)**
  - **위치:** [src/hmda_reliability/review_ai/evaluation.py](../../src/hmda_reliability/review_ai/evaluation.py)
  - **결함:** `compare_utility_evaluations()`가 `incident_id`, `target_column`, `deterministic_facts`의 일치 여부는 검사하지만, 실제 모델에 주입된 원본 입력 스냅샷인 `AgenticReviewInput` 또는 `RemediationDraft`의 불변 다이제스트(`review_input_digest`)를 닫지 않습니다.
  - **영향:** 대조군(Baseline)과 후보군(Candidate) 사이에 의도치 않게 다른 초안이나 입력 조건이 섞여 점수 차이가 발생하더라도 `COMPARED / ACCEPT` 판정이 날 수 있어, 점수 향상이 순수 모델 성능 개선인지 입력 차이인지 인과관계를 엄밀히 증명하지 못합니다.
- **F2: Bounded Context Overflow의 비규격 예외 탈출**
  - **위치:** [src/hmda_reliability/review_ai/context.py](../../src/hmda_reliability/review_ai/context.py), [src/hmda_reliability/review_ai/service.py](../../src/hmda_reliability/review_ai/service.py)
  - **결함:** 입력 증적의 총량이 기본 상한(16KB)을 초과할 때 `build_bounded_review_context()`가 일반 `ValueError`를 발생시킵니다. `service.py`는 `PromptTooLargeError`만 잡아내므로 이 예외가 서비스 밖으로 탈출합니다.
  - **영향:** 유효한 입력이 컨텍스트 한도를 넘었을 때 정규화된 `INPUT_REJECTED` 결과를 반환하지 못하고 파이프라인이나 API가 예기치 않게 비정상 크래시됩니다.
- **F3: 프롬프트 노출 증적과 검증기 허용 증적 간 불일치**
  - **위치:** [src/hmda_reliability/review_ai/prompt.py](../../src/hmda_reliability/review_ai/prompt.py), [src/hmda_reliability/review_ai/service.py](../../src/hmda_reliability/review_ai/service.py)
  - **결함:** 바운디드 컨텍스트는 최대 8개의 증적만 선별하지만, 프롬프트의 초안 투영(`draft.evidence_refs`)에는 원본 초안의 모든 증적 ID가 그대로 노출됩니다.
  - **영향:** 모델이 프롬프트에서 실제로 확인한 증적 ID를 인용했음에도 불구하고, 서비스의 결정론적 검증기([src/hmda_reliability/review_ai/validator.py](../../src/hmda_reliability/review_ai/validator.py))는 8개 외의 ID를 위조된 증적(`fabricated_evidence`)으로 오탐하여 유효한 응답을 거부할 수 있습니다.

### 2. Runtime Parsing Fragility (Markdown Fence Issue)

- **현상:** 라이브 러너 실행 시 로컬 모델(`qwen2.5-coder:7b`)이 약 16.6초 동안 519토큰의 응답을 정상 생성했으나 `response_schema_invalid`로 일괄 탈락했습니다.
- **원인:** [src/hmda_reliability/review_ai/service.py](../../src/hmda_reliability/review_ai/service.py)의 `_parse_output()`이 `json.loads()`를 직접 호출하여, 모델이 관습적으로 붙인 마크다운 코드 블록(```` ```json ... ``` ````)을 수용하지 못하고 문법 에러를 발생시켰습니다.
- **대응 계획:** [14 plan](14-plan-review-ai-json-markdown-fence-sanitization.md)에 따라 파이썬 코드 레벨의 펜스 제거 헬퍼를 추가하여 0.001초 내에 결정론적으로 정제하도록 보강이 필요합니다.

### 3. Boundary Conflation: Self-Declared Utility vs Human Judgment

- **결함:** 모델이 출력하는 `utility_contributions`라는 필드명 자체가 "모델이 자신의 유용성을 직접 선언"하는 구조입니다.
- **평가 계층과의 결합:** 평가 모듈이 모델 출력의 `contribution_kinds` 존재 자체를 `PASS`의 전제 조건이나 오라클로 사용하고 있습니다.
- **해결 방향:** 모델은 조사 우선순위, 증적 공백 등 업무 도메인 지원 내용(`decision_support`)만을 중립적으로 제시하고, 그 내용이 실제로 유용한지는 평가자가 `rubric_v1`과 구체적 Rationale로만 판정하도록 책임을 엄격히 분리해야 합니다.

### 4. The Proxy Gap and Restatement Illusion

- **결정론적 공백 복창 (Echo):** [src/hmda_reliability/review_ai/context.py](../../src/hmda_reliability/review_ai/context.py)가 이미 생성한 `missing_evidence`나 `unconfirmed_context`를 모델이 자연어로 다시 말하는 것만으로 유용한 기여를 한 것처럼 취급될 위험이 있습니다.
- **실험실 대리 지표의 한계:** 오프라인 러너([scripts/run_review_ai_utility_proof.py](../../scripts/run_review_ai_utility_proof.py))는 베이스라인 0점, 후보 10점, 인간 승인(`ACCEPT`)이 코드에 하드코딩된 합성 픽스처입니다. 이는 계약 무결성을 시험하는 도구일 뿐, 실제 현장 엔지니어의 장애 복구 시간(MTTR) 단축을 증명하지 못합니다.

### 5. Evaluation Overengineering and Maintenance Debt

- **비대한 추상화 계층:** 단순한 2개 출력 비교라는 MVP 요구사항에 비해 `QualityBasisValidation`, `UtilityControl`, `UtilityProofCase`, `UtilityProofBundle`, 전용 `UtilityEvidenceStore` 등 지나치게 많은 도메인 모델과 영속화 계층이 추가되었습니다.
- **유지보수 비용:** 향후 변경 시마다 여러 단계의 번들과 해시 다이제스트를 갱신해야 하므로, MVP 머지 후 불필요한 계층을 테스트 픽스처 수준으로 경량화(Simplification)해야 합니다.

## Summary Checklist for Next Milestones

향후 Review AI 완결을 위해 해소해야 할 체크리스트입니다.

| Category | Gap / Limitation | Action Required | Status |
| --- | --- | --- | --- |
| **Correctness** | F1: Same-case input binding 누락 | `review_input_digest` 바인딩 및 네거티브 테스트 | ⚪ 미해결 |
| **Stability** | F2: Context overflow 예외 탈출 | typed `INPUT_REJECTED` 변환 및 서비스 테스트 | ⚪ 미해결 |
| **Consistency** | F3: Allowed evidence ID 불일치 | 프롬프트 draft 투영과 validator 허용 집합 일치 | ⚪ 미해결 |
| **Robustness** | 마크다운 펜스 파싱 거부 | `_strip_markdown_fence()` 파서 보강 (14 plan) | 🟡 기획 완료 |
| **Architecture** | 유틸리티 자가선언 결합 | `decision_support` 명칭 변경 및 평가 오라클 분리 | 🟡 제안 완료 |
| **Simplicity** | 평가 계층 과잉 엔지니어링 | 머지 후 번들/스토어 계층 축소 (11 report) | ⚪ 보류 |
| **Acceptance** | 실제 인간 유용성 증적 결여 | 라이브 모델 호출 기반 Human Intake 및 채점 | ⚪ 후속 예정 |

## Conclusion

현재의 Review AI는 **안전 차단선(Safety Gate)은 견고하게 작동하지만, 모델의 출력을 공정하고 견고하게 평가하여 채택하는 증명 체계(Evaluation Proof)에는 구멍이 남아 있는 상태**입니다.

따라서 성급하게 머지하거나 모델 튜닝으로 건너뛰지 말고, [12 proposal](12-proposal-review-ai-utility-evaluation-remediation-and-simplification.md)에 제시된 순서대로 **1) 마크다운 펜스 정제, 2) F1~F3 블로커 최소 해소, 3) 평가 권한 경계 분리, 4) 인프라 감량**을 거쳐 단일 리비전 MVP 증명으로 나아가야 합니다.
