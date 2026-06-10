## Why

MVP scope는 profile/lineage뿐 아니라 대표 table metadata를 evidence로 조회할 수 있어야 한다. 현재 `EvidenceSource.TABLE_METADATA` contract는 있지만 DuckDB table metadata를 Evidence로 만드는 실행 경로가 없다.

## What Changes

- DuckDB table schema와 row count를 `Evidence` contract로 반환하는 metadata evidence builder를 추가한다.
- metadata evidence payload에 schema hash, column 목록, row count를 포함한다.
- table metadata 조회 실패를 도메인 예외로 감싼다.

## Capabilities

### New Capabilities

- `table-metadata-evidence`: DuckDB table metadata를 구조화된 Evidence로 조회한다.

### Modified Capabilities

- 없음

## Impact

- `src/project_pivot/reliability/metadata/` 모듈이 추가된다.
- `tests/reliability/test_table_metadata_evidence.py`가 추가된다.
- 기존 DuckDB/profile helper를 재사용하며 새 dependency는 없다.
