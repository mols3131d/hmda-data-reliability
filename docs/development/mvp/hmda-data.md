# MVP Goal: HMDA Data

## Goal

`volume_drop`을 결정론적으로 재현하고, recovery가 대상 partition의 현재 상태와 복원 결과를 신뢰할 수 있게 한다.

## Outcomes

- 원천을 수정하지 않고 같은 controlled `volume_drop` 입력을 재현할 수 있다.
- 같은 logical partition content와 실제 content divergence를 안정적으로 구분할 수 있다.
- 승인 이후 target이 바뀌면 기존 approval로 mutation하지 않는다.
- 복원 결과가 기대한 partition content와 같은지 검증할 수 있다.

## Non-Goals

- `null_spike`, `schema_drift`, `freshness_delay` recovery
- incident 판단, dbt validation, approval 결정

## References

- [HMDA Data Domain](../../domains/hmda-data.md)
- [MVP Goal](../../mvp.md)
- `tests/hmda_data/`
