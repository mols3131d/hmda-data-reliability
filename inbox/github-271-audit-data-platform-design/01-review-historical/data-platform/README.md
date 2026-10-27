---
type: review
title: Data Platform Test Design Review
description: DuckDB·SQL·artifact identity·dbt analytics의 테스트 oracle과 실제 실행 경계 및 누락된 대표 분기를 검토합니다.
---

> [!WARNING]
> Historical evidence only: PR #258 (`bdce0f4e`)의 리뷰 snapshot입니다. 현재 상태·승인·검증 근거로 간주하지 말고 코드 및 Spec에 대조하세요.

# Data Platform Test Design Review

> [!NOTE]
> 실제 dbt build와 exact mart·lineage 검증을 연결한다. Approval 계산의 일부 의미가 fixture에서 구별되지 않는다.

- **Target**: Data Platform, dbt staging/mart와 artifact primitive.
- **Revision**: `3ab899100fc0b35e23d464bd761f3b144a978ae7`.
- **Scope**: [test_duckdb.py](../../../../tests/data_platform/test_duckdb.py), [test_sql.py](../../../../tests/data_platform/test_sql.py), [test_artifacts.py](../../../../tests/data_platform/test_artifacts.py), [test_analytics_foundation.py](../../../../tests/dbt/test_analytics_foundation.py)와 package support 전체. Source·Spec은 targeted 대조.

## Findings

| ID | Severity | Finding | Action |
| --- | --- | --- | --- |
| P1 | Minor | action 2·반복소수·complete-key numeric NULL이 metric oracle에서 구별되지 않는다 | 의미가 다른 고정 입력과 손계산 mart tuple 추가 |

## Subdomain Assessment

아래는 평면 package의 책임별 review view다. 별도 source 하위 package를 새로 정의하지 않는다.

| Area | Contract And Scenario | Independent Oracle | Boundary And Limit |
| --- | --- | --- | --- |
| DuckDB connection | context cleanup, in-memory no-file, body failure 우선, I/O/lock 오류 분리 | 실제 연결 상태·typed failure, relative/symlink 경로 contention | primitive는 실제; read-only 호출이 write 거부까지 검증하는 것은 아님 |
| SQL identifiers/literals | 따옴표·schema/table·string escape | 고정 escape 예시 | Hypothesis의 일부 expected 식은 production과 같아 독립성이 약함 |
| Artifact read/identity | file pair 읽기와 lock 오류 구분 | 실제 byte 읽기와 오류 종류 | pair identity의 result-only 변경은 [Operations D1](https://github.com/mols3131d/hmda-data-reliability/blob/bdce0f4e8e871b1301bac8f8ab3a37c7ba50bd91/inbox/github-258-cover-sdk-retry-classification/03-review-domain-test-design/data-operations/README.md#d1--major-results-only-projection-drift) 보강 필요 |
| dbt staging | 실제 raw→staging→mart, 재실행과 NULL 보존 | 고정 staging row·NULL, mart tuple, source→staging→mart lineage | subprocess와 DuckDB 실제 실행; 운영 규모·다른 adapter는 미검증 |

### P1 — Minor: Analytics Branch Oracle

#### Locations

- [test_analytics_foundation.py](../../../../tests/dbt/test_analytics_foundation.py)
  - 106행 이후 fixture: action `1/3`, rate `0.5/0`.
- [System recovery 테스트](../../../../tests/data_operations/test_system_recovery_e2e.py)
  - 주변 mart fixture도 action 2와 반복소수를 보완하지 않는다.
- [Airflow DAGRun 테스트](../../../../tests/orchestration/test_airflow_dagrun.py)
  - 해당 metric 분기만 targeted 대조했다.

#### Evidence

Approval을 `IN(1,2)` 대신 `IN(1)`로 계산하거나 6자리 반올림을 없애도 현재 exact 결과는 같다. Invalid numeric 입력은 key도 NULL이어서 mart에서 제외되므로, 유효 grain에서 numeric NULL을 제외한 평균 의미까지 구별하지 못한다. 현재 SQL은 정상이며 mutant 실행은 하지 않았다.

#### Impact

실제 dbt build가 통과해도 승인율·평균의 계약 변경을 놓칠 수 있다. 모델 전체가 mock이라는 문제는 아니다.

#### Action

Action 2, 세 행으로 이루어진 grain, key는 완전하고 numeric만 NULL인 행을 추가한다. `0.333333`과 non-null 평균을 손계산한 exact tuple로 비교한다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | 독립 설계 검토 | Batch A 두 관점의 5개 파일 전체와 관련 source·dbt SQL 대조 |
| ✅ Pass | 현재 suite 실행 | 실제 dbt 포함 [실행 근거](https://github.com/mols3131d/hmda-data-reliability/blob/bdce0f4e8e871b1301bac8f8ab3a37c7ba50bd91/inbox/github-258-cover-sdk-retry-classification/03-review-domain-test-design/validation.md#test-execution) |
| ⚪ Not Verified | 위 metric mutant 검출 | 정적 gap이며 mutation 실행은 하지 않음 |

## Risks And Limits

Artifact identity primitive와 promotion composition은 서로 다른 책임이다. 동일한 result-only 공백은 Operations에서 한 번 추적하며 중복 결함 수로 세지 않는다. Lock primitive 통과만으로 모든 caller가 같은 physical DB lock에 연결됨을 보장하지 않는다.
