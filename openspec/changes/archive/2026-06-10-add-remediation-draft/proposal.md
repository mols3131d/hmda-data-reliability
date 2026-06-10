## Why

impact analysis는 affected assets를 계산하지만 아직 RCA와 조치 초안이 없다. MVP incident lifecycle은 evidence 기반 remediation draft를 만들어 사람이 승인할 수 있는 계획까지 도달해야 한다.

## What Changes

- Incident, Evidence, LineageEvidence를 입력으로 받는 remediation draft workflow를 추가한다.
- LangGraph 기반 triage/rca/plan node를 구성한다.
- 결과를 Pydantic `RemediationDraft`로 검증한다.
- 이상 유형별 test 보강, backfill 준비, validation 액션을 구조화한다.

## Capabilities

### New Capabilities

- `remediation-draft`: evidence 기반 RCA와 remediation 초안을 구조화된 Pydantic 출력으로 생성한다.

### Modified Capabilities

- 없음

## Impact

- `src/project_pivot/reliability/remediation/` 모듈이 추가된다.
- `tests/reliability/test_remediation_draft.py`가 추가된다.
- 기존 `langgraph` dependency를 사용하며 새 dependency는 없다.
