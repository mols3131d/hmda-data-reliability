---
type: review
title: HMDA Ingestion Test Design Review
description: 원천 검증, full load, partition 교체와 provenance 테스트가 실제 데이터 손상을 검출하는지 검토합니다.
---

# HMDA Ingestion Test Design Review

> [!NOTE]
> 값·partition 보존 oracle은 강하다. 다중 파일의 schema 검증과 교체 중간 실패는 보강이 필요하다.

- **Target**: HMDA Data ingestion.
- **Revision**: `3ab899100fc0b35e23d464bd761f3b144a978ae7`.
- **Scope**: [full-load 테스트](../../../../tests/hmda_data/test_ingestion.py), [partition 테스트](../../../../tests/hmda_data/test_ingestion_partition.py), fixture와 실제 loader·Spec 대조.

## Findings

| ID | Severity | Finding | Action |
| --- | --- | --- | --- |
| F1 | Major | 정상 파일과 필수 컬럼 누락 파일을 함께 넣으면 잘못된 성공을 놓친다 | 파일별 누락 검증의 회귀 사례 추가 |
| F2 | Major | DELETE 이후 INSERT 실패의 rollback을 직접 관찰하지 않는다 | 중간 fault와 기존 행 집합 보존 검사 추가 |
| F3 | Major | 파일 단위 교체가 같은 연도의 다른 파일을 삭제해도 놓칠 수 있다 | 같은 연도 A/B seed 후 A 교체, B 전체 행 보존 검사 |
| F4 | Minor | 대기 테스트의 fake lock이 실제 DB path 연결 오류를 가릴 수 있다 | file connection의 canonical lock 연결 검사 |

## Design Assessment

| Area | Independent Oracle And Strength | Boundary |
| --- | --- | --- |
| Discovery/full load | 지원 파일의 정렬된 정확한 목록, 반복 적재의 고정 행 수·provenance SQL 비교 | 실제 임시 CSV/Parquet와 DuckDB 사용 |
| Column order | 재정렬된 입력에서 고정 금액·소득을 비교하고 다른 연도 행도 보존 | 행 수만 맞는 값 뒤바뀜을 검출 |
| Scoped replacement | 연도·파일 선택, 반복 적재, stale identity·temporal state, metadata 보존·거부 | 실제 DB 상태 비교; expected identity는 사전 상태 |
| Failure | malformed CSV, missing file/column, mutation lock 실패 | lock 오류는 주입; parse·storage는 실제 경로 |

### F1 — Major: Mixed Source Schema

#### Locations: F1

- [test_ingestion.py](../../../../tests/hmda_data/test_ingestion.py)
  - `test_load_hmda_loans_validates_required_columns`: 누락 파일 하나만 입력한다.
- [_source_query.py](../../../../src/hmda_reliability/hmda_data/ingestion/_source_query.py)
  - `source_union_sql`: `UNION ALL BY NAME`으로 파일을 결합한다.
- [ingestion Spec](../../../../openspec/specs/hmda-data-ingestion/spec.md)
  - `Source contract validation`.

#### Evidence: F1

필수 컬럼이 모두 있는 파일과 `income`만 없는 파일을 함께 입력하면 full·partition loader 모두 2행 적재 성공을 반환하고, 잘못된 파일의 `income`은 `NULL`이 된다. [A1 재현](../validation.md#a1-mixed-source-schema)을 caller가 실행했다. 기존 단일 파일 검사와 정상 CSV/Parquet 혼합 검사는 이 조합을 검출하지 않는다.

#### Impact: F1

파일의 구조 오류가 정상적인 null 값처럼 저장된다. 이는 원천 null을 보존하는 정책과 별개인 파일별 필수 컬럼 계약 위반이다.

#### Action: F1

정상+누락 파일을 함께 넣는 full·partition 회귀 사례를 만들고 누락 컬럼의 validation failure를 요구한다. Full load의 기존 validation-after-replacement 의미와 partition의 기존 행 보존 의미는 각각 유지해 검사한다. 이번 보고 작업에서는 구현하지 않았다.

### F2 — Major: Mid-Replacement Rollback

#### Locations: F2

- [test_ingestion_partition.py](../../../../tests/hmda_data/test_ingestion_partition.py)
  - stale expected-state와 invalid provenance의 mutation 전 거부 검사.
- [partition.py](../../../../src/hmda_reliability/hmda_data/ingestion/partition.py)
  - `_replace_partition_in_transaction`, `_replace_partition_rows`.

#### Evidence: F2

현재 구현은 DELETE와 INSERT를 transaction으로 묶는다. 기존 rejection 사례는 destructive DELETE 전 종료하므로, transaction 경계가 사라져 DELETE 후 INSERT 오류가 기존 행을 잃게 해도 해당 rejection oracle은 통과할 수 있다. 실제 구현 결함이나 mutation 실행 결과로 주장하지 않는 정적 coverage gap이다.

#### Impact: F2

후속 입력 쓰기가 실패해 기존 partition을 잃는 회귀는 mutation 전 거부 테스트만으로 검출할 수 없다.

#### Action: F2

대상 partition과 다른 partition을 먼저 저장한 뒤 DELETE 이후 INSERT에만 오류를 주입한다. 예외와 재조회한 양쪽 전체 행 집합, staging 정리를 확인한다. 단순 mock 호출 횟수보다 원상복구를 oracle로 삼는다.

### F3 — Major: Same-Year Sibling Preservation

#### Locations: F3

- [test_ingestion_partition.py](../../../../tests/hmda_data/test_ingestion_partition.py)
  - 393행의 file-scoped test는 빈 target에서 시작한다.
  - 61행의 다른 partition 보존은 다른 연도다.
- [partition.py](../../../../src/hmda_reliability/hmda_data/ingestion/partition.py)
  - `_source_file_filter`, `_replace_partition_rows`.

#### Evidence: F3

현재 file predicate는 정상이다. 하지만 DELETE에서 file predicate를 빠뜨린 구현은 빈 target의 file-scoped test와 다른 연도 보존을 모두 통과할 수 있다. 같은 연도에 이미 저장된 sibling 파일의 행이 없어 이 손실을 관찰하지 못한다. Evaluation의 selected-source 사례에도 persisted sibling 보호가 없음을 targeted 대조했다. Mutation 실행으로 확인한 결과는 아니다.

#### Impact: F3

파일 하나를 복구하려는 요청이 같은 연도의 다른 파일까지 삭제하는 회귀를 놓칠 수 있다.

#### Action: F3

같은 연도의 A/B 파일을 먼저 적재하고 A의 값만 바꿔 file-scoped reload한다. A의 정확한 새 값과 B의 전체 행·provenance가 유지되는지 비교한다.

### F4 — Minor: Loader Lock Identity

#### Locations: F4

- [test_ingestion_partition.py](../../../../tests/hmda_data/test_ingestion_partition.py)
  - 201행의 writer 대기 테스트는 DB 인자를 버리고 자체 Lock을 사용한다.
- [test_duckdb.py](../../../../tests/data_platform/test_duckdb.py)
  - primitive의 relative/symlink alias contention은 별도로 보호한다.

#### Evidence: F4

대기 순서는 검사하지만 loader가 실제 file DB 대신 `None`을 lock에 전달하는 회귀는 fake lock이 가릴 수 있다. 현재 path 전달과 primitive는 정상이다. File connection에서 같은 physical DB의 canonical lock에 연결되는 작은 composition 사례를 후속으로 권한다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | 독립 설계 검토 | Batch A quality/adversarial의 test body·fixture·관련 계약 대조 |
| ✅ Pass | 현재 정상 suite 실행 | [실행 근거](../validation.md#test-execution), 도메인별 pass 수로 재배분하지 않음 |
| ❌ Fail | 혼합 schema 계약 probe | full·partition에서 누락 파일을 성공 처리 |
| ⚪ Not Verified | 중간 실패 negative control | 정적 분석이며 fault/mutation suite는 미실행 |
