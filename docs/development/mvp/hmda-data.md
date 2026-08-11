# MVP Goal: HMDA Data

## Goal

`volume_drop`을 결정론적으로 만들고 recovery가 안전하게 대상을 식별·교체할 수 있는 partition evidence를 제공한다.

## MVP Responsibilities

- 원천을 수정하지 않고 controlled `volume_drop` 입력을 생성한다.
- 같은 logical partition content를 안정적으로 식별하고 실제 content divergence를 구분한다.
- 승인된 expected state와 현재 state가 다르면 mutation 없이 중단할 수 있는 replacement 경계를 제공한다.

## Done When

- clean, dropped, restored partition의 content identity를 재현 가능하게 비교할 수 있다.
- expected identity가 일치하는 recovery는 target partition을 정확히 복원한다.
- stale 또는 diverged target은 기존 approval로 변경하지 않는다.
- row order나 ingestion timestamp 같은 비본질적 차이는 recovery identity를 흔들지 않는다.

## Non-Goals

- `null_spike`, `schema_drift`, `freshness_delay` recovery
- incident 판단, dbt validation, approval 결정

## References

- [HMDA Data Domain](../../domains/hmda-data.md)
- [MVP Goal](../../mvp.md)
- `tests/hmda_data/`
