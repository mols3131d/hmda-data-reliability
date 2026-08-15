# MVP Documentation Instructions

이 directory는 현재 MVP의 고수준 목표, proof milestone, domain별 목표와 개발 현황을 추적한다.

## Ownership

- [`README.md`](README.md)는 MVP 전체 목표, scope, milestone 순서와 end-to-end proof를 소유한다.
- `milestone-*.md`는 현재 MVP 완료에 필요한 각 proof milestone의 고수준 결과와 완료 경계를 소유한다.
- Domain 문서는 해당 domain의 MVP 목표, 비목표와 완료 관점을 소유한다.
- `status.yml`은 dashboard의 구조화된 current-state 정본이다.
- `status.md`는 `status.yml`에서 렌더링한 사람이 읽는 dashboard다.
- 세부 runtime behavior와 requirement는 OpenSpec Spec과 `docs/domains/**`가 소유한다.

## Milestones

- Milestone은 구현 task 묶음이 아니라 MVP 가치를 독립적으로 검토할 수 있는 proof gate다.
- `milestone-*.md`는 현재 MVP의 end-to-end proof를 구성하는 단계만 다룬다.
- MVP 이후 incident 또는 capability 확장은 MVP scope가 명시적으로 바뀌지 않는 한 이 directory의 milestone으로 추가하지 않는다.
- 각 milestone은 `Goal`, observable `Proof`, `Done When`, `Boundary`만 고수준으로 기록한다.
- API, class, package, fixture와 세부 test scenario는 milestone 문서에 복제하지 않는다.
- 현재 상태와 progress는 milestone 문서에 반복하지 않고 dashboard에서 관리한다.

## Dashboard Model

- Project dashboard는 canonical domain 하나를 한 행으로 사용한다.
- Implementation Requirement는 각 domain의 MVP `Outcomes`를 중복 없는 의미 단위로 정규화해 센다.
- Verification Target은 Requirement를 확인하는 acceptance, invariant 또는 failure path를 의미 단위로 센다.
- task 수와 test function 수를 progress 분모로 사용하지 않는다.
- implementation과 verification의 status, progress와 gap은 서로 분리한다.
- `status.yml`과 `status.md`가 충돌하면 current evidence를 확인해 YAML을 먼저 고치고 Markdown을 다시 렌더링한다.

## Status Evidence

- dashboard에는 snapshot과 관찰한 repository revision, implementation evidence를 기록한다.
- 구현 완료, 검증 완료와 현재 revision 재검증 여부를 구분한다.
- 실행하지 않은 validation을 통과로 기록하지 않는다.
- 구현, Spec 또는 MVP Outcome이 바뀌면 영향받는 Requirement와 Verification Target 분모를 다시 검토한다.
- 완료된 Requirement와 Verification Target은 gap에 남기지 않는다.
- repository lifecycle처럼 구현·검증 coverage와 다른 문제는 progress gap이 아니라 risk로 분류한다.

## Structure

- MVP 책임 또는 명시적 비목표가 있는 canonical domain마다 domain 문서 하나를 둔다.
- Subdomain 문서는 독립적으로 추적할 목표와 경계가 있고 parent 문서가 과도하게 커질 때만 추가한다.
- Domain 문서는 구현 방법보다 목표, 관찰 가능한 완료 결과, 비목표와 canonical reference에 집중한다.
- 현재 구현 상태는 domain 문서에 반복하지 않고 dashboard에서 관리한다.

## Writing

- KISS와 DRY를 따른다.
- 사실, 목표, 비목표와 미검증 상태를 구분한다.
- 숫자나 상태는 재확인 가능한 evidence와 연결한다.
- MVP 밖의 후속 확장을 현재 목표처럼 섞지 않는다.
