# Human Handoff

`handoff-human`은 agent가 사람에게 작업 상태, 판단 요청 또는 다음 행동을 넘길 때 적용하는 [Handoff](handoff.md)의 확장 가이드라인이다. 공통 handoff contract를 유지하면서 **가시성, 가독성, 판단 비용과 attention budget**을 더 엄격하게 다룬다.

## Activation

Agent가 사람에게 review, 승인, 선택, 보완 작업, blocker 해소 또는 작업 continuation을 넘길 때 적용한다. 단순 진행 보고나 정보 제공이 실제 handoff가 아니라면 이 가이드라인을 강제하지 않는다.

## Leading Information

문서나 메시지 상단만 읽어도 다음을 판단할 수 있어야 한다.

- 현재 상태 또는 핵심 결과가 무엇인지
- 사람의 판단이나 행동이 필요한지
- 필요하다면 무엇을 결정하거나 해야 하는지
- 작업을 막는 blocker나 중요한 risk가 있는지

사람의 action이 필요하지 않다면 그렇게 명확히 표현한다. 중요한 요청이나 blocker를 배경 설명 뒤에 숨기지 않는다.

## Presentation

사람에게는 전체 agent execution context가 아니라 **판단에 필요한 정보와 선택지**를 전달한다.

- 결론과 action을 먼저 두고 근거와 세부사항을 뒤에 둔다.
- 짧은 prose나 list로 충분하면 복잡한 table, tree 또는 대형 section 구조를 만들지 않는다.
- 같은 상태, 결론이나 요청을 heading, callout, summary와 closing에서 반복하지 않는다.
- 긴 evidence, diff, log 또는 세부 작업 기록은 owning artifact나 직접 확인 가능한 source로 연결한다.
- 여러 선택지가 있으면 실제 decision dimension과 material trade-off만 비교한다.
- path, commit, PR, check와 artifact reference는 사람이 직접 확인하거나 다음 행동에 필요한 것만 남긴다.

## Content

공통 handoff 정보 중 사람의 판단에 필요한 내용만 남긴다.

- 완료된 결과와 아직 남은 일
- 인간에게 필요한 decision, approval 또는 action
- 선택지가 있다면 차이를 만드는 핵심 trade-off
- material risk, blocker와 unresolved uncertainty
- 필요한 validation 상태와 신뢰할 수 있는 evidence pointer
- 사람이 선택한 뒤 agent가 이어서 할 수 있는 다음 단계

Agent 내부 orchestration, tool sequence, harness loading 과정, 일반 repository guidance와 이미 source에서 확인 가능한 세부사항은 기본적으로 제외한다.

## Anti-Patterns

- **Agent payload dump** — agent-to-agent handoff처럼 장황한 context, state, path와 세부 작업을 대량 전달한다.
- **Buried ask** — 사람이 해야 할 결정이나 행동을 긴 배경 설명의 끝에 배치한다.
- **Poor visibility** — 핵심 상태, blocker, 실패 또는 risk가 첫 부분에서 보이지 않는다.
- **Wall of text** — scan point 없이 긴 문단과 세부사항을 연속해서 적는다.
- **Decorative structure** — 정보량에 비해 과도한 heading, table, callout 또는 visual을 사용해 오히려 읽기 어렵게 만든다.
- **Evidence flooding** — raw diff, full log, transcript 또는 모든 finding detail을 본문에 붙여 넣는다.
- **False completeness** — 미검증 상태나 uncertainty를 숨기고 사람이 승인하기 쉬운 요약만 남긴다.
- **Context repetition** — harness, repository instructions, OpenSpec contract 또는 이미 연결된 owning artifact의 내용을 다시 설명한다.
- **No decision framing** — 선택을 요구하면서 각 선택의 의미, trade-off 또는 기본적으로 권장되는 다음 행동을 식별하지 않는다.

## Detail Boundary

사람이 직접 읽을 필요가 없는 세부 작업 맥락은 handoff 본문에 넣지 않는다. 세션 간 continuity 때문에 보존할 가치가 있다면 별도 durable working artifact 또는 기존 owning artifact에 두고 human handoff에서는 필요한 위치만 연결한다.

세부 내용이 OpenSpec artifact, review artifact, canonical document, code, test 또는 GitHub state에 이미 존재하면 그 source를 우선한다. Human handoff는 해당 내용을 다시 소유하지 않는다.

## Boundaries

- 이 가이드라인은 human-readable presentation과 decision handoff만 확장한다. 공통 scope, authority와 context boundary는 [Handoff](handoff.md)를 따른다.
- 사람에게 넘겼다는 이유만으로 Ready, approval, merge, destructive action 또는 권한 확대를 암묵적으로 승인받은 것으로 해석하지 않는다.
- 인간이 요청하지 않은 상세 agent trace나 내부 작업 기록을 readability 명목으로 별도 생성하지 않는다.
- Repository에 저장되는 handoff 관련 artifact는 [`inbox/AGENTS.md`](../AGENTS.md)와 적용되는 durable artifact contract를 따른다.
