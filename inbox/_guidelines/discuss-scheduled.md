# Scheduled Discussion

이 guide는 scheduler, host 또는 external runner가 A/B participant를 **예약된 invocation으로 반복 실행하는 asynchronous discussion**을 정의한다.

기본 discussion 계약은 [`discuss.md`](discuss.md)를 따른다. 이 extension은 scheduled cadence, session window, invocation lifecycle과 scheduled recovery만 소유한다.

## Use When

다음이 모두 가능할 때 사용한다.

- A와 B가 같은 persisted discussion bundle을 읽고 쓸 수 있다.
- scheduler/host가 participant를 나중에 다시 호출할 수 있다.
- 각 invocation은 durable state를 읽고 한 번의 eligible contribution을 persist할 수 있다.

Scheduler가 없거나 단일 response runtime 안에서 계속 토론해야 하면 이 extension을 사용하지 않는다. Active single-response 방식은 [`discuss-chatbot.md`](discuss-chatbot.md)를 사용한다.

## Defaults

| Field | Default |
| --- | --- |
| Lead | A |
| Topics | 1 primary, optional 1 secondary |
| Active topics | 1 |
| Session | 6–12 hours |
| Exchange | iterative |
| Synthesis | A |
| Decision authority | human or owning workflow |

Session window는 timebox이지 turn quota가 아니다. 더 긴 window나 추가 topic은 discussion goal에 필요한 이유가 있을 때만 사용한다.

Provider-specific task ID, recurrence syntax, model name, trigger interval과 notification 설정은 이 guide가 소유하지 않는다. Scheduler/host의 현재 authoritative configuration을 따른다.

## Scheduled State

A는 시작 시 `README.md`에 scheduled mode와 확인 가능한 session state를 기록한다.

```yaml
mode: scheduled
participants: [a, b]
```

Scheduler/host가 shared session start/end를 명시적으로 제공하면 해당 값을 기록할 수 있다. 제공되지 않은 deadline을 추정하지 않는다.

Topic, scope, current state, references와 synthesis는 `discuss.md`의 common bundle contract를 따른다.

## One Invocation = One Contribution

각 scheduled invocation은 다음 중 하나만 수행한다.

```text
read persisted state
→ check eligibility
→ run common Turn Workflow
→ persist one participant turn
→ exit
```

또는 A가 synthesis eligible이면:

```text
read persisted state
→ synthesize
→ persist shared state
→ exit
```

하나의 invocation 안에서 상대의 미래 turn을 기다리거나 delayed second turn을 시도하지 않는다. 다음 exchange는 scheduler/host의 다음 invocation이 진행한다.

## Eligibility

`discuss.md`의 persisted latest-turn 규칙을 그대로 사용한다.

```text
A1 → B1 → A2 → B2 → ...
```

- no turn → A
- latest A → B
- latest B → A
- discussion/topic closed → no argumentative turn

Invocation이 자신의 차례가 아니면 새 turn을 만들지 않는다. Missing prerequisite, duplicate invocation 또는 이미 소비한 state는 no-op으로 종료하고 다음 scheduled invocation에 맡긴다.

## A Lead Workflow

A는 common participant role에 Moderator coordination을 추가로 맡는다.

1. 첫 eligible invocation에서 active topic과 evidence baseline을 `README.md`에 정리한다.
2. 이후 A turn에서는 B의 latest material claim과 strongest evidence를 먼저 검증한다.
3. Topic transition과 shared Current State는 A가 관리한다.
4. Common stop condition 또는 session expiry가 확인되면 새 argumentative turn 대신 synthesis를 수행한다.

A는 `README.md`, A turns와 synthesis를 소유한다.

## B Challenger Workflow

B는 common Turn Workflow를 독립적으로 수행한다.

1. A의 framing을 기본 전제로 받아들이지 않고 중요한 evidence와 assumption을 확인한다.
2. strongest counterexample, omitted alternative, trade-off 또는 reason to agree를 찾는다.
3. B turn만 수정한다. Shared-state 변경은 `Next`에서 제안한다.
4. Material objection이 없으면 convergence/no-finding signal을 한 번 남길 수 있다.

B는 B turns만 소유한다.

## Session Window

- 한 번에 하나의 topic만 active로 유지한다.
- 시간이 남는다는 이유로 topic이나 turn을 추가하지 않는다.
- Common stop condition이 먼저 충족되면 session window가 남아 있어도 synthesize할 수 있다.
- Shared session expiry가 확인되면 새 argumentative turn을 시작하지 않는다.
- Expiry 이후 A가 별도 synthesis invocation을 받을 수 있다면 persisted turns만 기준으로 synthesis한다.

Scheduler가 호출을 놓쳤더라도 sequence를 건너뛰지 않는다. Latest valid persisted turn에서 다시 시작한다.

## Recovery

- Missing prerequisite 또는 duplicate invocation → no-op.
- Stale state 또는 write conflict → refresh 후 current eligibility에서 재시도.
- Missed turn → latest valid turn에서 resume.
- Missing material evidence → participant가 `Next: research`를 기록하고 필요한 경우 A가 topic을 blocked로 표시.
- Session expiry → 새 argumentative turn 금지; 가능한 경우 A synthesis로 전환.
- Scheduler failure → discussion state를 추측으로 advance하지 않는다.

Scheduled protocol은 scheduler가 A/B를 호출할 수 있다는 것만 가정한다. Scheduler-specific retry policy, recurrence expression, queue semantics와 notification은 외부 runtime이 소유한다.

## Boundaries

- 이 extension은 `discuss.md`의 bundle, ownership, turn quality, topic scope, synthesis와 decision authority를 변경하지 않는다.
- `discuss-chatbot.md`와 같은 participant 실행에 동시에 적용하지 않는다.
- Scheduling infrastructure 자체를 discussion artifact 안에서 구현하지 않는다.
- Elapsed time이나 invocation 수를 deeper reasoning의 증거로 취급하지 않는다.
- Shared session expiry를 확인하지 못했으면 임의로 deadline을 만들지 않는다.
