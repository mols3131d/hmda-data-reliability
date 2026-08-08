---
type: review
category: review
title: Data Platform Domain Contracts Review
description: data_platform의 DuckDB helper, dbt 모델 계약과 검증 신뢰성을 검토한다.
status: completed
tags:
  - data-platform
  - duckdb
  - dbt
---

> [!NOTE]
> **Revise.** 도메인 경계와 구성은 단순하고 일관적이지만, 기본 DuckDB 경로가 ingestion과 dbt에서 서로 다른 파일로 해석될 수 있고 `cleanup_on_close`가 caller 소유 DB를 삭제할 수 있다. Mart 지표는 HMDA action code별 모집단 정의가 canonical contract에 없어 구현의 의미를 검증할 수 없다.

## Overview

| Target | Revision | Scope | Verdict |
| --- | --- | --- | --- |
| `data_platform` domain | `f08c2fb7` | DuckDB helper, dbt source/staging/mart, domain 문서와 관련 test | Revise |

검토 대상:

- `src/project_pivot/data_platform/`
- `dbt/`
- `docs/domains/data-platform.md`
- `openspec/specs/dbt-analytics-foundation/spec.md`
- `tests/data_platform/`
- `tests/dbt/test_analytics_foundation.py`
- 직접 연결되는 `data_operations`의 dbt 실행 경계

## Findings

### F1. 기본 DuckDB 경로가 ingestion과 dbt에서 다른 파일을 가리킨다

- **Severity** - Major
- **Location** - `src/project_pivot/data_operations/request.py`, `src/project_pivot/data_operations/runner.py`, `dbt/profiles.yml`
- **Evidence** - `DataOperationRequest.database_path` 기본값은 `data/project_pivot.duckdb`이고 runner는 이를 상대 경로 그대로 `PROJECT_PIVOT_DUCKDB_PATH`에 전달한다. `dbt-duckdb`는 상대 `path`를 `profiles.yml` 위치 기준으로 해석하므로 현재 profile에서는 `dbt/data/project_pivot.duckdb`가 된다. 반면 Python ingestion은 repository root에서 `data/project_pivot.duckdb`를 연다. 기존 통합 test는 `tmp_path`의 절대 경로를 주입해 기본 경로를 통과하지 않는다. 공식 동작은 [dbt-duckdb profile documentation](https://github.com/duckdb/dbt-duckdb#configuring-your-profile)에 명시되어 있다.
- **Impact** - 기본 설정으로 pipeline을 실행하면 ingestion이 적재한 DB와 dbt가 변환하는 DB가 분리되어 raw source 누락 또는 잘못된 신규 DB 생성으로 이어질 수 있다.
- **Required Change** - subprocess 실행 전에 database path를 repository 또는 application root 기준 절대 경로로 정규화한다. 상대 기본값을 사용하는 실제 runner 경로의 integration test를 추가하고 ingestion과 dbt가 동일 파일을 열었는지 검증한다.

### F2. `cleanup_on_close`가 caller 소유 DuckDB 파일을 삭제할 수 있다

- **Severity** - Major
- **Location** - `src/project_pivot/data_platform/duckdb.py::DuckDBConnectionManager`
- **Evidence** - `cleanup_on_close=True`이면 DB가 연결 전에 존재했는지, manager가 생성했는지 또는 `read_only`인지 확인하지 않고 종료 시 DB와 `.wal`을 삭제한다. 현재 test는 manager가 새로 생성한 임시 DB만 다루므로 기존 파일 삭제 경로를 보호하지 않는다.
- **Impact** - 기존 개발 DB나 검증 대상 DB에 flag를 잘못 적용하면 정상 종료만으로 데이터가 삭제된다. 현재 production caller는 확인되지 않았지만 public utility 계약 자체가 파괴적 동작을 안전하게 제한하지 않는다.
- **Required Change** - cleanup을 manager가 소유한 명시적 temporary database에만 허용한다. 최소한 기존 파일과 `read_only=True` 조합을 거부하고, 기존 DB가 보존되거나 명확히 실패하는 test를 추가한다.

### F3. Mart 지표의 HMDA 모집단과 action code mapping이 정의되지 않았다

- **Severity** - Major
- **Location** - `openspec/specs/dbt-analytics-foundation/spec.md`, `docs/domains/data-platform.md`, `dbt/models/marts/mart_hmda_loan_outcomes.sql`
- **Evidence** - canonical spec은 `application_count`, `approval_count`, `denial_count`, `approval_rate`를 요구하지만 각 지표의 action code와 분모를 정의하지 않는다. 구현은 모든 row를 `application_count`로 세고 승인 `1, 2`, 거절 `3, 7`만 분류한다. HMDA action에는 purchased loan `6`, preapproval approved but not accepted `8`, withdrawn `4`, incomplete `5`도 존재한다. 공식 의미는 [CFPB Regulation C §1003.4](https://www.consumerfinance.gov/rules-policy/regulations/1003/4/)에서 확인된다.
- **Impact** - 현재 SQL이 틀렸다고 단정할 수는 없지만, purchased loan과 미결정 상태를 승인율 분모에 포함할지, preapproval code를 어느 지표에 포함할지 검증할 기준이 없다. 같은 이름의 지표가 후속 분석에서 다른 의미로 해석될 수 있다.
- **Required Change** - canonical spec에 지표별 대상 row, action code mapping과 분모를 정의한다. `1`부터 `8`까지 대표 fixture를 사용해 정의된 모집단과 지표를 독립적으로 검증한다. 필요하면 `record_count`, `application_count`, `decision_count`를 분리한다.

### F4. Staging의 row·Null 보존 계약이 false green 상태다

- **Severity** - Minor
- **Location** - `docs/domains/data-platform.md`, `tests/dbt/test_analytics_foundation.py`
- **Evidence** - domain 문서는 staging이 모든 raw row와 `state_code`, `county_code` Null을 보존한다고 선언한다. 통합 fixture에는 `state_code`가 Null인 row가 있지만 test는 이 row가 제외된 mart 결과만 검증한다. Staging row count, Null row 존재와 cast 결과를 직접 확인하지 않는다.
- **Impact** - staging에 잘못된 filter가 추가되거나 Null 보존이 깨져도 현재 test는 동일한 mart 결과로 통과할 수 있다.
- **Required Change** - `staging.stg_hmda_loans`의 전체 row count, Null key row 보존, 컬럼 타입과 `try_cast` 실패 결과를 직접 assertion한다.

## Validation

| Check | Evidence | Result |
| --- | --- | --- |
| Domain ownership boundary | `ARCHITECTURE.md`, `docs/domains/data-platform.md`, `hmda-data.md`, `data_operations/runner.py` 교차검토 | Pass |
| Default DB path trace | request 기본값 → runner env → dbt profile resolution 추적 | Fail |
| Cleanup ownership invariant | manager 구현과 기존 test 비교 | Fail |
| Mart metric contract | OpenSpec, SQL과 CFPB action 의미 비교 | Fail |
| Staging preservation oracle | 문서 contract와 integration assertion 비교 | Fail |
| Runtime test execution | GitHub connector 기반 정적 검토만 수행 | Not Verified |

## Remaining Risks

- test suite와 실제 dbt command를 실행하지 않아 runtime failure와 현재 pass 여부는 확인하지 않았다.
- action code별 실제 2025 데이터 분포를 측정하지 않아 F3의 현재 수치 영향은 정량화하지 않았다.
- `cleanup_on_close`의 현재 production caller는 발견되지 않았으므로 F2는 즉시 발생 중인 장애가 아니라 고영향 public API 위험이다.

## Verdict

| Decision | Rationale | Route |
| --- | --- | --- |
| Revise | 기본 실행 경로의 DB 불일치와 파괴적 cleanup 계약을 먼저 해소해야 한다. Mart 지표는 구현 수정 전에 canonical 의미를 확정해야 한다. | `data_platform`, `data_operations`, `dbt-analytics-foundation` owning artifacts |
