# Durable Artifacts

`durable artifact`는 chat 또는 agent session이 끝난 뒤에도 다음 session이나 다른 participant가 작업을 이어받을 수 있도록 repository에 남기는 **non-canonical working artifact**다. `durable`은 artifact type이 아니라 persistence mode이며, 실제 문서 목적에 맞는 `plan`, `brief`, `report`, `review` 같은 type을 그대로 사용한다.

## Activation

Durable artifact는 다음 경우에만 생성하거나 갱신한다.

- 호출자가 명시적으로 durable artifact, checkpoint, session 간 공유 artifact 또는 repository-backed handoff artifact를 요구한다.
- 현재 작업에 적용되는 repository, workflow 또는 agent guidance가 durable artifact 생성을 요구한다.

작업이 길거나 복잡하다는 이유만으로 자동 생성하지 않는다. 활성화되지 않았다면 유용해 보이더라도 repository에 별도 working artifact를 남기지 않는다. Handoff 자체는 artifact 생성을 의미하지 않으며, 실제 handoff에는 [Handoff](handoff.md)를 적용한다.

## Ownership

OpenSpec workflow가 정의한 proposal, design, tasks, review와 그 밖의 OpenSpec artifact는 `openspec/`가 소유한다. 같은 정보를 Inbox에 복제하거나 competing artifact를 만들지 않는다.

이 가이드라인이 활성화된 durable working artifact 중 OpenSpec이 소유하지 않는 것은 `inbox/`가 소유한다. 다만 canonical docs, spec, code, test, configuration처럼 이미 별도 canonical owner가 있는 내용은 해당 owner를 대체하거나 복제하지 않고 필요한 reference와 작업 맥락만 남긴다.

## Create or Update

먼저 현재 change unit에서 같은 목적의 owning artifact가 있는지 확인한다.

- 같은 작업을 이어가기 위한 artifact가 있으면 새 파일보다 기존 artifact 갱신을 우선한다.
- 기존 artifact로 현재 목적을 정확히 표현할 수 없거나 호출자 또는 지침이 별도 artifact를 요구할 때만 새 artifact를 만든다.
- Handoff를 위해 만든다는 이유만으로 `handoff`라는 artifact type을 만들지 않는다. 실제 문서 목적에 맞는 기존 type을 사용한다.
- 새 artifact의 path, naming, frontmatter와 sequence는 [`inbox/AGENTS.md`](../AGENTS.md)의 common contract를 따른다.
- Current owning work unit의 directory를 재사용한다. Branch가 Pull Request를 얻어 directory identity가 전환되면 같은 artifact를 rename된 work unit에서 이어서 사용하고 competing copy를 만들지 않는다.
- 여러 session이나 participant가 같은 mutable artifact를 이어 쓰면 owning ref와 exact path를 source identity로 유지한다.

## Content

다음 session이 이전 chat history 없이도 작업을 재개하는 데 필요한 최소한의 durable context만 남긴다.

- 현재 goal과 scope
- 이미 확정된 결정, 제약과 중요한 전제
- 현재 상태와 완료된 주요 작업
- 다시 확인해야 하는 evidence, revision, path 또는 external reference
- unresolved question, blocker와 next action

원문 대화, 장황한 reasoning, 쉽게 재생성할 수 있는 목록, large log와 canonical source의 복사본은 저장하지 않는다. 현재 상태를 이해하는 데 필요하지 않은 과거 과정은 누적하지 않는다.

## Refresh

Durable artifact가 활성화된 동안 material state가 바뀌거나 handoff가 필요한 시점에 현재 상태를 갱신한다.

- 완료된 항목, 새로운 결정, blocker와 next action이 바뀌면 기존 내용을 현재 사실에 맞게 정리한다.
- 단순 activity log가 목적이 아니라면 최신 상태를 소유하고 오래된 상태를 병렬로 유지하지 않는다.
- 핵심 결정이나 계약이 canonical owner에 반영되면 Inbox에는 필요한 연결과 남은 작업 맥락만 유지한다.
- 작업 종료만을 이유로 artifact를 자동 삭제, archive 또는 이동하지 않는다.

## Boundaries

- Durable artifact는 repository-backed working context이며 runtime session state를 대체하지 않는다.
- OpenSpec artifact의 구조, lifecycle 또는 completion gate는 이 가이드라인이 소유하지 않는다. [`openspec/README.md`](../../openspec/README.md)와 해당 OpenSpec workflow contract를 따른다.
- Durable artifact를 만들라는 요구는 현재 작업 scope를 확장하거나 unrelated repository state를 수정할 권한을 부여하지 않는다.
- Common Inbox ownership, writing과 lifecycle contract는 [`inbox/AGENTS.md`](../AGENTS.md)를 따른다.
