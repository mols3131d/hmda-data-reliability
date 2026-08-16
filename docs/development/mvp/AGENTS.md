# MVP Documentation Instructions

이 directory는 Project Pivot MVP의 전체 목표, domain별 완료 경계와 현재 상태를 관리한다.

## Ownership

- [`README.md`](README.md)는 MVP 전체 목표, scope, domain milestone과 완료 기준을 소유한다.
- Domain 문서는 해당 domain이 MVP에서 증명해야 하는 결과와 완료 경계를 소유한다.
- `status.yml`은 current-state의 구조화된 정본이다.
- `status.md`는 `status.yml`을 사람이 읽기 쉽게 표현한 dashboard다.
- 세부 runtime behavior와 requirement는 OpenSpec Spec과 `docs/domains/**`가 소유한다.

## Domain Milestones

- MVP milestone은 개발 순서가 아니라 domain별 **완료 gate**다.
- 현재 canonical domain인 HMDA Data, Data Platform, Data Operations, Reliability,
  Orchestration을 기준으로 문서 하나씩 둔다.
- 각 domain 문서는 `Goal`, `Outcomes`, `Done When`, `Non-Goals`, `References`에 집중한다.
- API, class, fixture와 세부 test scenario는 반복하지 않는다.
- 현재 상태와 progress는 domain 문서가 아니라 dashboard에서 관리한다.
- 새로운 canonical domain이 생기지 않는 한 MVP 편의를 위해 별도 domain을 만들지 않는다.

## Agentic Boundary

- 최소 Agentic capability는 Reliability MVP에 포함한다.
- LLM은 deterministic incident evidence와 `RemediationDraft`를 읽고 설명·검토·보강한다.
- LLM 출력은 approval 또는 recovery 명령이 아니며 deterministic guardrail을 우회하지 않는다.
- MVP 문서는 특정 model provider나 LLMOps vendor를 필수 dependency로 만들지 않는다.
- autonomous recovery, multi-agent orchestration과 production-grade prompt platform은 MVP 밖이다.

## Status Model

- task 수, test function 수 또는 임의의 `x/y` progress를 MVP 진행률로 사용하지 않는다.
- 각 domain은 `done`, `partial`, `blocked` 중 하나의 state와 구체적인 gap으로 표시한다.
- 구현 완료와 current revision 검증 여부를 분리한다.
- 실행하지 않은 validation을 통과로 기록하지 않는다.
- MVP 전체는 모든 domain gate가 `done`이고 current revision acceptance가 확인되어야 완료다.

## Writing

- KISS와 DRY를 따른다.
- 목표, 현재 사실, 비목표와 미검증 상태를 구분한다.
- 후속 capability를 현재 MVP 완료 조건에 섞지 않는다.
- 외부 research는 참고할 수 있지만 canonical 목표는 이 directory 안에서 자족적으로 설명한다.
