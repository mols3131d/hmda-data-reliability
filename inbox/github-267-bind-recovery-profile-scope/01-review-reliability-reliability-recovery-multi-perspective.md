---
type: review
title: PR #267 Recovery Profile Population Multi-Perspective Review
description: PR #267의 복구 profile population 검증과 동기화 락·회귀 테스트를 다관점으로 검토합니다.
tags:
  - domain:reliability
  - capability:reliability-recovery
---

# PR #267 Recovery Profile Population Multi-Perspective Review

> [!IMPORTANT]
> **Blocked** — 실제 코드·계약 기준의 필수 수정 finding은 확인되지 않았습니다. Year alias 정규화, 실제 profile filter와 numeric year population 비교, managed-writer 락 경계의 목적과 검증이 대체로 정합적입니다. 독립 specialist 재검토를 직접 수행하지 못해 독립 게이트는 미완입니다.

- **Target** — [PR #267](https://github.com/mols3131d/hmda-data-reliability/pull/267)
- **Revision** — base `34519fec148dd2ab38ddf0cc0157c3d3ed9f7247` / reviewed head `db7b532ff1a3ac205b1220efb9d5e223befd272d`
- **Scope** — 두 recovery 요청의 profile discriminator·year population, candidate/target guard, file-scope, DB lock 재진입과 writer 직렬화, OpenSpec·pytest·CI.

## Findings

현재 승인된 변경 범위에서 확인된 `current_required` finding 없음. 코드 관점 assessment: `clear`; 최종 독립-review gate: `blocked` (separate specialist coverage 미검증). 잠재 위험은 아래 Candidate Decisions와 Risks and Limits에서 분리합니다.

## Perspectives

| Perspective | Reviewer / Method | Focus | Assessment and Evidence |
| --- | --- | --- | --- |
| Correctness | 동일 세션, 데이터 흐름·계약 추적 | 승인 source_year와 profile 범위 | [요청 validators](../../src/hmda_reliability/reliability/recovery/request.py)는 `activity_year`/`source_year`를 정본 `source_year`로 변환; [population guard](../../src/hmda_reliability/reliability/recovery/profile_scope.py)는 numeric-year와 실제 profile VARCHAR 조건의 row membership 차이를 검사 |
| Adversarial | 동일 세션, 인접 실패·동시성 반례 검토 | staged candidate, replay, lock·fork | 두 executor의 candidate/target guard와 [nested lock](../../src/hmda_reliability/data_platform/duckdb.py)의 PID·thread·canonical path 소유를 확인; 다른 thread의 배타성 회귀 포함 |
| Evidence/Regression | 동일 세션, 테스트·CI 검토 | DECIMAL, file-year scope, target writer interleaving | 관련 테스트는 `DECIMAL(6,1)` 불일치 거부와 `DECIMAL(6,0)` 동등 결과 허용, 별도 writer 대기와 replay·unlock failure evidence를 점검 |

## Candidate Decisions

| ID | Perspectives | Candidate | Decision | Rationale | Finding |
| --- | --- | --- | --- | --- | --- |
| C1 | Correctness | `activity_year` profile이 승인된 source_year 외의 population을 선택할 수 있음 | Drop | request 재검증으로 discriminator를 `source_year`로 정규화하고 profile builder는 해당 field를 이용; activity-year mismatch 회귀에서 row count 2를 확인 | — |
| C2 | Adversarial | 숫자상 같은 year라도 VARCHAR profile 조건이 다른 행을 조용히 누락할 수 있음 | Drop | `ensure_recovery_profile_population`이 `source_year = BIGINT(year)`와 `CAST(source_year AS VARCHAR)=year`의 membership 차이를 검사. scale-1 DECIMAL 거부, scale-0 허용이 기존 profile semantics와 일치 | — |
| C3 | Adversarial | 상위 lock 추가로 내부 loader가 deadlock되거나 다른 writer가 중간에 진입 | Drop | 같은 PID/thread/canonical path의 중첩만 bypass하고 외부 thread/process는 flock을 획득함. 기존 lock 기능과 nested/fork 및 managed-writer interleaving 테스트가 있음 | — |
| C4 | Integration | PR #266과 병합 시 동일 executor 코드의 통합 검증이 누락될 가능성 | Open | 양쪽 PR이 동일 원본 `main`에서 별도 수정한 backfill/schema executor를 포함. 각 PR 독립 CI는 두 변경의 결합 동작을 검증하지 않음 | — |

같은 세션에서 **1차 계약·구현 확인 → 2차 반례·회귀·운영 경계 재검토 → 후보 재판정** 순으로 수행했습니다. 서로 다른 관점은 서로 독립된 subagent 실행을 의미하지 않습니다. `Drop`은 반례 무효화, 기존 safeguard 확인 또는 본 PR의 승인 범위 밖임을 뜻합니다. `Open`은 해결로 간주하지 않습니다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | 정본·코드 정적 검토 | [backfill spec](../../openspec/specs/reliability-recovery-backfill/spec.md), [schema spec](../../openspec/specs/reliability-schema-recovery/spec.md), [`profile_scope.py`](../../src/hmda_reliability/reliability/recovery/profile_scope.py), [`duckdb.py`](../../src/hmda_reliability/data_platform/duckdb.py) |
| ✅ Pass | 변경 test matrix 검토 | [backfill tests](../../tests/reliability/test_approval_backfill_validation.py), [schema tests](../../tests/reliability/test_schema_recovery_executor.py), [lock tests](../../tests/data_platform/test_duckdb.py); 새 numeric/VARCHAR mismatch·fork·nested lock·managed-writer interleaving 확인 |
| ✅ Pass | 원본 HEAD CI Lite | [Run 39145435515](https://github.com/mols3131d/hmda-data-reliability/actions/runs/39145435515) `check=success` |
| ⚪ Not Verified | pytest 직접 실행·독립 병합 시뮬레이션 | 이번 세션에 로컬 repo/test DB 또는 PR #266 통합 merge test를 실행하지 않음 |
| ⚪ Not Verified | 독립 specialist coverage | 별도 Verifier/Challenger 실행 불가. PR 본문 보고된 과거 검토와 이번 리뷰를 구별 |

## Risks and Limits

- **C4 — Integration, follow_up:** PR #266 병합 후 #267의 profile validation과 post-commit cleanup evidence를 함께 검증해야 합니다. 담당: 후속 병합·리뷰 주체. 이는 현재 #267 단독 코드의 `current_required` 결함으로 확정된 사항이 아닙니다.
- 내부 lock의 재진입 계약은 동기적 managed-writer 호출을 전제로 합니다. 미구현 비동기/임의 executor 경로까지 안전성이 증명된 것으로 해석하지 않습니다.
- **Next:** 독립 검토 근거 확인 → 인간 리뷰 → #266과 결합되는 merge revision에서 recovery 오류·lock·profile 회귀 재확인.

이 보고서는 비정본 리뷰 산출물입니다. 본문에 기록된 원본 HEAD 이후 보고서 커밋이나 후속 PR 병합으로 검증 state가 바뀌면 review readiness와 CI를 새 revision 기준으로 다시 판단해야 합니다.
