---
type: review
title: Data Operations Test Design Review
description: Quality gate·dbt 실행과 artifact promotion·incident lifecycle·system recovery 테스트의 설계와 외부 경계를 검토합니다.
---

# Data Operations Test Design Review

> [!NOTE]
> 실제 gate·DB·파일 교체와 system recovery를 함께 검증한다. Artifact pair의 run-results만 바뀌는 분기는 독립 oracle이 부족하다.

- **Target**: Data Operations application composition.
- **Revision**: `3ab899100fc0b35e23d464bd761f3b144a978ae7`.
- **Scope**: test 4개·support 1개·system recovery design 1개 전체. Source·Spec과 인접 artifact identity는 targeted 대조.

## Findings

| ID | Severity | Finding | Action |
| --- | --- | --- | --- |
| D1 | Major | manifest만 identity에 포함하는 잘못된 구현을 현재 promotion oracle이 구별하지 못한다 | run-results만 변경하고 거부·기존 pair 보존 검사 |

## Subdomain Assessment

| Area | Contract And Scenario | Independent Oracle And Strength | Boundary And Limit |
| --- | --- | --- | --- |
| Quality gate | 전체 Bronze profile, 다른 dirty partition, canonical source 제한, empty·NULL discriminator | 실제 DB→profile→policy의 정확한 통과·차단과 reason | [test_quality_gate.py](../../../../tests/data_operations/test_quality_gate.py), policy 자체는 Reliability 리뷰 |
| dbt execution | 누락·stale artifact, timeout, nonzero exit, byte read·lock 실패 | typed failure와 process 진입 여부, 실제 파일 상태 | [test_dbt_runner.py](../../../../tests/data_operations/test_dbt_runner.py); subprocess·일부 gate/lock은 fake |
| Projection promotion | candidate/current 분리, concurrent pair, partial replace rollback, commit 후 release/cleanup | old/new pair와 실제 byte·identity 비교 | manifest-only와 both-files 변경은 있으나 result-only 없음 |
| Incident lifecycle | no incident, 여러 incident 처리·정렬·중복 제거, threshold·baseline mismatch | 실제 detector·impact·draft, current profile과 결과 집합 | [test_incident_lifecycle.py](../../../../tests/data_operations/test_incident_lifecycle.py); dbt artifact는 fixture |
| System recovery | clean→defect→gate block→read-only lifecycle→isolated candidate→approval→recovery→replay | 실제 DuckDB·dbt와 content identity, rejected/stale/actions의 zero mutation | [E2E](../../../../tests/data_operations/test_system_recovery_e2e.py)와 [design S0–S7](../../../../tests/data_operations/test_system_recovery_e2e.design.md); approval은 외부 결정 fixture |

### D1 — Major: Results-Only Projection Drift

#### Locations

- [test_dbt_runner.py](../../../../tests/data_operations/test_dbt_runner.py)
  - 577행은 manifest만, 638행은 두 artifact를 함께 바꾼다.
- [artifacts.py](../../../../src/hmda_reliability/data_platform/artifacts.py)
  - `artifact_pair_identity`: 현재 두 파일의 길이와 bytes를 모두 포함한다.

#### Evidence

잘못된 구현이 manifest만 hash해도 위 변경은 모두 감지한다. Run-results만 달라진 경우를 별도로 검증하지 않으므로, 그 identity 회귀가 promotion에서 stale 결과를 허용하는지 구별하지 못한다. 현재 primitive의 구현은 정상이다.

Batch B의 승인 테스트는 literal ID mismatch, C의 promotion은 두 파일 동시 변경이다. D의 [DAGRun 테스트](../../../../tests/orchestration/test_airflow_dagrun.py) 365행은 runner와 같은 production hash 함수로 equality를 검사하므로 독립 sensitivity oracle이 아니다. 실제 file bytes·모델 status 확인은 유효하지만 manifest-only hash 회귀를 검출하는 별도 근거로 세지 않는다.

#### Impact

승인·promotion이 가리킨 pair와 실제 실행 결과의 변경을 구별해야 하는 경계가 약해진다. 단순 file 존재 검사를 추가하는 것으로 해결되지 않는다.

#### Action

Manifest bytes를 유지하고 run-results bytes만 바꿔 promotion을 요청한다. Typed rejection, 기존 JSON pair의 exact bytes 유지와 partial promotion 부재를 검사한다. 실행으로 확인한 current defect가 아니라 정적 coverage gap이며 후속 구현은 이번 작업에서 하지 않았다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | 독립 body·assertion·design 대조 | Batch A 두 관점의 6파일 전체 검토 |
| ✅ Pass | 현재 suite 실행 | [실행 근거](../validation.md#test-execution); E2E의 실제 dbt 경로 포함 |
| ⚪ Not Verified | result-only negative control | 정적 gap이며 mutation 실행은 하지 않음 |
| ⚪ Not Verified | 실제 사람의 승인·운영 배포 | 명시적인 fixture/exclusion 경계 |

## Risks And Limits

Fake subprocess의 timeout 예외 검사는 실제 process에 `timeout` 인자가 전달됨을 증명하지 않는다. 일부 fake-process test의 request 기본 DB path는 repository의 lock 경로에 접근하므로 향후 fixture를 정리할 때 임시 DB로 격리하는 편이 좋다. 현재 제품 결함으로 재현한 항목은 아니다.

Lifecycle의 단독 no-side-effect 검사는 row count·scratch 부재 범위이고, E2E의 content identity 보존 검사가 이를 보완한다. 실제 Airflow 조합은 [Orchestration 리뷰](../orchestration/README.md)가 별도로 소유한다.
