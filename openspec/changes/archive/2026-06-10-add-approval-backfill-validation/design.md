## Context

MVP의 조치 초안은 `prepare_partition_backfill`과 validation action을 제안한다. 실행 단계는 human approval이 명시적으로 승인된 경우에만 ingestion overwrite를 호출해야 한다.

## Goals / Non-Goals

**Goals:**

- `Approval` contract로 위험 작업 실행 가능 여부를 판별한다.
- 승인 후 yellow taxi partition overwrite를 실행한다.
- overwrite 완료 후 같은 partition의 `ProfileSnapshot`을 재생성한다.
- 실행 결과를 Pydantic 모델로 반환한다.

**Non-Goals:**

- Dagster asset job 구현
- 분산 backfill orchestration
- approval UI
- 자동 승인 또는 승인 우회

## Decisions

### Recovery 모듈로 분리한다

approval gate와 backfill 실행은 detection/remediation 책임이 아니다. `reliability.recovery`는 승인된 조치 실행과 검증만 담당한다.

### 승인 확인을 가장 먼저 수행한다

미승인 요청은 source path 유효성, table 생성, delete/insert 전에 실패해야 한다. 테스트는 존재하지 않는 source라도 approval 예외가 먼저 발생하는지 검증한다.

### ProfileSnapshot을 validation 결과로 둔다

사후 검증은 MVP에서 profile 재생성을 기준으로 삼는다. 결과 모델은 row count와 snapshot을 함께 반환해 후속 evaluation이 참조할 수 있게 한다.

## Risks / Trade-offs

- [Risk] 현재 backfill은 yellow taxi partition loader에 특화되어 있다. -> MVP 대상 data source가 NYC Taxi이므로 범위를 고정하고, 일반화는 후속 change로 둔다.
- [Risk] validation이 profile 재생성에 머문다. -> dbt build 검증은 기존 dbt foundation과 report 단계에서 별도 실행한다.
