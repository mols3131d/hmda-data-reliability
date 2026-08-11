# MVP Goal: Data Platform

## Goal

Candidate와 recovery validation 중 기존 last-known-good dbt evidence를 보존하고, 검증 대상 artifact pair를 하나의 projection으로 식별할 수 있게 한다.

## MVP Responsibilities

- run-scoped dbt artifact를 shared current projection과 분리할 수 있는 기반을 제공한다.
- `manifest.json`과 `run_results.json`의 pair identity와 projection read/lock 경계를 제공한다.
- failed candidate가 기존 current projection의 lineage·validation evidence를 파괴하지 않게 한다.

## Done When

- candidate artifact pair를 current projection과 혼동하지 않고 식별할 수 있다.
- failed validation 이후에도 prior current artifact pair를 읽을 수 있다.
- promotion에 사용되는 artifact pair가 validation에서 확인한 projection과 동일함을 검증할 수 있다.

## Non-Goals

- dbt subprocess 실행 순서와 promotion 호출 결정
- reliability approval 또는 recovery policy

## References

- [Data Platform Domain](../../domains/data-platform.md)
- [MVP Goal](../../mvp.md)
- `tests/data_platform/`
- `tests/dbt/`
