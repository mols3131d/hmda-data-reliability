---
type: review
title: Data Platform Chatbot Deep Review
description: PR #271 테스트 변경의 챗봇 심층 리뷰와 세션 간 지속 검토 상태를 기록합니다.
tags:
  - "capability:test-design"
  - "multi-perspective"
---

# Data Platform Chatbot Deep Review

> [!IMPORTANT]
> **Blocked (review in progress)** — 새 `current_required` 결함은 아직 확정하지 않았습니다. 이는 머지 불가 판정이 아니라 이번 챗봇 리뷰의 검토 범위와 독립 재검증이 아직 닫히지 않았다는 뜻입니다. 로컬 테스트를 직접 실행하지 않았으므로 기존 CI·독립 리뷰 기록을 본 검토의 재현 결과로 간주하지 않습니다.

- **Target** — [PR #271](https://github.com/mols3131d/hmda-data-reliability/pull/271), owning branch의 Inbox.
- **Revision** — base `ea39a4fd6c8f483509cf00a1d1114feb4ef3b686`; reviewed code/head `8ef30680eea1c9b6265545f7e913d2e6972ffa36` (2026-10-26 KST 1차 확인). 이후 Inbox-only commit은 반드시 test blob 변경 여부를 대조합니다.
- **Scope** — 변경 test/design 5파일 및 전체 5개 baseline tracked 파일의 감사 보고서, 실제 dbt mart fixture의 결과와 `data-platform-dbt-analytics` 정본 계약을 직접 대조.

## Findings

현재 직접 확인한 범위에서 **확정된 신규 finding 없음**. 이는 PR 전체의 `clear` 또는 merge readiness 검증 완료를 의미하지 않습니다.

## Perspectives

| Perspective | Reviewer / Method | Focus | Assessment and Evidence |
| --- | --- | --- | --- |
| 숫자·Spec 독립성 | 동일 세션 고정값 재계산 | 전체 mart grain·metric | dbt Spec상 action 1/2 승인, 3/7 거절, 6자리 반올림. TX actions 1/2/4 → 3 applications, 2 approvals, rate 0.666667, 유효 numeric 2개 평균 150000/75는 고정 fixture와 일치. `tests/dbt/test_analytics_foundation.py` |
| 실제 경계 | 동일 세션 test diff 검토 | dbt build/test, DuckDB read-only·parser | fake 호출 대신 실제 DuckDB parser와 실제 dbt CLI 실패 노드 집합을 확인하는 경계가 추가됨. `tests/data_platform/test_sql.py`, `tests/dbt/test_analytics_foundation.py` |
| 오류·격리 | 동일 세션 반증 점검 | lock cleanup, artifact identity | 독립 pair bytes와 shared/exclusive lock 테스트가 추가됨. 구현 의존 test assertions의 충분성은 추후 확인 필요 |

## Candidate Decisions

| ID | Perspectives | Candidate | Decision | Rationale | Finding |
| --- | --- | --- | --- | --- | --- |
| C1 | Oracle | approval rate와 numeric-null 기대값이 Spec과 불일치 | Drop | source-independent fixture 산술과 [Spec](../../openspec/specs/data-platform-dbt-analytics/spec.md)의 의미가 일치 | — |
| C2 | 테스트 경계 | SQL escape property가 생산 알고리즘 복사만 검사함 | Drop | 변경된 property는 DuckDB에서 실행해 원래 identifier/literal을 관찰 | — |
| C3 | 결함 검출력 | `dbt test` 실패 노드 4종은 특정 fixture 결합으로 false green 가능 | Open | returncode 1과 unique_id·test metadata 집합을 비교하므로 단순 exit-1 false green은 억제. manifest 결과가 실제 오염을 반영하는지 구현·dbt schema 추가 trace 필요 | — |

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | 정본 dbt analytics Spec 비교 | `openspec/specs/data-platform-dbt-analytics/spec.md`를 현재 main에서 직접 읽고 TX fixture의 수치·null·grain expected를 대조 |
| ✅ Pass | Diff/path 소유권 정적 대조 | test/design 변경 5파일은 `tests/data_platform/**`와 `tests/dbt/**`에 한정. 타 PR의 변경 경로와 중복 없음 |
| ⚪ Not Verified | 현재 source/dbt model의 직접 전체 검토 | 실 구현으로부터의 독립 oracle 및 모델 선언을 추가 추적해야 함 |
| ⚪ Not Verified | dbt CLI/pytest/CI 재실행 | PR의 43 passed / 1 warning 및 CI 주장은 기존 증거이며 이번 세션에서 직접 실행하지 않음 |

## Risks and Limits

- dbt quality test 결과는 `run_results.json`과 manifest node metadata를 전제로 합니다. target/log isolation을 포함한 실제 재실행은 이후 회차에서 확인합니다.
- 공용 Git hook 환경 문제와 cross-domain build/promotion은 #277에서 순차 취합이 필요합니다.

## Continuation

- **State:** `mols-loops deep`; Prepare → RPI Research/Plan/Work/Review 1차(동일 세션의 순차 관점) 완료, 독립 신규 specialist 게이트 및 완전한 contract trace 미완료. 이 기록은 제품/테스트를 수정한 증거가 아니라 리뷰 checkpoint입니다.
- **Next:** `dbt/models`와 schema.yml의 실제 quality configuration을 고정 fixture/4 failure node와 대조하고, DuckDB lock/artifact primitive의 구현 예외 우선순위 및 error context를 점검. 다른 domain 소비자와 연결은 #277로 유지.
- **Revalidation trigger:** main/base, head의 test/source/Spec blob, CI 상태, 새로운 feedback이 바뀌면 기존 판단을 stale로 표시하고 영향을 받는 영역을 다시 조사합니다. 전수 파일 수나 이전 에이전트가 표시한 `clear`를 독립 검증으로 대체하지 않습니다.
- **Boundary:** 이 문서는 비정본입니다. 공유 CI/Git fixture와 교차 도메인 계약은 [#277](https://github.com/mols3131d/hmda-data-reliability/pull/277)에서 선행 PR을 취합한 뒤 검증합니다. 승인·merge·thread resolution은 수행하지 않습니다.
