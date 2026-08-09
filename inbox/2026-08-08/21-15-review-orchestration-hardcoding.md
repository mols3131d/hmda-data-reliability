---
type: review
title: "Orchestration Hardcoding Review"
description: "orchestration domain의 Dagster resource와 default Definitions 설정을 검토해 application configuration의 중복 ownership을 확인한다."
status: "completed"
tags:
  - "domain:orchestration"
  - "concern:hardcoding"
  - "concern:configuration"
---

> [!NOTE]
> **Revise.** asset 이름, group, dependency 같은 Dagster graph identity는 orchestration contract이므로 하드코딩 결함이 아니다. 문제는 `DataOperationsResource`가 application operational default를 다시 직접 정의하고 default `Definitions`가 이를 그대로 사용한다는 점이다. 이 구조는 orchestration을 별도 configuration authority로 만든다.

## Overview

| Target | Revision | Scope | Verdict |
| --- | --- | --- | --- |
| `src/project_pivot/orchestration/**` | `main@8746db54c0e761f62e1fe4f248f9fdcce6266423` | Dagster resource, definitions, assets, related configuration tests | Revise |

## Findings

### F1. Dagster Resource가 application operational default를 별도로 소유한다

- **Severity** - Minor
- **Location** - `orchestration/defs/resource.py`, `orchestration/definitions.py`, `data_operations/request.py`
- **Evidence** - `DataOperationsResource`는 `database_path="data/project_pivot.duckdb"`, `source_root="data/raw/hmda"`, `source_year=2025`를 직접 정의한다. 동일 값이 `DataOperationRequest`에도 존재한다. `definitions.py`는 별도 settings source 없이 `DataOperationsResource()`를 기본 resource로 등록한다. 현재 orchestration tests는 graph와 materialization metadata를 검증하지만 두 default owner의 일치 또는 environment override를 검증하지 않는다.
- **Impact** - application default가 변경돼도 Dagster default가 따라오지 않아 기본 pipeline이 다른 database/source/partition을 사용할 수 있다. `.env.example`의 pipeline 설정을 runtime source로 기대할 경우 default Definitions 경로에는 이를 반영할 지점도 없다.
- **Required Change** - orchestration은 application configuration의 canonical owner를 소비해 `DataOperationRequest`로 변환하는 adapter 역할만 갖게 한다. Resource에 default가 필요하면 한 source에서 파생하고, Request와 Resource의 alignment를 test로 고정한다.

## Validation

| Check | Evidence | Result |
| --- | --- | --- |
| domain contract 확인 | `docs/domains/orchestration.md`에서 config conversion이 책임임을 확인 | Pass |
| default ownership 비교 | `DataOperationsResource`와 `DataOperationRequest` field defaults 비교 | Fail |
| default Definitions 경로 | `definitions.py`가 `DataOperationsResource()`를 직접 등록하는 경로 확인 | Fail |
| graph literal candidate | asset name, group, kinds, dependency는 canonical graph identity로 분류 | Pass |
| resource surface candidate | Resource가 Request의 일부 field만 노출하는 것은 현재 문서화된 orchestration contract라 Finding에서 제외 | Pass |
| runtime reproduction | 실행하지 않음 | Not Verified |
| pytest | 실행하지 않음 | Not Verified |

## Remaining Risks

- 현재 Request와 Resource의 operational default 값은 일치하므로 F1은 즉시 발생한 데이터 오류가 아니라 drift risk다.
- environment configuration을 공식 contract로 채택하지 않는다면 `.env.example` 정리가 별도로 필요하다.

## Verdict

| Decision | Rationale | Route |
| --- | --- | --- |
| Revise | orchestration이 config 변환 계층을 넘어 application default의 두 번째 owner가 되어 있다. | configuration ownership change에서 Resource를 adapter boundary로 정리한다. |
