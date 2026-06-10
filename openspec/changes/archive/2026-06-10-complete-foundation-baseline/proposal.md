## Why

scratch 문서는 Project Pivot의 방향을 잡았지만, foundation 완료 기준이 OpenSpec contract와 repo 문서에 명시적으로 고정되어 있지 않다. MVP 구현 전에 이미 끝난 기반 작업과 앞으로의 MVP 작업을 분리하고, 검증 가능한 기준선을 남겨야 한다.

## What Changes

- scratch의 proposal, architecture, tech stack, MVP scope, foundation plan을 OpenSpec 기준으로 해석한다.
- foundation 단계의 완료 기준과 제외 범위를 `foundation-baseline` capability로 고정한다.
- 기존 reliability contracts, taxi data foundation, partition ingestion, dbt analytics foundation을 foundation baseline의 증거로 연결한다.
- 아직 MVP 구현에 속하는 profile, detection, impact, remediation, approval/backfill, evaluation 작업은 후속 backlog로 분리한다.
- `scratch/docs` 문서에서 foundation readiness와 다음 작업 순서를 짧게 확인할 수 있게 한다.

## Capabilities

### New Capabilities

- `foundation-baseline`: scratch 기반 foundation 완료 기준, 증거, 후속 MVP 작업 경계를 정의한다.

### Modified Capabilities

- 없음

## Impact

- `openspec/changes/complete-foundation-baseline/` 아래 proposal, design, spec, tasks가 추가된다.
- `scratch/docs/foundation_readiness.md`에 foundation readiness 요약이 추가된다.
- code runtime, API, dependency 변경은 없다.
