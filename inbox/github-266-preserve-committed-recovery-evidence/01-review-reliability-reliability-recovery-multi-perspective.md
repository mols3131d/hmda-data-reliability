---
type: review
title: PR #266 Recovery Cleanup Evidence Multi-Perspective Review
description: PR #266의 commit 후 staging cleanup 오류와 복구 state·reconciliation evidence 보존을 다관점으로 검토합니다.
tags:
  - domain:reliability
  - capability:reliability-recovery
---

# PR #266 Recovery Cleanup Evidence Multi-Perspective Review

> [!IMPORTANT]
> **Blocked** — 확인된 current-required 결함은 없습니다. 두 executor 모두 commit/replay 완료 상태를 보존하는 예외 경계를 추가했고, 원본 HEAD의 CI는 성공했습니다. 독립 리뷰를 이번 세션에서 별도 실행할 수 없어 최종 독립 게이트는 열려 있습니다.

- **Target** — [PR #266](https://github.com/mols3131d/hmda-data-reliability/pull/266)
- **Revision** — base `34519fec148dd2ab38ddf0cc0157c3d3ed9f7247` / reviewed head `1cf822f70dab55deafc36b1aa68dd25e18899919`
- **Scope** — Backfill/schema executor의 staging 종료 오류, commit/replay 상태 추적, typed failure, rollback 경계, 관련 OpenSpec·회귀 테스트와 CI.

## Findings

현재 승인된 변경 범위에서 확인된 `current_required` finding 없음. 코드 관점 assessment: `clear`; 최종 독립-review gate: `blocked` (separate specialist coverage 미검증). 잠재 위험은 아래 Candidate Decisions와 Risks and Limits에서 분리합니다.

## Perspectives

| Perspective | Reviewer / Method | Focus | Assessment and Evidence |
| --- | --- | --- | --- |
| Correctness | 동일 세션, 실행 순서 추적 | commit·replay 이후 cleanup 예외 | [backfill executor](../../src/hmda_reliability/reliability/recovery/executor.py)는 완료 mutation state를, [schema executor](../../src/hmda_reliability/reliability/recovery/schema_executor.py)는 `completed_result`를 기록해 종료 예외에 노출 |
| Adversarial | 동일 세션, 반례 검토 | 사전 실패·rollback·double execution | 완료 결과 없는 오류에서는 완료 mutation을 주장하지 않으며, 이미 복구된 replay는 `already_recovered`/`already_restored`로 보고 |
| Evidence/Operational | 동일 세션, 회귀·계약·CI 검토 | actual state, cause chain, 후속 조치 | [backfill](../../tests/reliability/test_approval_backfill_validation.py)/[schema](../../tests/reliability/test_schema_recovery_executor.py)에서 staging cleanup 주입 후 별도 state 확인과 replay 확인; typed error `from exc` 확인 |

## Candidate Decisions

| ID | Perspectives | Candidate | Decision | Rationale | Finding |
| --- | --- | --- | --- | --- | --- |
| C1 | Correctness, Adversarial | commit 이후 staging cleanup 오류가 mutation/reconciliation 증거를 삭제 | Drop | backfill은 `actual_identity`·freshness를 재조회하고 schema는 `completed_result.actual_state`를 보존; 두 error의 reconciliation이 `resume_verification`으로 설정됨 | — |
| C2 | Adversarial | replay cleanup 실패를 새 mutation으로 잘못 표시 | Drop | 완료 분기의 `mutation_state`를 원형 보존해 backfill `already_recovered`, schema `already_restored`를 구분하고 회귀 테스트가 두 분기를 확인 | — |
| C3 | Operational | cleanup과 profile 실패가 동시에 발생하면 진단 chain이 사라질 수 있음 | Drop | `raise ... from exc`로 cleanup `OSError`를 원인에 연결하며 staging `finally` 예외에는 원래 profile failure가 Python exception context로 남음. 다중 실패 시 상위 에러 우선순위는 이번 변경의 별도 acceptance가 아님 | — |

같은 세션에서 **1차 계약·구현 확인 → 2차 반례·회귀·운영 경계 재검토 → 후보 재판정** 순으로 수행했습니다. 서로 다른 관점은 서로 독립된 subagent 실행을 의미하지 않습니다. `Drop`은 반례 무효화, 기존 safeguard 확인 또는 본 PR의 승인 범위 밖임을 뜻합니다. `Open`은 해결로 간주하지 않습니다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | 예외 경계·상태 정적 추적 | [`executor.py`](../../src/hmda_reliability/reliability/recovery/executor.py), [`schema_executor.py`](../../src/hmda_reliability/reliability/recovery/schema_executor.py), [backfill spec](../../openspec/specs/reliability-recovery-backfill/spec.md), [schema spec](../../openspec/specs/reliability-schema-recovery/spec.md) |
| ✅ Pass | 신규 test oracle 점검 | Staging cleanup 주입을 `before/after`·replay에 적용; DB 별도 조회, typed error, actual identity, `resume_verification`, 후속 replay 확인 |
| ✅ Pass | 원본 HEAD CI Lite | [Run 39142762860](https://github.com/mols3131d/hmda-data-reliability/actions/runs/39142762860) `check=success` |
| ⚪ Not Verified | 로컬 pytest 및 복합 fault 재실행 | 이번 세션에 테스트 실행 환경을 구성·실행하지 않았으며 복합 cleanup/profile fault chain은 코드와 테스트 설계로만 확인 |
| ⚪ Not Verified | 독립 specialist coverage | PR 본문에는 DualVantage 완료가 기록됐으나 원본 worker evidence를 이번 세션에서 확인하지 못함 |

## Risks and Limits

- PR #267 역시 backfill/schema executor와 복구 정본을 수정합니다. 두 PR은 동일 `main`에서 분기했으므로 **첫 병합 뒤 남은 PR의 merge 결과·회귀 테스트·CI를 다시 확인**해야 합니다. 현재 충돌을 확정했다는 의미는 아닙니다.
- 두 종류의 failure가 동시에 발생하는 특수 사례는 staged cleanup 실패의 단일 원인 계약과 구분합니다. 복합 failure의 top-level 메시지 개선은 현재 finding이 아닙니다.
- **Next:** 별도 독립 리뷰/인간 리뷰 → 다른 복구 PR 병합 이후 잔여 PR을 최신 `main`에 통합 검증.

이 보고서는 비정본 리뷰 산출물입니다. 본문에 기록된 원본 HEAD 이후 보고서 커밋이나 후속 PR 병합으로 검증 state가 바뀌면 review readiness와 CI를 새 revision 기준으로 다시 판단해야 합니다.
