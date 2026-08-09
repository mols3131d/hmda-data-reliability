---
type: review
title: "Data Operations Hardcoding Review"
description: "data_operations domain의 하드코딩과 application configuration ownership을 검토해 runtime 설정 연결과 operational default 중복 문제를 확인한다."
status: "completed"
tags:
  - "domain:data-operations"
  - "concern:hardcoding"
  - "concern:configuration"
---

> [!NOTE]
> **Revise.** `data_operations`는 application execution boundary이므로 운영 설정의 의미가 가장 명확해야 하지만, `.env.example`의 pipeline 설정과 `DataOperationRequest`가 연결되지 않고 일부 기본값은 orchestration·dbt와 중복된다. 반면 asset/table/column 기본값은 override 가능하거나 현재 domain contract를 표현하므로 별도 Finding으로 올리지 않았다.

## Overview

| Target | Revision | Scope | Verdict |
| --- | --- | --- | --- |
| `src/project_pivot/data_operations/**` | `main@8746db54c0e761f62e1fe4f248f9fdcce6266423` | request, runner, config 경계, related orchestration/dbt consumers와 tests | Revise |

## Findings

### F1. user-facing environment 설정이 application request의 입력이 아니다

- **Severity** - Major
- **Location** - `.env.example`, `data_operations/request.py`, `data_operations/runner.py`, `src/project_pivot/configs/`
- **Evidence** - `.env.example`은 `PROJECT_PIVOT_DUCKDB_PATH`, `PROJECT_PIVOT_SOURCE_ROOT` 등을 data pipeline 기본 설정처럼 선언하지만 `DataOperationRequest`는 literal default를 직접 가진다. `PROJECT_PIVOT_SOURCE_ROOT`는 application source에서 소비되지 않고, `PROJECT_PIVOT_DUCKDB_PATH`는 pipeline 입력으로 읽히는 대신 `run_dbt_build()`가 request의 값을 dbt subprocess environment에 다시 설정한다. `src/project_pivot/configs/`에는 이를 request로 변환하는 settings boundary가 없다.
- **Impact** - 운영자가 `.env`를 변경해도 기본 application/Dagster 실행 경로에는 반영되지 않을 수 있고, 동일 environment key가 direct dbt와 application path에서 다른 의미를 갖게 된다.
- **Required Change** - environment variable을 공식 runtime configuration으로 사용할지 결정한다. 사용한다면 하나의 application settings owner에서 `DataOperationRequest`로 변환하고, 사용하지 않는 key는 `.env.example`에서 runtime 설정처럼 노출하지 않는다. env → request 연결을 test로 검증한다.

### F2. operational default가 여러 실행 계층에 독립적으로 존재한다

- **Severity** - Minor
- **Location** - `data_operations/request.py`, `orchestration/defs/resource.py`, `dbt/profiles.yml`
- **Evidence** - DuckDB path `data/project_pivot.duckdb`는 Request, Dagster Resource, dbt fallback에 각각 정의된다. `source_root=data/raw/hmda`와 `source_year=2025`도 Request와 Resource에 중복된다. 현재 값은 일치하지만 각 위치가 독립적으로 변경 가능하다.
- **Impact** - 한 default만 변경하면 caller 또는 실행 경로에 따라 서로 다른 데이터베이스·source·partition이 선택되는 configuration drift가 발생할 수 있다.
- **Required Change** - application operational default의 canonical owner를 하나로 정한다. `DataOperationRequest`, Dagster Resource, dbt invocation은 해당 값을 변환하거나 명시적으로 override하며 별도 default authority가 되지 않게 한다.

## Validation

| Check | Evidence | Result |
| --- | --- | --- |
| application boundary 확인 | `docs/domains/data-operations.md`의 request/config 책임 확인 | Pass |
| environment key 소비 경로 | `.env.example`, request, runner, `PROJECT_PIVOT_*` source usage 교차 검색 | Fail |
| default ownership 비교 | Request, Dagster Resource, dbt profile fallback 비교 | Fail |
| dbt path coupling candidate | `dbt_project_dir`과 artifact path가 독립 field이며 연동 계약 근거가 부족해 Finding에서 제외 | Pass |
| fixed timeout candidate | `_DBT_BUILD_TIMEOUT_SECONDS=300`은 현재 local scope에서 defect 영향 근거가 부족해 제외 | Pass |
| runtime reproduction | 실행하지 않음 | Not Verified |
| pytest | 실행하지 않음 | Not Verified |

## Remaining Risks

- `.env.example`이 application runtime contract인지 development convenience인지 canonical 문서에서 명시적으로 정의되어 있지 않다. F1의 required change는 이 모호성을 먼저 해소하도록 작성했다.
- 기본값 자체보다 다중 ownership을 문제로 판단했다. `2025`, `raw.hmda_loans`, profile columns 같은 literal을 일괄 외부 설정으로 이동할 필요는 없다.

## Verdict

| Decision | Rationale | Route |
| --- | --- | --- |
| Revise | application 설정 source와 runtime request가 분리되어 있고 operational default가 여러 계층에 중복된다. | configuration ownership을 먼저 정하는 후속 OpenSpec change로 라우팅한다. |
