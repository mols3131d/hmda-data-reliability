---
type: plan
title: Review AI Evaluation Subdomain PR Completion
description: PR 251의 주 리팩터링을 마무리하기 위해 남은 테스트 공백, 독립 리뷰, 검증과 부모 PR 통합 순서를 정리한다.
---

# Review AI Evaluation Subdomain PR Completion

2026-09-27 KST. PR #251의 주 작업은 Review AI evaluation 하위 도메인 리팩터링이다. 구현은 `73702f1eba2983ce667bef46624a96bcae5d7170`에 있고, 후속 Inbox 보고서는 현재 branch head `47713d1b1668317a7b3b117c87a379dac14aa976`까지의 구현·검증을 기록한다. 이 계획은 남은 검증과 stacked PR 통합 순서를 정리한다.

## 남은 작업

1. **F1 테스트 공백 해소:** [셀프 리뷰 09](../github-248-review-ai-langfuse-evaluation/09-review-review-ai-evaluation-subdomain-self-review.md)에서 재현한 nested comparison JSON 호환성 공백을 고친다. Base `6e64cc70a5dca8ff8cd423a9f2240848f4b2e7dd`의 대표 JSON을 독립 golden으로 고정하고 `criterion_deltas`의 전체 key/value와 enum serialization을 비교한다. 현재 모델로 expected 값을 생성하지 않는다.
1. **Mutation 검출 확인:** `baseline_score` 또는 `candidate_score` 이름 변경 mutation에서 새 golden 검사가 실패하는지 확인한다. 정상 구현에서는 통과해야 한다.
1. **변경 후 검증 갱신:** 영향받은 evaluation/Langfuse 및 Review AI/Runtime AI 테스트와 project type/lint, Tach, strict OpenSpec, 변경 Markdown/Inbox 검사를 수정된 exact head에서 다시 실행하고 결과를 기록한다.
1. **전체 suite 결과 정리:** 이전 전체 pytest는 153 passed 뒤 Airflow child 60초 timeout으로 중단됐다. 수정 후 전체 suite를 다시 실행해 결과를 갱신한다. 같은 orchestration timeout이 재현되면 PR 변경과의 관계를 조사해 별도 원인 또는 환경 제한으로 명시하고 전체 suite pass라고 주장하지 않는다.
1. **독립 리뷰 완료:** F1 수정 후 exact final head에 독립 review-lead와 필요한 adversarial failure-path 검토를 요청한다. 기존 기록의 `blocked` 결과와 미확보 adversarial 관점을 자체 리뷰로 대체하지 않는다.
1. **리뷰 결과 반영:** 새 finding이 있으면 수정하고 관련 검증과 리뷰를 해당 revision에서 반복한다. 해결된 finding 및 남은 제한은 09를 고쳐 쓰지 말고 별도 후속 보고서에 revision과 함께 기록한다.

## Stacked PR 순서

- PR #248이 아직 base인 동안 #251은 stacked 상태로 유지하고 부모보다 먼저 병합하지 않는다.
- PR #248 병합 후 #251을 `main` 기준으로 갱신하고 필요한 검증을 다시 수행한다. CI Lite는 base가 `main`인 경우에 실행되므로 새 PR CI 결과를 확인한다.
- 현재 검증 가능한 근거와 적용 가능한 review feedback이 모두 최신일 때까지 #251은 Draft로 유지한다. readiness, Ready 전환, approval과 merge는 별도 사람 판단이다.

## 경계와 미검증 항목

- 외부 Python package consumer의 영향, wheel 설치 후 실행, 실제 Langfuse ingestion/UI와 human rubric 평가는 기존 보고서 기준 **Not Verified**다. 이들은 리팩터링 테스트 보강과 구분해 남긴다.
- PR #248의 Langfuse remediation과 CI를 #251의 구현 검증으로 간주하지 않는다.

## 완료 기준

- 정적 golden이 기존 comparison JSON 계약을 직접 고정하고, nested field/enum 변경 mutation을 검출한다.
- 수정 후 필요한 focused 검증, 프로젝트 계약 검사와 최종 독립 리뷰가 exact head에 연결된다.
- 전체 pytest 결과와 알려진 timeout의 처리가 사실대로 기록된다.
- 부모 #248 병합 후 #251의 `main` base CI를 확인하고, 최종 PR evidence가 해당 base/head에 적용 가능하다.
