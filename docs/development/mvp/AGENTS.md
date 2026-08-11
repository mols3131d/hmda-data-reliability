# MVP Documentation Instructions

이 directory는 현재 MVP의 domain별 목표와 개발 현황을 추적한다.

## Ownership

- [`docs/mvp.md`](../../mvp.md)는 MVP 전체 목표와 end-to-end proof를 소유한다.
- Domain 문서는 해당 domain의 MVP 목표, 비목표와 완료 관점을 소유한다.
- `status.md`는 현재 구현·검증 상태의 유일한 dashboard다.
- 세부 runtime behavior와 requirement는 OpenSpec Spec과 `docs/domains/**`가 소유한다.

## Status Evidence

- `status.md`에는 snapshot 날짜, 관찰한 repository revision과 implementation evidence를 기록한다.
- 구현 완료, 검증 완료와 현재 revision 재검증 여부를 구분한다.
- 실행하지 않은 validation을 통과로 기록하지 않는다.
- 구현이나 Spec이 바뀌면 영향받는 domain 상태와 dashboard를 함께 검토한다.
- 같은 current-state 판단을 별도 파일에 수동 복제하지 않는다.

## Structure

- MVP 책임 또는 명시적 비목표가 있는 canonical domain마다 domain 문서 하나를 둔다.
- Subdomain 문서는 독립적으로 추적할 목표와 경계가 있고 parent 문서가 과도하게 커질 때만 추가한다.
- Domain 문서는 구현 방법보다 목표, 관찰 가능한 완료 결과, 비목표와 canonical reference에 집중한다.
- 현재 구현 상태는 domain 문서에 반복하지 않고 `status.md`에서 관리한다.

## Writing

- KISS와 DRY를 따른다.
- 사실, 목표, 비목표와 미검증 상태를 구분한다.
- 숫자나 상태는 재확인 가능한 evidence와 연결한다.
- MVP 밖의 후속 확장을 현재 목표처럼 섞지 않는다.
