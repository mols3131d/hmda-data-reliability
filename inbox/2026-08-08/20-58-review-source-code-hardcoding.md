---
type: review
title: "Source Code Hardcoding Review"
description: "src/project_pivot의 변경 가능한 설정값과 중복 기본값을 도메인 책임 기준으로 검토한 결과, configuration ownership 관련 4개 finding을 확인했다."
status: "completed"
tags:
  - "domain:source"
  - "concern:configuration"
  - "concern:maintainability"
---

> [!NOTE]
> **Revise.** literal 자체보다 configuration ownership 분산이 핵심 문제다. 문제는 주로 `data_operations`, `hmda_data`, `orchestration` 경계에 집중되어 있다. custom `raw_table_name`의 schema 처리와 `.env.example`의 runtime 설정 연결은 실제 동작 계약에 영향을 주는 Major finding이며, operational default와 HMDA CSV parse policy의 중복은 drift 위험을 만드는 Minor finding이다.

## Overview

| Target | Revision | Scope | Verdict |
| --- | --- | --- | --- |
| `src/project_pivot/**` | `main@8746db54c0e761f62e1fe4f248f9fdcce6266423` | source code, `.env.example`, `dbt/profiles.yml`, 관련 domain 문서와 tests | Revise |

## Domain Summary

| Domain | Related Findings | Assessment | Primary Responsibility |
| --- | --- | --- | --- |
| `data_operations` | F1, F2, F3 | 가장 큰 configuration ownership 집중 지점 | request가 표현하는 runtime 설정 계약과 application default의 단일 소유권 정리 |
| `hmda_data` | F1, F4 | ingestion/EDA 실행 semantics에 hardcoded policy가 남음 | table schema 처리 계약과 HMDA CSV parse policy를 domain contract로 소유 |
| `orchestration` | F2, F3 | Resource가 application default를 다시 소유함 | canonical configuration을 소비하고 Dagster configuration으로 변환 |
| `data_platform` | F1 경로에 참여 | 독립 finding 없음 | generic DuckDB primitive를 유지하고 HMDA-specific 설정 ownership을 떠맡지 않음 |
| `reliability` | 없음 | material finding 없음 | configurable threshold와 공유 domain constant 사용은 현재 문제로 보지 않음 |
| `shared` | 없음 | material finding 없음 | 이번 검토에서 별도 hardcoding defect를 확인하지 않음 |

F1처럼 두 도메인에 걸친 문제는 중복 finding으로 세지 않는다. `data_operations`가 table target을 설정 계약으로 노출하고 `hmda_data`가 실제 table 생성 semantics를 구현하므로 두 경계가 함께 정리되어야 한다. F2와 F3도 `orchestration` 자체의 독립 설정 체계를 만드는 방향이 아니라 application configuration의 canonical owner를 소비하는 방향이 적절하다.

## Findings

### F1. custom `raw_table_name`의 schema가 생성되지 않는다

- **Severity** - Major
- **Location** - `data_operations/request.py`, `data_operations/runner.py`, `hmda_data/ingestion/partition.py`, `data_platform/duckdb.py`
- **Evidence** - `DataOperationRequest.raw_table_name`은 자유 문자열로 전달되지만 `_ensure_hmda_loans_table()`은 대상 table의 schema를 해석하지 않고 기본값 `raw`로 `ensure_schema()`를 호출한다. 따라서 새 DB에서 `raw_table_name="bronze.hmda_loans"`을 사용하면 `raw`만 생성한 뒤 존재하지 않는 `bronze` schema에 table 생성을 시도한다. 관련 partition tests도 `raw.hmda_loans` 경로만 검증한다.
- **Impact** - 공개된 request 설정을 정상적으로 사용해도 custom schema에서 적재가 실패할 수 있어 API 계약과 runtime behavior가 어긋난다.
- **Required Change** - `data_operations`에서 custom table을 지원하는 계약인지 먼저 확정한다. 지원한다면 `hmda_data`가 `table_name`에서 schema를 도출해 필요한 schema를 생성하고, 지원하지 않는다면 request validation에서 허용 범위를 명시적으로 제한한다. custom schema/table path component test를 추가한다.

### F2. `.env.example`의 application 설정이 기본 pipeline에 연결되지 않는다

- **Severity** - Major
- **Location** - `.env.example`, `src/project_pivot/configs/`, `data_operations/request.py`, `orchestration/defs/resource.py`, `orchestration/definitions.py`, `data_operations/runner.py`
- **Evidence** - `.env.example`은 `PROJECT_PIVOT_DUCKDB_PATH`, `PROJECT_PIVOT_SOURCE_ROOT`, `PROJECT_PIVOT_REPORT_PATH`, `LOG_LEVEL` 등을 runtime 설정처럼 선언하지만 `src/project_pivot/configs/`에는 loader가 없고 기본 Dagster entry point는 literal default를 가진 `DataOperationsResource()`를 생성한다. normal pipeline의 `PROJECT_PIVOT_DUCKDB_PATH`는 읽히지 않고 request 값으로 dbt subprocess environment에 다시 설정된다. 반면 직접 dbt 실행은 `dbt/profiles.yml`에서 같은 environment key를 읽는다.
- **Impact** - `.env` 수정이 실행 경로에 따라 적용되거나 무시되어 운영자가 동일 설정의 의미를 일관되게 예측할 수 없다.
- **Required Change** - environment variable을 공식 설정 계약으로 사용할지 결정하고 application configuration의 canonical owner를 하나로 둔다. `data_operations`는 해당 설정을 runtime request로 표현하고 `orchestration`은 이를 Dagster resource로 변환한다. 사용하지 않는 key는 `.env.example`에서 제거하거나 용도를 제한하고, env 값이 runtime request에 반영되는 test를 둔다.

### F3. operational default의 owner가 중복된다

- **Severity** - Minor
- **Location** - `data_operations/request.py`, `orchestration/defs/resource.py`, `dbt/profiles.yml`
- **Evidence** - `data/project_pivot.duckdb`는 Request, Resource, dbt fallback에 각각 정의되어 있고 `data/raw/hmda`, `source_year=2025`도 Request와 Resource에 중복된다. 현재 값은 일치하지만 각 위치는 독립적으로 변경 가능하다.
- **Impact** - 한 위치만 수정하면 caller나 실행 경로에 따라 서로 다른 default가 적용되는 configuration drift가 발생할 수 있다.
- **Required Change** - application default의 canonical owner를 하나로 두고 `DataOperationRequest`, Dagster Resource, dbt invocation은 이를 변환하거나 명시적으로 override하도록 한다. `orchestration`이 별도 default authority가 되지 않도록 한다.

### F4. HMDA CSV parse policy가 여러 실행 경로에 복제되어 있다

- **Severity** - Minor
- **Location** - `hmda_data/eda/analysis.py`, `hmda_data/ingestion/_source_query.py`, `tests/hmda_data/eda/test_eda.py`
- **Evidence** - `header=true`, `nullstr=['NA', '']`, `sample_size=200000`이 EDA evidence용 `CSV_OPTIONS`, EDA `read_csv_auto()` SQL, ingestion `read_csv_auto()` SQL에 독립적으로 기록된다. 현재 값은 일치하지만 test는 evidence 값 자체만 고정하고 reader 간 동일 정책까지 검증하지 않는다.
- **Impact** - 한 경로만 변경되면 EDA baseline과 ingestion parse semantics가 달라지거나 evidence가 실제 실행 옵션과 다른 값을 보고할 수 있다.
- **Required Change** - `hmda_data`가 HMDA CSV parse semantics의 단일 domain contract를 소유하고 EDA와 ingestion에서 공유한다. Evidence도 실제 reader에 사용한 옵션에서 생성하고 reader 간 parse contract 일치 test를 추가한다.

## Validation

| Check | Evidence | Result |
| --- | --- | --- |
| configuration source 탐색 | `src/project_pivot/**`, `.env.example`, `dbt/profiles.yml` static search | Pass |
| domain ownership 분류 | `data_operations`, `hmda_data`, `orchestration`, `data_platform`, `reliability`의 관련 call path와 domain 경계 비교 | Pass |
| custom `raw_table_name` call path | Request → runner → partition loader → `ensure_schema()` 추적 | Fail |
| environment configuration 연결 | `.env.example` key와 Dagster/resource/request 소비 경로 교차 확인 | Fail |
| operational default 중복 | Request, Resource, dbt fallback 비교 | Fail |
| HMDA CSV parse policy 일치 | EDA evidence, EDA SQL, ingestion SQL 비교 | Fail |
| runtime reproduction | 실행하지 않음 | Not Verified |
| pytest | 실행하지 않음 | Not Verified |

## Remaining Risks

- 이번 검토는 application source package와 직접 관련된 config/test에 집중했다. `scripts/`, notebooks, archived artifacts의 literal은 범위에서 제외했다.
- runtime reproduction과 test 실행을 수행하지 않았으므로 F1과 F2의 failure behavior는 static call-path 분석에 근거한다.
- `_DBT_BUILD_TIMEOUT_SECONDS = 300`은 operational tuning value지만 현재 local Foundation 범위에서 즉시 finding으로 분류할 근거는 부족하다.
- `reliability`와 `shared`의 "material finding 없음"은 이번 하드코딩 검토 범위에서의 결론이며, 해당 도메인 전체에 모든 형태의 configuration debt가 없다는 의미는 아니다.

## Verdict

| Decision | Rationale | Route |
| --- | --- | --- |
| Revise | Major 2건은 `data_operations`를 중심으로 `hmda_data`·`orchestration`과의 설정 계약이 어긋난 문제이며, Minor 2건은 동일 설정·정책의 다중 owner로 drift 위험을 만든다. | 후속 OpenSpec change에서 configuration ownership을 먼저 정하고, 각 domain implementation과 tests가 그 계약을 따르게 한다. |
