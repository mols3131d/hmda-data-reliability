---
type: review
title: Airflow DAG Test Design Review
description: 실제 DAG의 dependency와 DAGRun 실패·성공·event·artifact oracle 및 배포 범위 제한을 검토합니다.
---

> [!WARNING]
> **Historical evidence only:** PR #258 (`bdce0f4e`), 당시 테스트 설계 기록. 현재 main 검증·승인 완료를 의미하지 않습니다. 이 PR에서 근거를 다시 확인하고 채택 여부를 판정하세요.

# Airflow DAG Test Design Review

> [!NOTE]
> 실제 graph와 CLI 실행을 연결해 task 순서·차단·부작용을 검증한다. Production scheduler 전체와 hash algorithm 독립성까지 보장하는 증거는 아니다.

- **Target**: Orchestration dags 하위 패키지.
- **Revision**: `3ab899100fc0b35e23d464bd761f3b144a978ae7`.
- **Scope**: [test_airflow_dag.py](../../../../tests/orchestration/test_airflow_dag.py), [test_airflow_dagrun.py](../../../../tests/orchestration/test_airflow_dagrun.py), [design](../../../../tests/orchestration/test_airflow_dagrun.design.md) 전체.

## Findings

이 하위 패키지에 추가로 채택한 material finding은 없다. 365행의 artifact projection equality는 production 함수를 재사용하므로 manifest-only hash 회귀를 구별하는 독립 oracle로 세지 않는다. [Operations D1](https://github.com/mols3131d/hmda-data-reliability/blob/bdce0f4e8e871b1301bac8f8ab3a37c7ba50bd91/inbox/github-258-cover-sdk-retry-classification/03-review-domain-test-design/data-operations/README.md#d1--major-results-only-projection-drift)에 한 번 추적한다.

## Design Assessment

| Layer | What Is Observed | Strength And Limit |
| --- | --- | --- |
| Definition | 정확한 task·edge·asset·parameter 집합, retry·XCom policy | DAG 테스트 17·48·67행, 실제 DAG object |
| Disabled | 비활성 시 task 상태·실행 부재 | DAGRun 262행, 단순 wrapper mock이 아님 |
| Raw failure | load 실패 후 downstream 차단·event 부재 | 278행, 실제 CLI와 metadata DB |
| Gate failure | quality gate 실패 후 analytics 미실행 | 296행, 실제 DuckDB profile·policy |
| Success | task timestamp 순서, exact row/profile/mart, asset events, XCom 부재 | 320행, 실제 Airflow·dbt·SQLite·DuckDB |
| dbt failure | 실패 task·downstream/event와 기존 artifact 상태 | 391행, 실제 실패 실행 |
| Artifact copy | candidate/current manifest·results bytes 일치와 model status | 360–364행, hash equality와 독립적인 유효한 byte oracle |

이 묶음은 CI와 같은 로컬 CLI DAGRun의 대표 5경로다. Scheduler daemon, 외부 executor, 여러 worker와 production 운영 주기는 design의 제외 범위다. Explicit config와 임시 경로를 통해 운영 DB에 의존하지 않는다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | 독립 body·design·source 대조 | Batch D 두 관점 |
| ✅ Pass | 현재 실제 CLI DAGRun | caller 5 passed / 106.76s, [실행 기록](https://github.com/mols3131d/hmda-data-reliability/blob/bdce0f4e8e871b1301bac8f8ab3a37c7ba50bd91/inbox/github-258-cover-sdk-retry-classification/03-review-domain-test-design/validation.md#test-execution) |
| ⚪ Not Verified | 분산·운영 scheduler 증거 | 실행하지 않은 명시적 범위 |
