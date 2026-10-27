---
type: review
title: HMDA Synthetic Test Design Review
description: 합성 결함의 크기·결정성·연도·경로 격리와 원본 보존 테스트를 검토합니다.
---

# HMDA Synthetic Test Design Review

> [!NOTE]
> 결함 지표와 결정성은 실제 출력으로 확인한다. 출력과 입력 경로가 겹칠 때 원본 보존을 놓친다.

- **Target**: HMDA Data synthetic.
- **Revision**: `3ab899100fc0b35e23d464bd761f3b144a978ae7`.
- **Scope**: [test_synthetic.py](../../../../tests/hmda_data/test_synthetic.py), 실제 generator·writer·Spec과 연결된 evaluation safeguard.

## Findings

| ID | Severity | Finding | Action |
| --- | --- | --- | --- |
| F1 | Major | source가 교체할 case directory 안에 있으면 삭제되지만 테스트는 입력·출력을 항상 분리한다 | 경로 중첩 거부와 원본 byte 보존 회귀 추가 |
| F2 | Minor | row-drop 직접 oracle에 희소 연도가 없어 연도 소실을 놓칠 수 있다 | 한 행짜리 연도를 포함한 두 연도의 exact 출력 검사 |

## Design Assessment

| Area | Independent Oracle And Strength | Boundary |
| --- | --- | --- |
| Row drop | 실제 Parquet 행 수와 입력 순서·컬럼 순서가 다른 동치 데이터의 선택 결과 | 실제 DuckDB sampling·파일 사용 |
| Null spike | 높은 기존 null 비율, 부분 sample, 정수 cross-product로 엄격한 증가 확인 | production float 계산 복제를 피함 |
| Distribution | 연도별 요청 비율의 observable null 수 | 전체 증가만으로 연도 편중을 숨기지 않음 |
| Invalid requests | all-null·missing column·fraction·case name 오류와 output 부재 | `..` 거부가 source/output 중첩까지 보장하지 않음 |
| Schema drift | 출력 physical type이 실제 변경됐는지 조회 | review 품질·실제 장애 빈도를 평가하는 test가 아님 |

### F1 — Major: Overlapping Input And Output

#### Locations: F1

- [test_synthetic.py](../../../../tests/hmda_data/test_synthetic.py)
  - 원천 fixture와 output root를 분리하고 traversal sentinel을 검사한다.
- [_writer.py](../../../../src/hmda_reliability/hmda_data/synthetic/_writer.py)
  - `_prepare_case_dir`: 기존 case directory를 재귀 삭제한다.
- [synthetic Spec](../../../../openspec/specs/hmda-data-synthetic-defects/spec.md)
  - `Isolated synthetic output`: 원천 파일 불변.

#### Evidence: F1

`cases/row_count_drop/year_2025.csv`를 source로, `cases`를 output root로 지정한 caller [A2 probe](../validation.md#a2-synthetic-source-preservation)에서 `SyntheticCaseError` 후 source가 사라졌다. Case name은 정상 단일 이름이므로 기존 traversal 검사는 이를 차단하지 않는다.

#### Impact: F1

synthetic 생성 실패가 원본 데이터 손실을 동반할 수 있다. 경로 overlap이 현재 API에서 명시적으로 거부되지 않으며 source 불변 계약에 예외도 없다.

#### Action: F1

원천이 교체될 case directory 내부인 경우를 생성 전 거부하도록 후속 수정하고, 성공·실패 모두 원본의 존재와 bytes가 유지되는지 검증한다. 단순 output 부재나 예외 type만으로 끝내지 않는다. 이번 작업은 보고만 수행했다.

### F2 — Minor: Sparse-Year Row Drop

#### Locations: F2

- [test_synthetic.py](../../../../tests/hmda_data/test_synthetic.py)
  - 23행과 310행의 직접 row-drop oracle은 단일 연도다.
- [cases.py](../../../../src/hmda_reliability/hmda_data/synthetic/cases.py)
  - `_sample_limit_sql`: 현재 연도별 최소 한 행을 보존한다.

#### Evidence: F2

전체 population을 한 번에 sampling해 작은 연도를 없애는 구현도 단일 연도 oracle은 통과할 수 있다. 현재의 연도별 최소 한 행 처리는 정상이며 mutation 실행은 하지 않았다. 한 행짜리 연도와 여러 행짜리 연도를 함께 넣고 각 연도의 exact 행 수·값을 비교하는 보강을 권한다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | 독립 테스트 설계 검토 | Batch A 두 관점의 body·실제 writer·Spec 대조 |
| ✅ Pass | 현재 suite 실행 | [실행 근거](../validation.md#test-execution) |
| ❌ Fail | 원본 보존 probe | 임시 원천 파일이 호출 후 삭제됨 |
