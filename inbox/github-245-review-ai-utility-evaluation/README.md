# Review AI Utility Evaluation (PR #245)

이 디렉터리는 [PR #245 · `feat(review-ai): prove MVP utility evaluation`](https://github.com/mols3131d/hmda-data-reliability/pull/245) 작업 과정에서 생성된 비정본 작업 산출물(리뷰, 기획, 보고서, 제안서)을 보관합니다.

## Key Artifacts

| Sequence | Type | Artifact | Description |
| --- | --- | --- | --- |
| **15** | `report` | [15-report-review-ai-limitations-and-gaps.md](15-report-review-ai-limitations-and-gaps.md) | **★ [Archive] 리비전 정보 및 에이전트 리뷰 5대 한계·부족점 종합 정리** |
| 14 | `plan` | [14-plan-review-ai-json-markdown-fence-sanitization.md](14-plan-review-ai-json-markdown-fence-sanitization.md) | 로컬 LLM 마크다운 펜스(```` ```json ````) 자동 정제 구현 계획 |
| 13 | `report` | [13-report-review-ai-hands-on-evaluation-guide.md](13-report-review-ai-hands-on-evaluation-guide.md) | 오프라인 픽스처 및 opt-in 라이브 리뷰 사용자 직접 체험 가이드 |
| 12 | `proposal` | [12-proposal-review-ai-utility-evaluation-remediation-and-simplification.md](12-proposal-review-ai-utility-evaluation-remediation-and-simplification.md) | 블로커 최소 해소 및 평가 권한 분리, 인프라 감량 후속 제안서 (08 대체) |
| 11 | `report` | [11-report-review-ai-overengineering-assessment.md](11-report-review-ai-overengineering-assessment.md) | 평가 인프라 과잉 엔지니어링 진단 및 단순화 대상 식별 |
| 10 | `report` | [10-report-review-ai-decision-support-boundary.md](10-report-review-ai-decision-support-boundary.md) | 모델 자가선언 유틸리티 vs 인간 평가 루브릭 경계 분석 |
| 09 | `review` | [09-review-review-ai-utility-evaluation-current-head.md](09-review-review-ai-utility-evaluation-current-head.md) | Current-Head 독립 리뷰 (F1~F3 블로커 식별) |
| 08 | `proposal` | [08-proposal-review-ai-next-milestones-and-mvp-completion.md](08-proposal-review-ai-next-milestones-and-mvp-completion.md) | 3단계 마일스톤 제안서 (12번 제안서로 대체됨) |
| 07 | `report` | [07-report-review-ai-subjective-utility-verification.md](07-report-review-ai-subjective-utility-verification.md) | 유용성 주관성 한계 및 4단계 검증 방법론 |
| 06 | `plan` | [06-plan-review-ai-overdefensive-hedging-prevention.md](06-plan-review-ai-overdefensive-hedging-prevention.md) | 과도한 방어적 면책(Hedging) 회피 답변 방지 계획 |
| 05 | `brief` | [05-brief-review-ai-utility-evaluation.md](05-brief-review-ai-utility-evaluation.md) | 유틸리티 평가 구조 요약 브리프 |
| 04 | `review` | [04-review-review-ai-utility-proof-current-status.md](04-review-review-ai-utility-proof-current-status.md) | 구현 및 검증 현황 리뷰 |
| 03 | `review` | [03-review-review-ai-utility-proof-semantics.md](03-review-review-ai-utility-proof-semantics.md) | 동일 사건 바인딩 및 오프라인 증적 시맨틱스 리뷰 |
| 02 | `review` | [02-review-review-ai-utility-evaluation-improvement.md](02-review-review-ai-utility-evaluation-improvement.md) | 개선 계획 검토 |
| 01 | `plan` | [01-plan-review-ai-utility-evaluation-improvement.md](01-plan-review-ai-utility-evaluation-improvement.md) | 개선 실행 계획 |
| 00 | `review` | [00-review-review-ai-utility-evaluation.md](00-review-review-ai-utility-evaluation.md) | 초기 유틸리티 평가 설계 리뷰 |

## Limitation and Gap Tracking (Marked at #15)

[15-report-review-ai-limitations-and-gaps.md](15-report-review-ai-limitations-and-gaps.md)에 정리된 핵심 결함 및 미해결 과제 요약:

1. **Same-case Attribution 불완전 (F1):** baseline과 candidate 간 원본 입력 불변 바인딩(`review_input_digest`) 필요.
1. **Bounded Context Overflow 예외 탈출 (F2):** 16KB 초과 시 `INPUT_REJECTED` 대신 `ValueError`가 탈출하는 결함.
1. **프롬프트-검증기 허용 증적 불일치 (F3):** 프롬프트 노출 ID와 validator 허용 ID(8개) 불일치로 인한 오탐 거부 위험.
1. **런타임 마크다운 펜스 거부:** 로컬 모델의 ```` ```json ```` 응답 시 `response_schema_invalid`로 일괄 탈락하는 파서 취약성 ([14 plan](14-plan-review-ai-json-markdown-fence-sanitization.md)으로 해소 예정).
1. **평가 권한 혼재 및 프록시 착시:** 모델의 `decision_support` 제공과 인간 `rubric_v1` 평가의 엄격한 분리 필요.
