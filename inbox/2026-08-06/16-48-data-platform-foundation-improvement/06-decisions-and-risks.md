---
title: Data Platform Decisions and Remaining Risks
description: data_platform foundation 구현 전에 확정해야 할 결정과 아직 검증되지 않은 위험을 정리한다.
tags:
  - data-platform
  - decisions
  - risks
---

# Decisions And Risks

## Decision Register

### D1. Database path resolution owner

**Question**

상대 `database_path`를 어느 boundary에서 absolute identity로 변환할 것인가?

**Options**

| Option | Strength | Risk |
| --- | --- | --- |
| Request model 생성 시 resolve | 이후 모든 caller가 동일 값 사용 | 생성 CWD에 의미가 고정되고 serialization 값 변경 |
| Runner 진입 시 application root 기준 resolve | 실행 boundary가 책임지고 project default와 잘 맞음 | runner 밖에서 helper를 직접 쓰는 caller는 별도 정책 필요 |
| dbt profile에 `../data` 사용 | 변경이 작음 | Python/dbt identity 문제를 profile layout에 숨기며 custom path 문제 유지 |
| absolute path만 허용 | 가장 명확함 | CLI와 config 사용성이 낮아지고 migration 필요 |

**Recommendation**

Application execution boundary가 명시적 root를 기준으로 resolve하고, subprocess와 result model에 같은 resolved value를 전달한다. Domain helper는 전달받은 path를 임의로 project-relative 해석하지 않는다.

### D2. Cleanup ownership API

**Question**

누가 persistent DuckDB와 sidecar resource를 삭제할 권한을 갖는가?

**Options**

| Option | Strength | Risk |
| --- | --- | --- |
| 현재 boolean 유지 + pre-existing 거부 | migration이 작음 | ownership 의미가 여전히 간접적 |
| dedicated temporary manager/factory | ownership이 명시적 | API 추가와 caller migration |
| cleanup 기능 제거, tmp_path가 lifecycle 소유 | 가장 단순하고 안전 | helper 편의 감소 |
| caller가 explicit delete method 호출 | 파괴적 action이 보임 | close와 cleanup 원자성 감소 |

**Recommendation**

Production helper에서는 implicit cleanup을 제거하거나 엄격히 제한한다. Test temporary DB는 fixture가 lifecycle을 소유하는 구조가 가장 단순하다. boolean을 유지한다면 pre-existing, read-only와 unknown ownership을 생성 전에 거부한다.

### D3. Mart population

**Question**

현재 `application_count`는 전체 row인가, 일반 application인가, preapproval까지 포함하는가?

**Recommended starting model**

| Population | Proposed codes | Note |
| --- | --- | --- |
| `record_count` | 1–8 | grain에 포함된 전체 record |
| general application | 1–5 | human confirmation required |
| purchased loan | 6 | application과 분리 |
| preapproval | 7–8 | 일반 application과 분리 |

이 분리는 CFPB action meaning을 구조적으로 드러낸다. MVP가 preapproval 분석을 하지 않더라도 code 7만 denial에 혼합하지 않는 편이 일관적이다.

### D4. Approval rate

**Question**

어떤 decision population을 denominator로 사용할 것인가?

**Recommended default for discussion**

```text
approval_count = actions 1, 2
denial_count = action 3
decision_count = approval_count + denial_count
approval_rate = approval_count / decision_count
```

Preapproval은 별도 rate가 필요할 때 actions 7, 8로 계산한다. Withdrawn, incomplete와 purchased loans는 일반 approval rate denominator에서 제외한다.

이는 제안이며 canonical decision이 아니다. Portfolio에서 보여주려는 분석 질문과 downstream 사용자를 기준으로 인간이 확정해야 한다.

### D5. Zero denominator

Options:

- `NULL`: rate가 정의되지 않음을 보존
- `0`: 소비는 편하지만 실제 0% approval과 구분되지 않음
- row 제외: grain 존재와 record count 정보를 잃을 수 있음

**Recommendation**

`NULL`을 기본으로 하고 consumer가 표시 정책을 정한다.

### D6. Test ownership

**Question**

동일 behavior를 dbt unit, data test와 pytest integration 중 어디서 보호할 것인가?

**Rule**

- SQL mapping과 계산: dbt unit
- materialized relation invariant: dbt data test
- real path, subprocess, artifact와 lineage wiring: pytest integration
- DuckDB lifecycle: pytest component

한 behavior를 모든 계층에서 exact하게 반복하지 않는다.

## Remaining Risks

### Runtime state unknown

이번 조사에서는 test suite와 실제 dbt command를 실행하지 않았다. 현재 behavior의 runtime pass/fail, test duration과 platform-specific failure는 미확인이다.

### Current data impact unknown

2025 full dataset에서 action code별 row count와 현재·제안 metric 차이를 계산하지 않았다. Semantic decision 전에 read-only impact query가 유용하다.

권장 evidence:

- action code별 count
- code 6, 7, 8 비중
- 현재 denominator와 proposed decision denominator 차이
- state/loan_purpose별 approval rate delta
- Null grain 제외 row 비중

이 분석은 decision을 돕지만 full-data output을 routine test fixture로 사용하지 않는다.

### Hidden callers

Repository 검색으로 `cleanup_on_close`와 mart column caller를 확인해야 한다. 외부 사용자나 unpublished notebook은 repository만으로 알 수 없다.

### DuckDB sidecar behavior

현재 cleanup은 DB와 `.wal`만 대상으로 한다. DuckDB는 persistent database 주변에 temporary directory도 만들 수 있다. sidecar를 모두 지우는 generic cleanup을 만들기보다 ownership을 좁히는 편이 안전하다.

### Concurrency and locking

동일 DB에 Python load와 dbt subprocess가 동시에 접근하는 orchestration은 이번 scope에서 검증하지 않았다. 현재 sequential contract가 canonical인지 확인해야 한다.

### Artifact freshness

runner는 기존 manifest와 run results를 제거하지만 integration helper는 직접 dbt를 실행한다. 실패 중 stale artifact가 남지 않는지, result status를 어떻게 판정할지 명시가 더 필요하다.

### Income unit semantics

HMDA `income`의 단위와 mart의 `average_income` 표시 의미를 downstream 문서가 명확히 전달하는지 별도 확인이 필요하다. 이는 current F1–F4 수정의 blocker는 아니지만 portfolio 해석 risk다.

## Research Needed Before Implementation

| Question | Evidence | Output |
| --- | --- | --- |
| cleanup caller가 존재하는가 | repository symbol search | compatibility note |
| metric change 영향은 얼마인가 | full-data read-only SQL | decision table |
| default runner를 실제 어디서 호출하는가 | CLI/Dagster call graph | path owner decision |
| dbt unit test가 현재 adapter/version에서 통과하는가 | minimal spike | implementation constraint |
| integration runtime budget은 얼마인가 | serial focused run | test gate budget |

## Blockers

다음은 구현 전에 반드시 해소한다.

- D1 path resolution owner
- D2 cleanup ownership behavior
- D3/D4 metric population과 denominator

다음은 구현과 함께 결정할 수 있다.

- test file 세부 배치
- integration helper 분리
- marker와 selector 이름
- artifact freshness assertion 형식

## Recommended Human Decisions

우선순위대로 인간에게 요청할 결정은 세 가지다.

1. DB path는 runner가 repository/application root 기준으로 absolute resolve한다.
1. `cleanup_on_close`는 pre-existing/read-only DB에 사용할 수 없으며 temporary ownership을 명시한다.
1. Mart는 `record_count`와 decision population을 분리하고 preapproval을 일반 approval rate에 혼합하지 않는다.

이 세 결정이 확정되면 나머지는 test-first implementation으로 상당 부분 자동 검증할 수 있다.
