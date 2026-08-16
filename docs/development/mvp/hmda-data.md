# MVP Domain Milestone: HMDA Data

## Goal

로컬 HMDA 원천을 안전하게 발견·검증하고 DuckDB Bronze가 사용할 수 있는 재현 가능한
입력과 synthetic reliability case를 제공한다.

## Outcomes

- CSV/Parquet 원천을 명시적인 file과 partition identity로 다룰 수 있다.
- full 또는 partition ingestion에 필요한 source metadata를 안정적으로 제공한다.
- 같은 입력의 재실행이 의도하지 않은 duplicate state를 만들지 않는다.
- 원본 파일을 수정하지 않고 controlled synthetic defect를 만들 수 있다.
- Reliability와 recovery가 비교할 수 있는 content evidence를 제공한다.

## Done When

대표 HMDA fixture를 반복 실행해 같은 logical source와 partition을 식별할 수 있고,
Bronze ingestion과 synthetic case가 원천을 훼손하지 않음을 검증하면 완료한다.

## Non-Goals

- 원천 다운로드와 외부 catalog
- 다수 dataset을 위한 범용 connector framework
- dbt 변환, incident 판단, LLM 분석 또는 approval 결정

## References

- [HMDA Data Domain](../../domains/hmda-data.md)
- [MVP](README.md)
- `tests/hmda_data/`
