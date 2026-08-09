---
type: review
title: "Data Platform Hardcoding Review"
description: "data_platform domain의 DuckDB/dbt 설정 literal을 검토해 dbt profile의 독립 database default ownership을 확인한다."
status: "completed"
tags:
  - "domain:data-platform"
  - "concern:hardcoding"
  - "concern:configuration"
---

> [!NOTE]
> **Revise.** Python DuckDB helper의 `raw` schema default와 SQL/dbt model의 grain·action code는 현재 계약상 고정 semantics이거나 override 가능해 Finding이 아니다. 다만 `dbt/profiles.yml`이 application과 별도로 DuckDB 파일 경로 fallback을 소유해 direct dbt와 application 실행 경로 사이 drift 가능성이 남는다.

## Overview

| Target | Revision | Scope | Verdict |
| --- | --- | --- | --- |
| `src/project_pivot/data_platform/**`, `dbt/**` | `main@8746db54c0e761f62e1fe4f248f9fdcce6266423` | DuckDB helpers, dbt profile/model contracts, 관련 tests | Revise |

## Findings

### F1. dbt profile이 DuckDB database default의 별도 authority다

- **Severity** - Minor
- **Location** - `dbt/profiles.yml`, `data_operations/request.py`, `orchestration/defs/resource.py`
- **Evidence** - `dbt/profiles.yml`은 `PROJECT_PIVOT_DUCKDB_PATH`가 없으면 `data/project_pivot.duckdb`를 사용한다. 같은 경로가 `DataOperationRequest`와 Dagster Resource에도 독립 default로 존재한다. application runner는 request 값을 subprocess environment에 주입하므로 pipeline 경로에서는 profile fallback보다 request가 사실상 우선하지만 direct dbt 실행은 profile fallback을 사용한다.
- **Impact** - 한 계층의 default만 변경되면 direct dbt와 application/Dagster가 서로 다른 DuckDB 파일을 대상으로 실행될 수 있다.
- **Required Change** - database path의 canonical operational default를 하나로 정하고 dbt profile은 environment 또는 명시 입력을 소비하는 adapter로 둔다. fallback을 유지한다면 다른 계층과 drift하지 않도록 계약 또는 test로 고정한다.

## Validation

| Check | Evidence | Result |
| --- | --- | --- |
| domain contract 확인 | `docs/domains/data-platform.md`의 DuckDB helper와 dbt ownership 확인 | Pass |
| database path ownership | dbt profile, DataOperationRequest, Dagster Resource 비교 | Fail |
| `ensure_schema("raw")` candidate | `schema_name`이 명시적으로 override 가능하고 문서화된 helper contract라 Finding에서 제외 | Pass |
| dbt model literal candidate | mart grain, action code, schema 이름은 canonical data contract로 분류 | Pass |
| `threads: 4` candidate | 현재 local Foundation에서 구체적 failure 또는 change-cost 근거가 없어 Finding에서 제외 | Pass |
| runtime reproduction | 실행하지 않음 | Not Verified |
| dbt/pytest execution | 실행하지 않음 | Not Verified |

## Remaining Risks

- F1은 현재 값 불일치가 아니라 configuration drift risk다. 현재 세 경로의 database path 값은 동일하다.
- dbt model business rules를 외부 configuration으로 이동하는 것은 이번 리뷰의 권고가 아니다.

## Verdict

| Decision | Rationale | Route |
| --- | --- | --- |
| Revise | direct dbt와 application 실행이 동일 database default를 서로 다른 위치에서 소유한다. | application configuration ownership 정리 시 `dbt/profiles.yml`의 fallback 책임을 함께 정한다. |
