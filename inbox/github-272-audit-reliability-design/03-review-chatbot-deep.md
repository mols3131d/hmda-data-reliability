---
type: review
title: Reliability Chatbot Deep Review
description: PR #272 테스트 변경의 챗봇 심층 리뷰와 세션 간 지속 검토 상태를 기록합니다.
tags:
  - "capability:test-design"
  - "multi-perspective"
---

# Reliability Chatbot Deep Review

> [!IMPORTANT]
> **Blocked (review in progress)** — 새 `current_required` 결함은 아직 확정하지 않았습니다. 이는 머지 불가 판정이 아니라 이번 챗봇 리뷰의 검토 범위와 독립 재검증이 아직 닫히지 않았다는 뜻입니다. 로컬 테스트를 직접 실행하지 않았으므로 기존 CI·독립 리뷰 기록을 본 검토의 재현 결과로 간주하지 않습니다.

- **Target** — [PR #272](https://github.com/mols3131d/hmda-data-reliability/pull/272), owning branch의 Inbox.
- **Revision** — base `ea39a4fd6c8f483509cf00a1d1114feb4ef3b686`; reviewed code/head `22660aba530ec79a82deec2b12e3cc757cd5fd5f` (2026-10-26 KST 1차 확인). 이후 Inbox-only commit은 반드시 test blob 변경 여부를 대조합니다.
- **Scope** — 변경 5개 Reliability 테스트 모듈 diff, 도메인 28파일 전수 감사 기록, `reliability-evaluation-report` 정본 Spec과 평가 expected/actual 판정을 직접 비교.

## Findings

현재 직접 확인한 범위에서 **확정된 신규 finding 없음**. 이는 PR 전체의 `clear` 또는 merge readiness 검증 완료를 의미하지 않습니다.

## Perspectives

| Perspective | Reviewer / Method | Focus | Assessment and Evidence |
| --- | --- | --- | --- |
| 평가·정본 | 동일 세션 Spec 대조 | 다중 incident/action 및 empty case | 모든 expected와 required action이 포함되어야 한다는 Spec에 맞춰 partial-failure와 complete-success, 빈 목록 0.0 기대값을 검사함. `tests/reliability/test_evaluation_report.py` |
| 승인·복구 안전 | 동일 세션 정적 반증 | rejected approval, schema exact after replay | rejected reviewer/time 부재 오류, 실행 gate 거부, replacement 진입 차단·실제 after-state 재관측을 함께 검증. `contracts/test_approval.py`, `test_schema_recovery_executor.py` |
| fixture·원본 관측 | 동일 세션 반례 점검 | schema hash rename/type, freshness all-null | `test_profile_snapshots.py`가 해당 partition만 timestamps null로 갱신; observed_at fallback 검출력과 다른 연도 보존 주장은 구현과 추가 대조 필요 |

## Candidate Decisions

| ID | Perspectives | Candidate | Decision | Rationale | Finding |
| --- | --- | --- | --- | --- | --- |
| C1 | 정본 | extra detected incident/action이 자동 실패가 아닌 것은 테스트 오류 | Drop | Spec은 모든 expected/required 값의 포함을 요구; extra를 금지하는 contract 없음. 새 과잉 요구 불가 | — |
| C2 | 복구 안전 | replay가 label만 검사해 replacement를 숨길 수 있음 | Drop | 변경 테스트에 `_replace_table` fail guard와 실제 `create_table_state_identity` 재관측 존재 | — |
| C3 | fixture | all-null freshness 생성이 다른 partition을 손상할 수 있음 | Open | 대상 partition 조건이 diff에 보이나 실제 fixture/비대상 불변 assertion의 충분성은 재확인 필요 | — |

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | Evaluation 정본 Spec 비교 | `openspec/specs/reliability-evaluation-report/spec.md`의 subset 요구와 empty 0.0 규칙 직접 확인 |
| ✅ Pass | Diff/path 소유권 정적 대조 | 변경 21파일 중 test는 `tests/reliability/**` 5개. 다른 세 PR와 변경 파일 충돌 없음 |
| ⚪ Not Verified | Recovery/profile implementation과 전체 28-file audit의 독립 재검토 | [existing audit](02-review-current/README.md)와 [기존 independent](02-review-current/independent.md)는 수집된 evidence, 이번 리뷰의 독립 재현은 아님 |
| ⚪ Not Verified | pytest/negative control/CI 재실행 | PR의 268 passed와 변형 테스트 주장은 이 세션에서 직접 실행하지 않음 |

## Risks and Limits

- 정본 Evaluation Spec의 `Existing or aliased evaluation database` 시나리오에 THEN 누락이 실제로 존재합니다. 이는 현행 PR 테스트 변경이 만든 결함이 아니라 #277의 Spec owner 결정 대상입니다.
- data operations와 recovery의 actual E2E, Git fixture 공유 hook 변경도 #277 소유입니다.

## Continuation

- **State:** `mols-loops deep`; Prepare → RPI Research/Plan/Work/Review 1차(동일 세션의 순차 관점) 완료, 독립 신규 specialist 게이트 및 완전한 contract trace 미완료. 이 기록은 제품/테스트를 수정한 증거가 아니라 리뷰 checkpoint입니다.
- **Next:** schema recovery replay code에서 `_replace_table` guard와 expected after identity의 독립성을 추적하고, profile fixture의 비대상 연도 영향과 mutation detection evidence를 검토. 평가 Spec의 missing THEN은 #277 scope decision으로 분리.
- **Revalidation trigger:** main/base, head의 test/source/Spec blob, CI 상태, 새로운 feedback이 바뀌면 기존 판단을 stale로 표시하고 영향을 받는 영역을 다시 조사합니다. 전수 파일 수나 이전 에이전트가 표시한 `clear`를 독립 검증으로 대체하지 않습니다.
- **Boundary:** 이 문서는 비정본입니다. 공유 CI/Git fixture와 교차 도메인 계약은 [#277](https://github.com/mols3131d/hmda-data-reliability/pull/277)에서 선행 PR을 취합한 뒤 검증합니다. 승인·merge·thread resolution은 수행하지 않습니다.
