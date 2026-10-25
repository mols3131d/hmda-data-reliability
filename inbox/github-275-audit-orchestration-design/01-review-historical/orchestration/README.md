---
type: review
title: Orchestration Test Design Review
description: Config 변환·task application boundary·DAG dependency·실제 DAGRun 테스트를 층별로 검토합니다.
---

> [!WARNING]
> **Historical evidence only:** PR #258 (`bdce0f4e`), 당시 테스트 설계 기록. 현재 main 검증·승인 완료를 의미하지 않습니다. 이 PR에서 근거를 다시 확인하고 채택 여부를 판정하세요.

# Orchestration Test Design Review

> [!NOTE]
> Config·wrapper 단위와 실제 DAGRun을 함께 사용해 순서·실패·event 경계를 확인한다. 이 범위에서 추가 material finding은 확인하지 못했다.

- **Target**: Orchestration config·execution와 dags 하위 패키지.
- **Revision**: `3ab899100fc0b35e23d464bd761f3b144a978ae7`.
- **Scope**: test 4개·initializer 1개·DAGRun design 1개 전체를 두 관점 독립 검토. 관련 source·Spec 대조.

## Findings

채택한 material finding은 없다. Artifact hash의 독립 sensitivity 공백은 [Operations D1](https://github.com/mols3131d/hmda-data-reliability/blob/bdce0f4e8e871b1301bac8f8ab3a37c7ba50bd91/inbox/github-258-cover-sdk-retry-classification/03-review-domain-test-design/data-operations/README.md#d1--major-results-only-projection-drift)에 연결하며 같은 결함을 중복 세지 않는다.

## Subdomain Assessment

| Area | Contract And Oracle | Boundary And Limit |
| --- | --- | --- |
| Config | exact path/year/boolean, explicit > env > default, invalid env masking·validation | [test_config.py](../../../../tests/orchestration/test_config.py) 13·19·34·53·64·73·82·87행, 실제 변환 사용 |
| Application execution | exact event·exception/cause, 실패 시 event 부재 | [test_airflow_execution.py](../../../../tests/orchestration/test_airflow_execution.py) 68·124·153·179·216·240·264·280행; domain 함수는 fake |
| DAG definition | actual task/dependency/asset/parameter set, retry·XCom policy | [DAG 리뷰](dags.md), 실제 DAG object 검사 |
| DAGRun | disabled·raw failure·gate failure·success·dbt failure의 실제 task 상태와 DB·artifact·event | [DAG 리뷰](dags.md), 별도 직렬 실행 |

Wrapper를 수동으로 순서대로 호출하는 test만으로 scheduler ordering을 증명하지 않는다. 여기서는 별도 실제 DAG graph와 CLI DAGRun이 그 의미를 보완한다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | 독립 full-body·design 검토 | Batch D 두 관점 6파일 |
| ✅ Pass | 현재 실제 DAGRun 5사례 | caller 직렬 실행 5 passed / 106.76s |
| ✅ Pass | 나머지 현재 tests | [전체 suite](https://github.com/mols3131d/hmda-data-reliability/blob/bdce0f4e8e871b1301bac8f8ab3a37c7ba50bd91/inbox/github-258-cover-sdk-retry-classification/03-review-domain-test-design/validation.md#test-execution)에 포함, 중복 합산 없음 |
| ⚪ Not Verified | scheduler daemon·분산 배포 | design의 명시적 exclusion |
