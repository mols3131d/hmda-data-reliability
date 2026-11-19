---
type: design
title: Ingestion Evidence Tool Schemas
description: 실제 적재 범위에 맞춘 원천 스냅샷, 준비 검사, Airflow 결과 연결과 계약 테스트를 정의합니다.
---

# Ingestion Evidence Tool Schemas

## Input Identity

**준비 판정은 실제로 읽은 원천 스냅샷에 결합한다.** 호출자가 허용한 원천 위치와 `source_year`, 선택적 `source_file`, 대상 테이블을 기존 요청에서 가져온다. 현재 `load_raw_data`는 실행 시 원천을 다시 발견하고, 파티션 로더는 전달받은 전체 파일의 구조를 검사한 뒤 요청 범위의 행을 적재한다. 따라서 검사할 파일 집합과 교체할 행의 범위를 모두 기록한다. [적재 진입점](../../../src/hmda_reliability/data_operations/runner.py), [파티션 로더](../../../src/hmda_reliability/hmda_data/ingestion/partition.py)

첫 구현의 원천 버전은 **고정된 읽기 전용 파일 집합의 상대 이름과 내용 SHA-256을 정렬해 만든 목록의 해시**다. 호출자가 고정한 스냅샷이 있으면 재사용한다. 변경 가능한 입력은 허용된 범위와 시간 안에서 이름을 보존한 로컬 스냅샷으로 확보하고, 그 사본에서 버전을 계산하고 읽는다. 원천 목록 전체를 검사할 권한이나 시간 안에 같은 버전을 확보할 수 없으면 확인 가능한 범위와 부족한 근거를 돌려준다. [원천 발견과 파싱 규칙](../../../openspec/specs/hmda-data-ingestion/spec.md)

## Tool Interfaces

| 도구 | 모델이 보내는 인자 | 반환하는 관찰값 |
| --- | --- | --- |
| `list_sources` | 없음 | 고정 범위의 파일 ID와 `csv`·`parquet` 형식 |
| `inspect_source` | 허용된 `source_id` | 파일명에서 얻은 `source_year` 또는 `null`, 누락된 필수 열 |
| `inspect_input_partition` | 없음 | 요청 범위의 `row_count`는 0 이상의 정수 또는 미확인 시 `null`. `parse_status`는 `passed`, `failed`, `not_checked` |
| `read_stage_result` | `raw_load`, `quality_gate`, `dbt_build` 중 허용된 단계 | 지정한 실행·단계의 실제 상태와 연결이 확인된 결과 |

모델에는 자료 ID와 관찰 요약을 보낸다. 읽기 코드가 자료 ID를 허용된 스냅샷 파일이나 실행 기록에 매핑한다. 같은 범위와 버전에서 이미 확보한 관찰값은 재사용한다. 각 조회 결과에는 호출 ID, 상태, 대상, 입력 버전 또는 실행 참조, 관찰 시각을 붙인다.

## Evidence and Failure

| 필수 검사 | 통과 근거 | 위반과 미확인 처리 |
| --- | --- | --- |
| 대상과 원천 범위 | 허용된 범위가 적재기가 읽는 지원 파일 집합을 덮고 대상 연도·파일과 연결된다. | 확정된 빈 원천 집합은 위반이다. 범위 일부를 확인할 수 없으면 미확인으로 남긴다. |
| 파일별 구조 | 실제 적재기에 전달될 모든 파일의 필수 열을 확인했다. | 열 누락은 위반이다. 파일이 보이지 않거나 버전이 달라졌으면 미확인으로 남긴다. |
| 파싱과 대상 행 | 동일한 읽기·필터 규칙으로 격리된 임시 연결에서 대상 입력을 파싱했고, 대상 행 수가 양수다. | 확인한 파싱 오류나 0행은 위반이다. 단순 행 수 조회, 읽기 오류, 시간 초과의 경우 파싱이 확인되지 않은 상태를 기록한다. |

도구 상태 `ok`에는 0이나 빈 목록을 포함해 실제로 관찰한 값을 담는다. `not_found`는 조회할 자료를 확보하지 못한 상태, `error`는 조회 실패다. 그래프는 같은 범위와 버전에서 확인한 관찰에 근거 ID를 발급한다. 파싱과 필수 열 검사는 기존 적재 규칙을 공유한다. [파일별 구조 검사](../../../src/hmda_reliability/hmda_data/ingestion/_common.py), [출력 상태 계약](decision-contract.md#result-contract)

## Airflow Evidence

읽기 어댑터는 Airflow 공개 REST API의 태스크 인스턴스 조회를 사용한다. `raw_load`는 `load_raw_hmda_loans`, `quality_gate`는 `evaluate_quality_gate`, `dbt_build`는 `build_dbt_loan_analytics`로 매핑한다. `dag_id`, `run_id`, `task_id`, `map_index`, `try_number`와 관찰 시각을 결과에 담는다. 현재 DAG는 XCom 저장을 끈다. 성공한 적재의 asset 기록에는 연도·행 수가 있으며, 시도 번호와 원천 버전은 별도로 확인해야 한다. [현재 DAG](../../../src/hmda_reliability/orchestration/dags/hmda_data_plane.py), [Airflow 3.3.0 이벤트 필드](https://github.com/apache/airflow/blob/3.3.0/airflow-core/src/airflow/api_fastapi/core_api/datamodels/assets.py)

- **단계 상태와 데이터 갱신.** `task_state`는 해당 태스크 기록에서 가져온다. 동일 시도에서 갱신을 뒷받침할 때 `update_status=confirmed`와 확인한 행 수를 반환한다. 그 밖에는 `unknown`과 행 수 `null`을 남긴다. 태스크가 실패해도 그 전에 Bronze 트랜잭션이 커밋됐을 수 있다.
- **사전과 사후 비교.** 준비 조사와 실행 기록의 실제 범위·원천 버전이 일치하면 `input_match=matched`로 기록하고 결과를 대조한다. 비교한 값이 다르면 `mismatched`, 어느 한쪽 근거를 확보하지 못하면 `unknown`을 사용한다. 현재 기본 기록만 있을 때는 확인한 단계 상태와 부족한 정보를 보고한다.

정확한 비교가 필요한 운영 경로에서는 적재기가 실제 사용한 범위와 원천 버전을 실행·시도별 기록에 담아 제공한다. 조사기는 이 기록이 있는 실행에서 입력을 대조한다.

## Contract Tests

| 검증할 계약 | 독립적인 기대값 |
| --- | --- |
| 도구의 권한 | 등록되지 않은 도구, 추가 인자, 범위 밖 ID와 한 응답의 복수 조회를 거절한다. 거절된 조회로는 도구 호출과 근거가 생기지 않는다. |
| 준비 검사 | 고정 CSV·Parquet의 필수 열과 대상 행 수가 독립적으로 계산한 값과 일치한다. 파일 하나를 지정해도 전체 입력에서 열 누락을 잡고, 허용 범위·버전 미확인은 `ready`와 구별한다. |
| 판단·조회 연결 | 실제 로컬 조회와 고정 응답 모델로 검증한다. 초기 근거가 다른 두 입력에서 조회나 후속 조치가 달라지고, 같은 근거의 모델 설명만 바뀌면 준비 판정은 같다. |
| 인계와 결과 | 정확한 DAG 실행의 단계 상태를 반환한다. 다른 실행·시도의 행 수나 입력 버전이 부족한 기록은 갱신·일치 여부의 증거로 채택하지 않는다. 조사 전후 임시 Bronze 상태는 같다. |
| 기한과 재현 | 기한이 지난 응답을 저장하고 추가 조회로 이어가지 않는다. 저장된 근거와 고정된 버전으로 오프라인 재현 결과가 일치하며, 필요한 기록이 없으면 이유가 드러난다. |

계약 테스트는 [프로젝트 테스트 설계 기준](../../../docs/development/test-design.md)을 따른다.
