---
title: Review Findings to Data Platform Invariants
description: data_platform review finding을 테스트 가능한 invariant와 독립 oracle로 변환한다.
tags:
  - data-platform
  - invariants
  - regression
---

# Review To Invariants

## Purpose

Review finding은 과거의 문제 설명으로만 남으면 다음 변경 때 다시 조사해야 한다. 재현 가능한 finding은 다음 구조로 이전한다.

```text
finding → decision → invariant → scenario → oracle → executable check
```

Decision이 아직 없으면 test를 먼저 쓰지 않는다. 모호한 의미를 test가 임의로 canonicalize하면 false confidence가 생긴다.

## Foundation Invariant Catalog

| ID | Invariant | Risk | Oracle | Level | Current state |
| --- | --- | --- | --- | --- | --- |
| DP-R01 | 모든 execution boundary는 하나의 resolved DuckDB path를 사용한다. | 다른 DB에 load/build | 실제 raw와 mart가 같은 absolute file에 존재 | Integration | Missing |
| DP-R02 | read-only connection은 기존 DB에만 열리고 persistent state를 변경하지 않는다. | silent creation 또는 mutation | 사전·사후 파일과 table state 동일 | Component | Partial |
| DP-R03 | cleanup은 manager가 소유한 temporary DB만 삭제한다. | caller data loss | pre-existing DB 보존, owned temp 삭제 | Component | Missing |
| DP-R04 | body exception이 있어도 connection은 닫히며 원래 exception 의미가 보존된다. | lock leak, error masking | 재연결 성공과 original exception | Component | Missing |
| DP-M01 | metadata helper는 quoted schema/table을 정확히 처리한다. | 잘못된 SQL 또는 injection | 특수 identifier fixture의 exact result | Component | Partial |
| DP-S01 | staging row count는 raw row count와 같다. | silent row loss | `count(raw) == count(staging)` | dbt data/Integration | Missing |
| DP-S02 | 허용된 regional Null은 staging에서 보존된다. | coverage 왜곡 | known Null fixture의 count와 values | dbt unit/Integration | Missing |
| DP-S03 | tolerant numeric cast 실패는 row 삭제가 아니라 Null로 나타난다. | malformed data 은폐 | invalid numeric fixture가 Null output | dbt unit | Missing |
| DP-S04 | required code cast 실패는 build failure로 관찰된다. | invalid core code 사용 | invalid fixture의 non-zero dbt result | dbt unit/Integration | Missing |
| DP-G01 | mart grain은 `activity_year + state_code + loan_purpose`로 유일하다. | duplicate aggregate | unique와 not-null data tests | dbt data | Covered |
| DP-G02 | Null grain row의 제외 정책은 staging 보존과 독립적이다. | staging filter로 잘못 해결 | staging에는 존재, mart에는 부재 | Integration | Partial |
| DP-K01 | metric population과 action mapping은 canonical spec과 일치한다. | 의미가 다른 동일 metric | codes 1–8 fixture의 exact result | dbt unit | Blocked by decision |
| DP-K02 | `approval_rate`는 정의된 numerator/denominator와 zero policy를 따른다. | 왜곡된 비율 | hand-calculated fixture | dbt unit | Blocked by decision |
| DP-K03 | count metric은 음수가 아니며 component count가 population을 초과하지 않는다. | arithmetic regression | simple inequality data test | dbt data | Missing |
| DP-E01 | 동일 raw와 command의 반복 build는 동일 mart state를 만든다. | duplicate accumulation | first/second exact rows | Integration | Covered |
| DP-E02 | manifest lineage는 raw → staging → mart를 유지한다. | downstream evidence 단절 | node dependency graph | Integration | Covered |
| DP-E03 | artifact는 현재 실행에서 새로 생성된 결과다. | stale artifact false green | pre-delete 후 존재 + run result status | Integration | Partial |

## Finding Conversion

### F1: Split database path

**Decision needed**

- 어느 경계에서 relative path를 resolve할지 정한다.
- 권장 owner는 subprocess를 호출하는 application boundary다.
- domain model에 absolute-only constraint를 강제할지는 별도 판단한다.

**Regression scenarios**

| Scenario | Expected |
| --- | --- |
| default request로 raw load 후 dbt build | 동일 absolute DB에 `raw`, `staging`, `marts` 존재 |
| 다른 working directory에서 runner 실행 | 결과 DB identity가 변하지 않음 |
| explicit absolute tmp path | 전달된 path를 그대로 사용 |
| non-existent parent | writable flow에서 parent 생성, read-only flow에서는 명확한 실패 |

**Independent oracle**

dbt command 인자를 mock으로만 검사하지 않는다. 실제 file identity와 schema state를 조회한다.

### F2: Unsafe cleanup

**Decision needed**

`cleanup_on_close` boolean을 유지할지, explicit temporary ownership API로 교체할지 정한다.

**Minimum safe scenarios**

| Scenario | Expected |
| --- | --- |
| manager가 새 temporary DB 생성 | close 후 DB와 관련 owned temp 제거 |
| 사전에 존재한 DB + cleanup 요청 | 생성 전에 거부하거나 DB 보존 |
| read-only + cleanup 요청 | 생성 전에 거부 |
| context body exception | connection 닫힘, cleanup contract 유지 |
| cleanup unlink failure | original body exception을 가리지 않는 명시적 error policy |

DuckDB는 persistent DB 주변에 WAL뿐 아니라 temporary directory를 만들 수 있다. cleanup 구현은 파일 목록을 추측해서 무조건 삭제하기보다 ownership scope를 먼저 제한해야 한다.

### F3: Undefined metrics

**Decision needed**

현재 `application_count`, `approval_count`, `denial_count`, `approval_rate` 이름만으로는 HMDA action code population을 결정할 수 없다.

권장 최소 분리는 다음과 같다.

| Metric | Proposed meaning | Status |
| --- | --- | --- |
| `record_count` | grain에 포함된 전체 LAR row | Recommended |
| `application_count` | 일반 application lifecycle population | Human decision |
| `preapproval_count` | preapproval action population | Optional |
| `purchased_loan_count` | code 6 population | Optional |
| `decision_count` | approval rate denominator | Human decision |
| `approval_count` | approved population | Human decision |
| `denial_count` | denied population | Human decision |
| `approval_rate` | `approval_count / decision_count` | Recommended shape |

핵심은 code 7을 denial에 포함하면서 code 8을 approval에 포함하지 않는 현재 비대칭을 의도된 정책으로 확정하거나 제거하는 것이다.

**Fixture**

action code `1`부터 `8`을 각각 최소 한 행 포함하고, 다음 경계를 별도 group으로 만든다.

- 일반 application
- preapproval
- purchased loan
- withdrawn/incomplete
- Null grain exclusion
- zero denominator

Expected rows는 SQL 표현을 복제하지 않고 사람이 계산한 literal로 둔다.

### F4: Staging false green

**Decision exists**

Domain 문서는 모든 raw row, regional Null과 tolerant numeric cast 결과를 보존한다고 선언한다. 별도 의미 결정 없이 test로 고정할 수 있다.

**Regression scenarios**

- raw 5행이면 staging도 5행이다.
- Null `state_code`, `county_code`는 staging에 남는다.
- invalid `loan_amount`, `income`은 해당 field만 Null이고 row는 남는다.
- mart는 Null grain row를 제외한다.
- source metadata column과 type contract가 유지된다.

## Prioritization

| Priority | Invariants | Reason |
| --- | --- | --- |
| P0 | DP-R01, DP-R03 | 잘못된 DB 또는 data deletion은 다른 test 신뢰성까지 훼손한다. |
| P1 | DP-K01, DP-K02 | metric 의미가 없으면 mart correctness를 판정할 수 없다. |
| P1 | DP-S01, DP-S02, DP-S03 | staging은 downstream 분석의 보존 경계다. |
| P2 | DP-R04, DP-E03 | failure diagnosis와 stale evidence를 강화한다. |
| P2 | DP-M01, DP-K03 | 낮은 비용으로 회귀 범위를 넓힌다. |

## Traceability Rule

채택 후 canonical spec 또는 design에 invariant ID를 영구적으로 넣을 필요는 없다. 다만 작업 중에는 requirement, test와 review finding을 다음처럼 추적한다.

| Requirement | Scenario | Test | Finding |
| --- | --- | --- | --- |
| Same DB identity | default request end-to-end | `test_default_pipeline_uses_one_database` | F1 |
| Owned cleanup only | pre-existing DB | `test_cleanup_rejects_preexisting_database` | F2 |
| Staging preserves rows | Null and malformed numeric | dbt unit + integration assertion | F4 |
| Metric population | action codes 1–8 | dbt unit test | F3 |

Review를 삭제해도 requirement와 test가 남으면 lifecycle이 완료된 것이다.
