## Context

현재 repo에는 scratch 문서와 여러 OpenSpec archive가 함께 존재한다. scratch는 방향과 원칙을 설명하고, archived OpenSpec 변경은 실제 contract/data/ingestion/dbt 기반 구현 증거를 담고 있다.

문제는 foundation 완료 판단이 한 곳에 없다. 앞으로 profile, detector, impact analysis 같은 MVP 기능을 시작하려면 foundation에서 무엇이 완료되었고 무엇이 아직 후속 작업인지 구분되어야 한다.

## Goals / Non-Goals

**Goals:**

- scratch 문서를 foundation baseline의 입력 근거로 사용한다.
- 이미 완료된 OpenSpec capability를 foundation 증거로 연결한다.
- MVP 이전 기반과 MVP 구현 작업을 분리한다.
- 다음 작업자가 테스트 가능한 acceptance criteria를 보고 이어갈 수 있게 한다.

**Non-Goals:**

- 새 runtime 기능 구현
- detector, LangGraph, Dagster asset graph 구현
- dbt 모델 확장
- production 배포 구성
- dashboard UI 구성

## Decisions

### Foundation baseline은 새 capability로 둔다

`foundation-baseline` capability는 기존 `reliability-contracts`, `taxi-data-foundation`, `partition-ingestion`, `dbt-analytics-foundation`을 대체하지 않는다. 각 capability의 완료 증거를 묶어 MVP 진입 기준을 설명한다.

대안: 기존 capability 중 하나에 요구사항을 추가한다. 하지만 foundation baseline은 cross-cutting 상태 판단이므로 특정 기능 spec에 넣으면 책임이 섞인다.

### scratch 문서는 source input으로 남긴다

scratch 문서 내용을 그대로 반복하지 않고, 핵심 기준만 OpenSpec과 `scratch/docs/foundation_readiness.md`에 반영한다.

대안: scratch 전체를 docs로 승격한다. 하지만 proposal, architecture, tech stack, scope가 서로 일부 반복하므로 foundation 완료 기준이 다시 흐려질 수 있다.

### Foundation 이후 작업은 backlog/OpenSpec 후보로 유지한다

profile snapshot, incident detection, impact analysis, remediation draft, approval/backfill/validation, evaluation report는 MVP 구현 단계다. foundation 완료 판단에는 포함하지 않는다.

대안: 이번 변경에서 다음 기능까지 구현한다. 하지만 scratch의 foundation non-goal과 충돌한다.

## Risks / Trade-offs

- [Risk] 문서성 capability라 테스트가 약해 보일 수 있다. -> spec scenario를 파일 존재, OpenSpec archive, 검증 명령 기준으로 둔다.
- [Risk] backlog 초안과 OpenSpec archive가 중복되어 혼란을 줄 수 있다. -> readiness 문서에서 완료된 foundation archive와 다음 backlog를 분리해 보여준다.
- [Risk] scratch 입력 메모와 readiness 문서가 동시에 남아 오래되면 내용이 갈라질 수 있다. -> `foundation_readiness.md`는 현재 기준선, 나머지 scratch 문서는 입력 메모로 취급한다.
