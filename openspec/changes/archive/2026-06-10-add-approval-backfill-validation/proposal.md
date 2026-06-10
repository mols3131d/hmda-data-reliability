## Why

remediation draft는 backfill 필요성을 제안하지만, MVP는 승인 없는 재처리를 금지해야 한다. approval gate 이후 partition overwrite와 profile 재검증까지 이어져야 incident lifecycle이 닫힌다.

## What Changes

- `ApprovalStatus.APPROVED`일 때만 partition backfill을 실행하는 안전 인터페이스를 추가한다.
- 승인된 backfill 후 `ProfileSnapshot`을 자동 재생성하는 validation 결과를 추가한다.
- 미승인 상태에서는 source 접근이나 target 변경 전에 도메인 예외를 발생시킨다.

## Capabilities

### New Capabilities

- `approval-backfill-validation`: approval gate 이후 partition backfill과 profile validation을 실행한다.

### Modified Capabilities

- 없음

## Impact

- `src/project_pivot/reliability/recovery/` 모듈이 추가된다.
- `tests/reliability/test_approval_backfill_validation.py`가 추가된다.
- 기존 DuckDB ingestion/profile builder를 조합하며 새 dependency는 없다.
