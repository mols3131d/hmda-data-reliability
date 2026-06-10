## Context

Incident lifecycle의 evidence inventory는 profile snapshot과 dbt lineage뿐 아니라 table metadata도 포함한다. MVP에서는 Apache Iceberg catalog 전체 구현 대신 DuckDB table에서 schema/row count metadata를 결정적으로 조회한다.

## Goals / Non-Goals

**Goals:**

- DuckDB table metadata를 조회한다.
- 결과를 `EvidenceSource.TABLE_METADATA` Evidence로 반환한다.
- payload에 schema hash, columns, row_count를 포함한다.

**Non-Goals:**

- Apache Iceberg catalog 연동
- snapshot history 저장소
- column-level lineage
- UI catalog 조회

## Decisions

### Evidence contract를 재사용한다

metadata 전용 모델 대신 기존 `Evidence` contract를 사용해 detector/RCA가 같은 evidence_refs 흐름을 유지한다.

### schema hash는 profile helper와 공유한다

동일 table schema에 대해 profile snapshot과 metadata evidence가 같은 hash 계산 규칙을 쓰도록 `calculate_schema_hash`를 재사용한다.

### table-level partition token을 허용한다

Evidence contract는 partition 필드를 요구한다. table metadata는 기본값 `table`을 사용해 partition-level evidence와 구분한다.

## Risks / Trade-offs

- [Risk] DuckDB metadata는 Iceberg snapshot metadata보다 표현력이 낮다. -> MVP 재현성을 우선하고 Iceberg catalog는 후속 확장으로 둔다.
