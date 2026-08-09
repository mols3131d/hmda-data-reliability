---
type: review
title: "HMDA Data Hardcoding Review"
description: "hmda_data domain의 하드코딩과 설정 소유권을 검토해 custom table schema와 CSV parse policy 관련 finding을 확인한다."
status: "completed"
tags:
  - "domain:hmda-data"
  - "concern:hardcoding"
  - "concern:configuration"
---

> [!NOTE]
> **Revise.** `hmda_data`의 literal 대부분은 HMDA 데이터 계약이거나 caller가 override할 수 있어 문제가 아니다. 다만 공개 `table_name`은 arbitrary qualified name을 받으면서 schema 생성은 `raw`에 고정되어 실제 failure path가 있고, CSV parse policy는 ingestion과 EDA에 중복되어 drift 위험이 있다.

## Overview

| Target | Revision | Scope | Verdict |
| --- | --- | --- | --- |
| `src/project_pivot/hmda_data/**` | `main@8746db54c0e761f62e1fe4f248f9fdcce6266423` | ingestion, EDA, synthetic defaults, 관련 tests와 domain contract | Revise |

## Findings

### F1. custom `table_name`의 schema가 생성되지 않는다

- **Severity** - Major
- **Location** - `hmda_data/ingestion/full_load.py`, `hmda_data/ingestion/partition.py`, `data_platform/duckdb.py`
- **Evidence** - `load_hmda_loans()`와 `load_hmda_loans_partition()`은 `table_name`을 인자로 받지만 table 생성 전에 항상 `ensure_schema(connection)`을 호출한다. `ensure_schema()`의 기본 schema는 `raw`다. 따라서 새 DB에서 `table_name="bronze.hmda_loans"`처럼 다른 schema를 지정하면 `raw`만 생성한 뒤 존재하지 않는 `bronze`에 table 생성을 시도한다. custom schema를 검증하는 test도 확인되지 않았다.
- **Impact** - 공개된 설정 경로가 정상 입력에서도 실패할 수 있어 API의 configurability와 runtime behavior가 어긋난다.
- **Required Change** - custom schema를 지원한다면 `table_name`에서 schema를 도출해 생성한다. 지원하지 않는다면 허용 가능한 table contract를 명시적으로 제한한다. 두 경우 모두 custom table 계약을 component test로 고정한다.

### F2. HMDA CSV parse policy가 ingestion과 EDA에 복제되어 있다

- **Severity** - Minor
- **Location** - `hmda_data/ingestion/_source_query.py`, `hmda_data/eda/analysis.py`, `tests/hmda_data/eda/test_eda.py`
- **Evidence** - `header=true`, `nullstr=['NA', '']`, `sample_size=200000`이 ingestion reader SQL, EDA reader SQL, EDA evidence용 `CSV_OPTIONS`에 각각 존재한다. 현재 값은 같지만 한 위치를 변경해도 다른 경로가 자동으로 따라오지 않는다.
- **Impact** - ingestion과 EDA가 같은 HMDA CSV를 다르게 해석하거나, evidence가 실제 EDA reader 옵션과 다른 값을 보고할 수 있다.
- **Required Change** - HMDA CSV parse semantics를 domain-owned contract 하나로 두고 ingestion과 EDA가 공유한다. Evidence는 실제 reader에 사용된 설정에서 생성하고 두 경로의 일치를 test로 검증한다.

## Validation

| Check | Evidence | Result |
| --- | --- | --- |
| domain contract 확인 | `docs/domains/hmda-data.md`의 source/Bronze ownership과 공개 API 확인 | Pass |
| custom table call path | full/partition load → `ensure_schema()` → qualified table 생성 추적 | Fail |
| CSV parse policy 비교 | ingestion SQL, EDA SQL, `CSV_OPTIONS` 비교 | Fail |
| domain literal 후보 재검토 | required columns, staging temp table, synthetic case defaults는 데이터 계약 또는 override 가능 값으로 분류 | Pass |
| runtime reproduction | 실행하지 않음 | Not Verified |
| pytest | 실행하지 않음 | Not Verified |

## Remaining Risks

- F1은 static call-path 분석에 근거하며 실제 DuckDB 실행으로 재현하지 않았다.
- EDA의 required columns와 mart grain 같은 domain semantics는 이번 하드코딩 결함 범위에서 제외했다.

## Verdict

| Decision | Rationale | Route |
| --- | --- | --- |
| Revise | custom table schema에 도달 가능한 failure path 1건과 CSV parse policy의 다중 owner 1건이 확인됐다. | `hmda_data` 후속 change에서 table contract와 CSV parse contract를 정리한다. |
