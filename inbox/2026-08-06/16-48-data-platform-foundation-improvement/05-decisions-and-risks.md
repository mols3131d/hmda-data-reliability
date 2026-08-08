---
title: Data Platform Decisions and Risks
description: foundation 구현 전에 확정할 결정, 권장안과 미검증 위험을 분리한다.
tags:
  - data-platform
  - decisions
  - risks
---

# Decisions And Risks

> [!NOTE]
> 아래 권장안은 canonical decision이 아니다. 인간 결정 후 OpenSpec과 domain 문서로 이전한다.

## Decision Register

### D1. Database Path Owner

**Question:** 상대 `database_path`를 어디에서 absolute identity로 바꿀 것인가?

**Recommendation:** Application execution boundary가 명시적 root 기준으로 resolve하고, subprocess와 result에 같은 value를 전달한다. `data_platform` helper는 전달된 path를 project-relative로 재해석하지 않는다.

Profile의 `../data` 수정만으로 해결하지 않는다. 이는 layout에 의존하며 custom path와 다른 caller를 보호하지 못한다.

### D2. Cleanup Ownership

**Question:** 어떤 API가 persistent DB 삭제 권한을 갖는가?

**Recommendation:** Production helper의 implicit cleanup을 제거하거나, 명시적으로 소유한 temporary resource에만 제한한다. 기존 DB, read-only DB와 unknown ownership은 연결 전에 거부한다.

Test용 DB는 가능하면 pytest fixture가 lifecycle을 소유한다.

### D3. Mart Population

**Question:** `application_count`와 각 action code의 모집단은 무엇인가?

논의를 위한 시작점:

| Population | Codes | Note |
| --- | --- | --- |
| `record_count` | 1–8 | grain에 포함된 전체 record |
| general application | 1–5 | 인간 확정 필요 |
| purchased loan | 6 | application과 분리 |
| preapproval | 7–8 | 일반 application과 분리 |

현재처럼 code 7만 denial에 포함하고 code 8은 approval에서 제외하는 비대칭은 명시적으로 승인하거나 제거해야 한다.

### D4. Approval Rate

논의를 위한 권장 형태:

```text
approval_count = actions 1, 2
denial_count = action 3
decision_count = approval_count + denial_count
approval_rate = approval_count / decision_count
```

Withdrawn, incomplete, purchased loan은 일반 approval-rate denominator에서 제외하고, preapproval은 필요할 때 별도 rate로 계산한다.

### D5. Zero Denominator

**Recommendation:** `NULL`. 정의되지 않은 rate와 실제 0%를 구분한다. Row를 제거하지 않는다.

### D6. Test Ownership

Test ownership은 [`02-test-strategy.md`](02-test-strategy.md)가 소유한다. 같은 behavior를 여러 계층에 반복하거나 예외가 필요할 때만 별도 결정을 기록한다.

## Risk Register

| Risk | Current evidence | Required action |
| --- | --- | --- |
| Runtime state unknown | test와 dbt command 미실행 | focused baseline 실행 |
| Metric impact unknown | 2025 action distribution 미측정 | read-only impact query |
| Hidden callers | repository 전체 symbol 영향 미확정 | cleanup과 mart-column search |
| DuckDB sidecars | 현재 cleanup은 DB와 WAL만 가정 | generic deletion 대신 ownership 제한 |
| Concurrency | load와 dbt는 sequential로만 가정 | canonical execution policy 확인 |
| Artifact freshness | integration helper의 stale-result 정책 불명확 | current run status assertion |
| Income semantics | `average_income` 단위 해석 미확인 | downstream domain 문서 확인 |

Full-data impact query는 decision evidence이며 routine regression fixture가 아니다.

권장 query output:

- action code별 count와 code 6–8 비중
- current/proposed denominator 차이
- state·loan-purpose별 rate delta
- Null grain 제외 비중

## Blockers

구현 전에 확정:

1. D1 path resolution owner
1. D2 cleanup ownership
1. D3–D5 metric population, denominator와 zero policy

구현 중 결정 가능:

- test file 배치와 selector 이름
- integration helper 분리
- artifact freshness assertion 형식

## Immediate Research

| Question | Evidence | Output |
| --- | --- | --- |
| cleanup caller가 있는가 | repository symbol search | compatibility note |
| metric 변경 영향은 얼마인가 | full-data read-only SQL | decision table |
| default runner 호출 경로는 무엇인가 | CLI·Dagster call graph | D1 근거 |
| dbt unit test가 현재 version에서 동작하는가 | minimal spike | implementation constraint |
| integration runtime은 얼마인가 | serial focused run | gate budget |
