# Data Operations: Application Execution Boundary

**`data_operations`는 입력, 실행 순서, 결과를 묶는 application boundary다.** 파일 파싱, DuckDB 세부 구현, incident 규칙은 각 domain에 위임한다.

> [!IMPORTANT]
> **Incident lifecycle은 read-only다.** backfill, approval, recovery, evaluation을 실행하지 않는다.

## Mental Model

이 package는 직접 데이터를 해석하거나 reliability 규칙을 소유하는 곳이 아니다. Caller가 하나의 `DataOperationRequest`를 만들면 `data_operations`가 필요한 domain API를 올바른 순서로 호출하고, 실행 결과와 외부에 노출할 오류를 application-level contract로 정리한다.

두 실행 흐름을 분리해서 읽으면 구조를 빠르게 이해할 수 있다.

```text
Data plane
DataOperationRequest
→ load_raw_data()
→ run_dbt_build()
→ candidate dbt artifacts
→ caller가 promotion 시점을 결정
→ promote_dbt_artifacts()
→ current dbt projection

Reliability analysis
DataOperationRequest + baseline ProfileSnapshot
→ run_incident_lifecycle()
→ current profile
→ detection
→ dbt impact
→ remediation draft
→ LifecycleResult
```

첫 번째 흐름은 raw table과 current dbt artifact projection을 변경할 수 있다. 두 번째 흐름은 DuckDB와 current dbt artifact를 읽기만 하며 recovery나 evaluation으로 이어지는 side effect를 만들지 않는다.

## Package Map

| File | 읽을 때 확인할 질문 | 책임 |
| --- | --- | --- |
| [`__init__.py`](../../src/project_pivot/data_operations/__init__.py) | 외부 caller가 의존해도 되는 API는 무엇인가? | Public import surface |
| [`request.py`](../../src/project_pivot/data_operations/request.py) | 한 번의 실행을 정의하는 입력과 기본값은 무엇인가? | Immutable request와 environment adapter |
| [`runner.py`](../../src/project_pivot/data_operations/runner.py) | raw load와 dbt artifact state가 언제 바뀌는가? | Data-plane 실행과 dbt artifact promotion |
| [`incident_lifecycle.py`](../../src/project_pivot/data_operations/incident_lifecycle.py) | 탐지 이후 어떤 분석을 하고 무엇은 하지 않는가? | Read-only reliability orchestration |
| [`raw_result.py`](../../src/project_pivot/data_operations/raw_result.py) | Raw load caller가 관찰할 수 있는 결과는 무엇인가? | Raw load result contract |
| [`dbt_result.py`](../../src/project_pivot/data_operations/dbt_result.py) | Candidate dbt run을 어떤 identity로 다시 식별하는가? | dbt build result contract |
| [`lifecycle_result.py`](../../src/project_pivot/data_operations/lifecycle_result.py) | Lifecycle이 caller에게 어떤 요약만 반환하는가? | Reliability analysis result contract |
| [`errors.py`](../../src/project_pivot/data_operations/errors.py) | 외부 실행자가 실패 원인을 어디서 읽는가? | Application-level error와 structured context |

## Responsibilities

- `DataOperationRequest`로 실행 설정을 검증한다.
- HMDA raw 적재와 dbt build를 호출한다.
- reliability 분석 단계를 순서대로 조합한다.
- 실행 결과를 Pydantic 모델로 반환한다.
- 외부 실행자가 다룰 수 있는 오류를 `DataOperationError`로 통일한다.

## Public Entry Points

| API | 변경 가능 상태 | Caller가 알아야 할 contract | 결과 |
| --- | --- | --- | --- |
| `load_raw_data()` | DuckDB raw table | 같은 partition을 다시 적재해도 중복 row를 만들지 않는 HMDA ingestion contract에 위임한다. | `RawLoadResult` |
| `run_dbt_build()` | Run-scoped target directory | 성공해도 current artifact를 자동 변경하지 않는다. 이번 run의 verified artifact pair를 반환한다. | `DbtBuildResult` |
| `promote_dbt_artifacts()` | Current dbt artifact projection | 전달된 `DbtBuildResult`의 artifact pair가 build 이후 바뀌지 않았는지 다시 확인한 뒤 current projection을 교체한다. | `None` |
| `run_incident_lifecycle()` | 없음 | Baseline과 실제 current를 비교해 분석만 수행한다. approval, recovery, evaluation은 호출하지 않는다. | `LifecycleResult` |

공개 API와 모델은 [`__init__.py`](../../src/project_pivot/data_operations/__init__.py)에서 확인한다. `runner.run_incident_lifecycle` import path는 기존 caller 호환성을 위해 같은 함수 객체를 re-export한다.

## Data Plane Control Flow

### Raw Load

[`runner.py`](../../src/project_pivot/data_operations/runner.py)의 `load_raw_data()`는 orchestration보다 adapter에 가깝다.

```text
request.source_root
→ hmda_data.discover_hmda_files()
→ DuckDBConnectionManager
→ hmda_data.load_hmda_loans_partition()
→ RawLoadResult
```

`data_operations`는 HMDA 파일 선택이나 partition 적재 알고리즘을 구현하지 않는다. 그 세부 동작은 `hmda_data`가 소유하고, 여기서는 request를 전달하고 실행 결과를 application result로 바꾼다.

### dbt Build: Candidate와 Current를 분리한다

`run_dbt_build()`와 `promote_dbt_artifacts()`는 하나의 작업을 둘로 나눈 API다. 이 분리는 실패한 run이나 아직 채택하지 않은 candidate가 last-known-good current projection을 덮어쓰지 못하게 하는 경계다.

```text
run_dbt_build(request)
  1. unique run target directory 생성
  2. dbt build --target-path <run target> 실행
  3. return code 확인
  4. manifest.json + run_results.json 존재 확인
  5. artifact pair의 projection_id 계산
  6. DbtBuildResult 반환

promote_dbt_artifacts(result, request)
  1. exclusive projection lock 획득
  2. artifact pair 존재 여부 재확인
  3. projection_id 재계산으로 build 이후 변경 여부 확인
  4. temporary/backup file을 사용해 current pair 교체
  5. 실패 시 기존 current pair 복구
```

중요한 invariant는 **`run_dbt_build()` 성공과 current projection 변경이 같은 사건이 아니라는 것**이다. `DbtBuildResult.manifest_path`와 `run_results_path`는 current 경로가 아니라 해당 run에 고정된 candidate 경로다.

Dagster caller는 [`assets.py`](../../src/project_pivot/orchestration/defs/assets.py)에서 이 두 단계를 명시적으로 연속 호출한다.

```text
run_dbt_build(request)
→ promote_dbt_artifacts(result, request)
```

## Reliability Control Flow

[`incident_lifecycle.py`](../../src/project_pivot/data_operations/incident_lifecycle.py)의 `run_incident_lifecycle()`는 reliability domain API를 순서대로 연결한다.

```text
metadata evidence 읽기
→ current ProfileSnapshot 생성
→ baseline/current compatibility 확인
→ incident 전체 탐지
→ 각 detection의 dbt impact 분석
→ 각 impact의 remediation draft 생성
→ content identity + dbt projection identity 고정
→ LifecycleResult로 요약
```

### Compatibility Gate

Baseline은 아무 `ProfileSnapshot`이나 받을 수 있는 것이 아니다. 현재 profile과 `asset_name`, `partition`이 같아야 비교 가능한 baseline으로 인정된다. 이 gate를 통과하지 못하면 `DataOperationError`로 중단한다.

### Incident가 없을 때

Detection이 비어 있으면 downstream impact analysis를 실행하지 않는다. 따라서 recovery proposal에 필요한 `target_content_identity`와 `dbt_projection_id`도 `None`으로 남는다.

### Incident가 있을 때

각 detection은 다음 tuple로 생각하면 된다.

```text
DetectionResult
→ ImpactAnalysisResult
→ RemediationDraft
```

`LifecycleResult`는 이 tuple들을 caller가 소비하기 쉬운 summary로 flatten한다. 여러 incident에서 같은 evidence, asset, action이 반복되면 최초 순서를 유지하면서 중복을 제거한다.

## Core Contracts

[`request.py`](../../src/project_pivot/data_operations/request.py)의 `DataOperationRequest`가 공통 입력이다. 기본값은 로컬 HMDA·DuckDB·dbt 경로를 가리키며, 알 수 없는 필드는 거부되고 model은 변경 불가다.

`data_operation_request_from_environment()`가 해석하는 environment override는 다음 세 개뿐이다.

| Environment | Request field |
| --- | --- |
| `PROJECT_PIVOT_DUCKDB_PATH` | `database_path` |
| `PROJECT_PIVOT_SOURCE_ROOT` | `source_root` |
| `PROJECT_PIVOT_SOURCE_YEAR` | `source_year` |

Dagster의 [`DataOperationsResource`](../../src/project_pivot/orchestration/defs/resource.py)는 이 environment 기반 request를 만든 뒤 명시된 Dagster config만 override한다. 따라서 명시 config가 environment보다 우선한다.

결과 모델은 모두 변경 불가다.

- [`RawLoadResult`](../../src/project_pivot/data_operations/raw_result.py)
- [`DbtBuildResult`](../../src/project_pivot/data_operations/dbt_result.py)
- [`LifecycleResult`](../../src/project_pivot/data_operations/lifecycle_result.py)

`DataOperationError.context`는 subprocess command, return code, artifact path처럼 운영자가 실패를 식별하는 structured detail을 담는다. Caller는 exception message만이 아니라 필요한 경우 이 context를 함께 사용할 수 있다.

## Safety Boundaries

| Boundary | 보존되는 상태 |
| --- | --- |
| dbt build 실패 | 기존 current dbt artifact pair |
| Candidate artifact만 생성 | 기존 current dbt artifact pair |
| Candidate artifact가 build 이후 변경됨 | Promotion 거부, current projection 보존 |
| Promotion 중 file operation 실패 | 가능한 범위에서 기존 current pair 복구 |
| Incident lifecycle 실행 | Raw partition, approval state, recovery/evaluation output을 변경하지 않음 |
| Incident 없음 | Recovery proposal identity를 만들지 않음 |

이 경계의 executable contract는 [`tests/data_operations`](../../tests/data_operations)에서 확인한다. 특히 `test_dbt_runner.py`는 candidate/current 분리와 promotion invariant를, `test_incident_lifecycle.py`는 read-only lifecycle과 ordering을 검증한다.

## Reading Order

처음 읽을 때는 구현 file 순서보다 contract에서 side effect 쪽으로 이동하는 편이 빠르다.

1. [`__init__.py`](../../src/project_pivot/data_operations/__init__.py)에서 public surface를 확인한다.
1. [`request.py`](../../src/project_pivot/data_operations/request.py)에서 한 실행의 입력을 확인한다.
1. [`runner.py`](../../src/project_pivot/data_operations/runner.py)의 public 함수 세 개만 먼저 읽고, private helper는 필요한 invariant를 확인할 때 내려간다.
1. [`assets.py`](../../src/project_pivot/orchestration/defs/assets.py)에서 실제 data-plane caller가 build와 promotion을 어떻게 조합하는지 본다.
1. [`incident_lifecycle.py`](../../src/project_pivot/data_operations/incident_lifecycle.py)에서 read-only reliability 순서를 읽는다.
1. [`test_dbt_runner.py`](../../tests/data_operations/test_dbt_runner.py)와 [`test_incident_lifecycle.py`](../../tests/data_operations/test_incident_lifecycle.py)에서 경계 조건을 확인한다.

새 기능의 상세 규칙을 찾고 있다면 `data_operations` 내부에서 계속 내려가기보다 해당 owner domain으로 이동한다. HMDA 파일·partition 적재는 `hmda_data`, DuckDB와 artifact projection primitive는 `data_platform`, detection·impact·remediation 규칙은 `reliability`가 소유한다.
