# Foundation

Foundation phase의 작업 문서와 완료 판단을 모은다.

- [`readiness.md`](readiness.md)와 [`readiness.yml`](readiness.yml)은 현재 완료 판단, evidence inventory와 validation 상태를 기록한다.
- 나머지 문서는 Foundation 범위를 설명하는 supporting document다.
- 시스템의 canonical behavior contract는 OpenSpec Spec과 domain 문서가 소유한다.

## Scope

| 주제 | 문서 |
| --- | --- |
| 원천 데이터 적재 | [Bronze](data-pipeline-bronze.md) |
| dbt 변환 | [Silver](data-pipeline-silver.md), [Gold](data-pipeline-gold.md) |
| 데이터 탐색 | [EDA](eda.md) |
| 관찰 근거 | [Observability](observability.md) |
| 실행 경계 | [Orchestration](orchestration.md) |
| Reliability | [Reliability](reliability.md) |
| 완료 판단 | [Readiness](readiness.md) |

## Common Criteria

- 관찰한 사실과 아직 모르는 것을 구분한다.
- 원천 데이터는 자동 삭제하거나 임의로 고치지 않는다.
- 위험한 작업은 사람의 승인 뒤 별도 실행 경계에서 수행한다.
- 자세한 구현 규칙이나 canonical contract를 이 폴더에 복사하지 않는다.
