# MVP Goal: Data Platform

## Goal

Candidate와 recovery validation 중 dbt evidence의 정체성과 last-known-good 상태를 잃지 않게 한다.

## Outcomes

- candidate와 failed run의 evidence를 current last-known-good evidence와 구분할 수 있다.
- validation이 확인한 dbt evidence와 이후 current로 채택되는 evidence가 같은 pair인지 판정할 수 있다.
- current artifact pair를 갱신하는 동안 reader가 서로 다른 run의 혼합 상태를 정상 current evidence로 보지 않는다.
- candidate 또는 validation 실패가 기존 current evidence를 파괴하지 않는다.

## Non-Goals

- dbt subprocess 실행 순서
- 어떤 candidate를 current로 채택할지 결정하는 application policy
- reliability approval 또는 recovery policy

## References

- [Data Platform Domain](../../domains/data-platform.md)
- [MVP](README.md)
- `tests/data_platform/`
- `tests/dbt/`
