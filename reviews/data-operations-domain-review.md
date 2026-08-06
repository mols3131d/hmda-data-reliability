---
type: review
category: review
title: Data Operations Domain Review
description: data_operations application boundary의 contract, runtime behavior와 caller 일관성을 검토한다.
status: completed
tags:
  - data-operations
  - application-boundary
  - domain-review
---

> [!NOTE]
> **Revise.** Stage API 분리와 read-only lifecycle은 명확하지만, dbt artifact 설정과 실제 출력 위치가 연결되지 않고 공개 API의 오류 contract가 일관되지 않다. 또한 표준 Dagster pipeline이 dbt build 없이도 Silver/Gold asset materialization을 기록할 수 있어 실행 결과의 신뢰성을 훼손한다.

## Overview

| Target | Revision | Scope | Verdict |
| --- | --- | --- | --- |
| `src/project_pivot/data_operations/`와 직접 caller·spec·tests | `f08c2fb7a71aecd6659b77dcab5d0026e5d9ee93` | request, raw load, dbt build, incident lifecycle, result/error contract, Dagster 연계 | Revise |

## Findings

### F1. Configured dbt artifact paths are not connected to dbt output

- **Severity** - Major
- **Location** - `request.py`, `runner.py`, `tests/data_operations/test_dbt_runner.py`
- **Evidence** - `DataOperationRequest`는 `dbt_manifest_path`와 `dbt_run_results_path`를 설정으로 받는다. `run_dbt_build()`는 해당 경로의 기존 파일을 삭제하고 결과를 검증하지만, 실행 command에는 `--target-path`를 전달하지 않는다. 테스트는 subprocess stub이 request 경로에 직접 파일을 써서 성공하므로 실제 dbt 출력 위치와의 연결을 검증하지 않는다.
- **Impact** - caller가 기본값과 다른 artifact 경로를 지정하면 dbt build가 성공해도 runner는 다른 위치를 검사해 실패할 수 있다. 설정은 유효하게 보이지만 실환경에서는 동작하지 않는 false contract다.
- **Required Change** - artifact 위치의 source of truth를 하나로 만든다. `dbt_target_path`를 command의 `--target-path`와 결과 경로에 함께 사용하거나, 독립 artifact path 설정을 제거하고 project target에서 경로를 파생한다. 실제 command와 생성 위치의 일치를 검증하는 test를 추가한다.

### F2. Public entry points do not provide a stable error boundary

- **Severity** - Major
- **Location** - `docs/domains/data-operations.md`, `runner.py`, `incident_lifecycle.py`, `errors.py`
- **Evidence** - domain contract는 외부 실행자가 처리할 오류를 `DataOperationError`로 통일한다고 명시한다. `run_dbt_build()`는 subprocess와 artifact 오류를 변환하지만, `load_raw_data()`는 `HMDADataLoadError`와 DuckDB 오류를 그대로 노출할 수 있고 `run_incident_lifecycle()`도 `ReliabilityError`와 DuckDB 오류를 변환하지 않는다.
- **Impact** - 같은 application boundary의 stage마다 caller가 서로 다른 하위 domain 예외를 알아야 한다. Dagster와 직접 Python caller의 failure handling, retry와 사용자 메시지가 stage별로 달라진다.
- **Required Change** - 각 공개 entry point에서 예상 가능한 하위 domain 예외만 `DataOperationError`로 변환하고 exception chaining과 필요한 context를 유지한다. programming error나 예상하지 않은 예외를 광범위하게 숨기지 않는다.

### F3. The standard pipeline can materialize Silver/Gold without running dbt

- **Severity** - Major
- **Location** - `request.py`, `orchestration/defs/resource.py`, `orchestration/defs/assets.py`, `openspec/specs/standard-dagster-orchestration/spec.md`, `tests/orchestration/test_dagster_definitions.py`
- **Evidence** - `run_dbt_build=False`는 shared `DataOperationRequest`에 포함되고 Dagster asset은 dbt를 실행하지 않은 채 `MaterializeResult`를 반환한다. 테스트도 skipped metadata가 있는 materialization을 정상 동작으로 고정한다. 반면 canonical spec은 `pipeline_job` materialization이 raw load 다음 dbt build를 호출하도록 요구한다.
- **Impact** - stale Silver/Gold 데이터가 새로 materialize된 asset처럼 기록될 수 있다. 실행 graph와 데이터 상태의 의미가 달라져 lineage와 운영 판단의 신뢰성이 낮아진다.
- **Required Change** - 표준 pipeline에서는 skip flag를 제거하고 raw-only 실행은 asset selection이나 별도 job으로 표현한다. skip을 제품 contract로 유지해야 한다면 spec을 명시적으로 수정하고, 실행하지 않은 asset에 materialization event를 기록하지 않는 방식을 사용한다. orchestration 전용 flag는 shared stage request에서 분리한다.

### F4. `source_file_count` reports discovery count, not processed file count

- **Severity** - Minor
- **Location** - `docs/domains/data-operations.md`, `runner.py`, `hmda_data/ingestion/partition.py`, `orchestration/defs/assets.py`
- **Evidence** - 문서는 결과를 처리 파일 수로 설명하지만 `load_raw_data()`는 발견된 전체 path의 수인 `len(hmda_paths)`를 반환한다. 실제 적재는 `source_year`와 선택적 `source_file`로 row를 필터링한다.
- **Impact** - 특정 파일이나 연도 partition을 적재해도 metadata가 전체 발견 파일 수를 표시할 수 있다. 적재 범위와 관측 metadata가 일치하지 않는다.
- **Required Change** - 의미가 discovery count라면 `discovered_source_file_count`로 명확히 이름을 변경한다. processed count가 필요하면 실제 선택·기여한 파일 수를 ingestion 결과로 반환한다. 여러 파일과 `source_file` filter를 사용하는 test를 추가한다.

### F5. Frozen result models remain mutable through list fields

- **Severity** - Minor
- **Location** - `docs/domains/data-operations.md`, `dbt_result.py`, `lifecycle_result.py`
- **Evidence** - 문서는 모든 result model을 변경 불가로 정의하지만 `DbtBuildResult.command`와 `LifecycleResult`의 summary field는 `list[str]`다. Pydantic의 `frozen=True`는 field 재할당을 막지만 list 자체의 변경까지 막지 않는다.
- **Impact** - 반환 후 result가 수정되어 원래 실행 결과와 이후 logging·metadata·검증 값이 달라질 수 있다.
- **Required Change** - 변경 불가 contract를 유지한다면 collection field를 `tuple[str, ...]`로 바꾸고 nested mutation 방지 test를 추가한다. 가변 결과가 의도라면 문서의 immutability contract를 제거한다.

## Validation

| Check | Evidence | Result |
| --- | --- | --- |
| Public API가 stage 함수만 노출하는지 확인 | `__init__.py`, pipeline stage spec, Dagster ownership test | Pass |
| Incident lifecycle이 read-only boundary를 유지하는지 확인 | `incident_lifecycle.py`, lifecycle component tests | Pass |
| dbt failure, timeout, stale artifact 검증 확인 | `test_dbt_runner.py` | Pass |
| Custom artifact path가 실제 dbt output과 연결되는지 확인 | command에 `--target-path` 없음, subprocess stub test만 존재 | Fail |
| Application error type이 public stage 전체에서 통일되는지 확인 | raw·lifecycle 하위 domain 예외 변환 부재 | Fail |
| Standard pipeline의 dbt skip semantics가 spec과 일치하는지 확인 | skip materialization test와 ordered pipeline requirement 충돌 | Fail |
| Runtime test suite 실행 | 실행 환경을 사용하지 않은 static review | Not Verified |

## Remaining Risks

- 현재 spec은 baseline 호환성을 asset과 partition으로 한정한다. `profile_columns`가 다른 baseline을 허용하면 새 column의 baseline null rate가 `0.0`으로 해석될 수 있다. 이는 현재 spec 위반은 아니지만 lifecycle false positive 가능성이 있으므로 contract 확장 여부를 별도로 결정해야 한다.
- `run_dbt_build()`는 artifact 존재만 확인하며 JSON 구조나 invocation metadata가 이번 실행과 일치하는지는 검증하지 않는다. 현재 Foundation 범위에서 요구할 수준인지 판단이 필요하다.
- Test suite와 실제 dbt process는 실행하지 않았으므로 runtime 재현과 regression 여부는 확인하지 않았다.

## Verdict

| Decision | Rationale | Route |
| --- | --- | --- |
| Revise | artifact 설정의 reachable failure, 불완전한 error boundary, pipeline materialization 의미 충돌이 남아 있다. | `data_operations`와 `orchestration` owning artifacts, 관련 OpenSpec과 tests |
