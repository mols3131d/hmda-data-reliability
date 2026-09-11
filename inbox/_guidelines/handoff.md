# Handoff

`handoff`는 진행 중인 작업을 다른 session, agent 또는 사람에게 넘길 때 **다음 주체가 불필요한 재탐색 없이 이어갈 수 있도록 필요한 작업 delta를 전달하는 행위**다. Handoff는 artifact type이 아니며, 이 가이드라인은 handoff가 발생할 때 전달 내용과 경계를 규정한다.

## Activation

호출자, workflow 또는 applicable guidance가 handoff를 요구하거나 현재 작업이 실제로 다른 주체에게 이관될 때 적용한다. Handoff 자체가 Inbox artifact 생성을 요구하지는 않는다. Repository-backed persistence가 별도로 요구되면 [Durable Artifacts](durable-artifacts.md)를 함께 적용한다.

## Contract

수신자가 다음 행동을 결정하고 실행하는 데 필요한 최소한의 현재 상태만 전달한다.

- 현재 goal, scope와 완료된 핵심 결과
- 아직 끝나지 않은 작업, blocker와 unresolved question
- 이미 내려진 material decision과 수신자가 알아야 하는 예외·제약
- 다음에 수행할 구체적인 action 또는 판단
- continuation에 필요한 exact path, revision, artifact 또는 external reference
- stale 가능성이 있는 상태나 다시 검증해야 하는 사실

결정, 제안, 추측과 미검증 상태가 섞여 있다면 구분한다. Handoff는 현재 authority나 scope를 확대하지 않으며, 기존 owner와 workflow gate를 그대로 따른다.

## Context Boundary

수신자가 harness와 repository discovery를 통해 정상적으로 얻는 context는 handoff에 복제하지 않는다. 필요한 경우 해당 source의 존재를 다시 설명하기보다 현재 작업에서 **그 context 때문에 달라진 결정이나 예외**만 전달한다.

다음은 기본적으로 다시 적지 않는다.

- root 또는 path-scoped repository instructions
- harness가 자동으로 제공하거나 로드하는 project/runtime context
- 일반 Skill, Rule, workflow 사용법
- canonical docs, OpenSpec artifact, PR description 또는 source file의 장문 복사본
- GitHub나 repository에서 직접 확인할 수 있는 전체 file inventory와 일반 상태

정확한 continuation point를 식별하는 데 path, commit, PR, artifact reference가 필요하면 짧게 남긴다.

## Anti-Patterns

- **Harness context dump** — 수신자가 자동으로 받는 지침, Skill, Rule이나 project context를 다시 나열한다.
- **Transcript handoff** — 대화 전문, 장황한 reasoning 또는 작업 과정을 시간순으로 재현한다.
- **Inventory dump** — 관련 파일, commit, check와 artifact를 중요도 없이 대량 나열한다.
- **Canonical duplication** — canonical source나 OpenSpec owning artifact의 내용을 handoff에 복제해 두 번째 source of truth를 만든다.
- **Vague continuation** — `계속 진행`, `검토 필요`처럼 다음 행동이나 판단 대상을 식별하지 않는다.
- **State without freshness** — mutable state를 revision이나 재검증 필요 여부 없이 현재 사실처럼 전달한다.
- **Mixed authority** — 확정된 결정, 제안과 개인적 추측을 같은 수준의 지침처럼 쓴다.
- **Scope transfer by implication** — handoff를 이유로 수신자에게 기존에 없던 권한이나 작업 범위를 암묵적으로 부여한다.

## Durable Handoff

Handoff 내용을 repository에 지속해야 한다면 새 `handoff` type을 만들지 않는다. 실제 문서 목적에 맞는 기존 artifact type을 사용하고, 같은 작업의 owning artifact가 있으면 새 파일보다 갱신을 우선한다.

상태가 이미 OpenSpec workflow artifact에 소유되어 있으면 해당 artifact를 갱신하거나 참조하고 competing Inbox artifact를 만들지 않는다. OpenSpec이 소유하지 않는 durable working context는 Inbox common contract와 [Durable Artifacts](durable-artifacts.md)를 따른다.

## Boundaries

- Handoff는 새로운 requirement, decision authority 또는 canonical contract를 만드는 절차가 아니다.
- 수신자가 직접 확인 가능한 current state를 불필요하게 snapshot하지 않는다.
- Secret, large log, raw generated output 또는 재생성 가능한 장문 evidence를 handoff에 포함하지 않는다.
- Inbox에 저장되는 경우 common ownership, writing과 lifecycle contract는 [`inbox/AGENTS.md`](../AGENTS.md)를 따른다.
