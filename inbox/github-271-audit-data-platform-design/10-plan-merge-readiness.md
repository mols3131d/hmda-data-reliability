---
type: plan
title: PR 271 Merge Readiness Work Plan
description: 수용한 C6을 보완하고 C11·공유 작업의 경계를 명시한 뒤 현재 코드의 리뷰·검증·전달 근거를 머지 판단에 사용할 수 있게 갱신합니다.
---

# PR 271 Merge Readiness Work Plan

**State:** C6 보완·실제 반례 검증·새 독립 리뷰(`clear`)와 base/head CI 확인 완료. [현재 판정과 잔여 위험](11-review-merge-readiness.md)을 기준으로 인간의 머지 판단에 전달한다. GitHub Ready 전환·approval·merge는 별도 인간 권한으로 유지한다.

## Active Scope

- **Start:** head `b285467ad631f6c1055b573b6c8657f46a822a57`, base `ea39a4fd6c8f483509cf00a1d1114feb4ef3b686`. 시작 당시 로컬에 있던 [수용 문서](09-report-chatbot-review-adoption.md)는 이 계획과 함께 `75efa994`에 전달했다.
- **In scope:** #271 exclusive 테스트와 design, 이 PR의 Inbox, 현재 PR 본문·검증·리뷰 상태의 갱신과 commit/push.
- **Out of scope:** 제품 source·Spec·공유 hook/config, 타 도메인 테스트와 통합 구현, Ready 전환·승인·실제 merge. [기존 계획](00-plan-data-platform-tests.md)의 경계를 유지한다.
- **Context:** [수용 판정](09-report-chatbot-review-adoption.md)의 원본 C6/C11 재현, 현재 dbt test·helper·정본 analytics Spec과 프로젝트 test 지침을 기준으로 한다. 반복된 챗봇 회차 수를 검증 근거로 사용하지 않는다.

## Work Units

| Order | Work | Acceptance / evidence |
| --- | --- | --- |
| 1 | C6의 추가 error 무시를 최소 수정 | 실제 `dbt test`의 의도된 네 fail identity를 계속 exact 비교하고, 그 밖의 실행 오류·예상 밖 status를 거부한다. |
| 2 | C6의 정상·fault 검증과 관련 정적 검사 | 원래 negative scenario 통과, 기존 `DROP COLUMN application_count` fault가 추가 error를 이유로 거부됨을 실제 dbt에서 확인. `tests/data_platform tests/dbt`와 Ruff·format·ty 실행. 테스트가 수정된 것이며 제품 behavior 변경이 아님을 구분한다. |
| 3 | 새 independent review | Development context의 gate에 따라 별도 `review-lead`가 quality/adversarial 검토를 취합한다. `current_required`만 현 scope에 수용·수정하고, source/공유 작업의 scope decision은 임의 구현하지 않는다. |
| 4 | C11·공유 hook·통합 항목의 disposition 확정 | C11은 원본 재현이 있는 기존 source 위험이다. #271이 이 경로를 변경하거나 노출을 넓히지 않는지 대조하고, source owner의 후속 정책·수정 필요를 명시한다. 공유 hook의 영구 수정 완료로 임시 wrapper를 대신하지 않는다. 리뷰가 해당 경계를 blocker로 판단하면 ready를 선언하지 않는다. |
| 5 | 문서·PR·원격 evidence 전달 | 기존 과거 기록을 보존하면서 현재 plan/report/PR 본문에 새 결과를 연결한다. 현재 base/head·prospective merge에서 CI가 실제 선택된 테스트와 Python 검사를 실행했는지 log로 확인한다. |

## Delivery Safety

이전 pre-push의 Git-local 환경 누출은 미해결 공유 문제다. Repository 밖의 임시 wrapper에서 pytest child 직전에 `git rev-parse --local-env-vars`가 반환한 이름을 제거한다. Synthetic Git fixture probe, 실제 child 환경 확인, push 후 HEAD/index/worktree 점검을 유지하며 공유 hook 자체는 수정하지 않는다. 기존 `/tmp` 경로의 존재나 이전 hook 결과를 현재 실행 근거로 가정하지 않는다.

## Completion Gates

- [x] C6의 예상 밖 status 거부 및 기존 네 fail identity 검증 유지
- [x] 실제 정상·추가 error 반례와 도메인·정적·문서 검사
- [x] 최종 코드의 fresh independent review와 finding disposition
- [x] C11·공유 hook·cross-domain 항목의 실제 미해결 범위와 소유권 명시
- [x] PR 본문과 base/head/prospective-merge CI, blocking feedback·rules 상태 확인
- [x] 원격 동기화와 clean HEAD/index/worktree 확인, 남은 인간 gate 보고

## Run State

`mols-loops`, standard, `max_loops=30`, `loops_used=1`. Prepare는 READY WITH LIMITS였다. Research/Plan → Work → 최종 코드의 독립 Review를 완료했고 `clear`를 받았다. C11·공유 hook은 이 코드의 새 blocker가 아닌 별도 `follow_up / independent_requirement`로 판정했다. 새 공유 Git identity 잔류도 [hook addendum](07-report-pre-push-environment.md#current-delivery-addendum)에 기록하고 config·공개 history를 보존했다.

Finalize의 근거 snapshot은 head `75efa994` / merge `961be736`이다. Focused dbt `3 passed`, domain `43 passed, 1 warning`, 실제 fault 거부, 독립 focused `1 passed`·실제 fault 거부, Python 정적 검사와 CI domain `43 passed, 1 warning`을 확인했다. 이 문서를 전달하는 Inbox-only commit 이후에도 base/head·CI·본문·Git 상태를 다시 대조한다. 기계적 문서 마무리는 추가 Loop로 세지 않는다. 현 lane의 준비 작업은 COMPLETE이며 실제 인간 review·Ready·merge와 별도 source/공유 수정은 완료로 세지 않는다.
