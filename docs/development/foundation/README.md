# Foundation (Draft)

이 폴더는 foundation에서 **어디까지 다룰지** 적어 둔 작업 초안이다. 확정 명세가 아니며, 수정·삭제·보관될 수 있다.

## 범위

| 주제 | 문서 |
| --- | --- |
| 원천 데이터 적재 | [Bronze](data-pipeline-bronze.md) |
| dbt 변환 | [Silver](data-pipeline-silver.md), [Gold](data-pipeline-gold.md) |
| 데이터 탐색 | [EDA](eda.md) |
| 관찰 근거 | [Observability](observability.md) |
| 실행 경계 | [Orchestration](orchestration.md) |
| Reliability | [Reliability](reliability.md) |
| 완료 판단 | [Readiness](readiness.md) |

## 후속 후보

- profile snapshot과 incident detection
- downstream impact analysis와 remediation draft
- approval 이후 backfill·validation
- synthetic case evaluation report

## 공통 기준

- 작게 시작하고, 필요한 규칙만 적는다.
- 관찰한 사실과 아직 모르는 것을 구분한다.
- 원천 데이터는 자동 삭제하거나 임의로 고치지 않는다.
- 위험한 작업은 사람의 승인 뒤 별도 실행 경계에서 수행한다.
- 자세한 구현 규칙은 이 폴더에 복사하지 않는다.

## 아직 정하지 않은 것

- foundation 완료를 판단할 최소 기준
- Gold mart의 최종 grain과 grouping
- notebook smoke의 실행 방식
