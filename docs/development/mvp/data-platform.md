# MVP Domain Milestone: Data Platform

## Goal

DuckDB Bronze를 최소한의 dbt staging/mart로 변환하고, 데이터와 dbt artifact를
검증 가능한 local Data Lake state로 유지한다.

## Outcomes

- `raw.hmda_loans`가 로컬 DuckDB의 Bronze source로 조회된다.
- dbt staging과 mart가 Bronze를 소비해 분석 가능한 모델을 만든다.
- dbt test와 `manifest.json` / `run_results.json`이 validation evidence로 남는다.
- candidate, failed run과 current last-known-good artifact를 구분할 수 있다.
- current artifact 갱신 중 서로 다른 run의 혼합 상태를 정상 evidence로 노출하지 않는다.

## Done When

같은 local database에서 Bronze → staging → mart를 재현하고, 어떤 dbt artifact pair가
해당 결과를 증명하는지 식별할 수 있으면 완료한다.

## Non-Goals

- cloud warehouse와 distributed query engine
- PyIceberg를 active table engine으로 운영
- 범용 catalog, lakehouse governance와 production retention
- 어떤 candidate를 current로 채택할지 결정하는 application policy

## References

- [Data Platform Domain](../../domains/data-platform.md)
- [MVP](README.md)
- `dbt/`
- `tests/data_platform/`
- `tests/dbt/`
