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
| Synthesis | Lead |
| Decision authority | human or owning workflow |

Session window는 timebox이지 turn quota가 아니다. 더 긴 window나 추가 topic은 discussion goal에 필요한 이유가 있을 때만 사용한다.

Provider-specific task ID, recurrence syntax, model name, trigger interval과 notification 설정은 이 guide가 소유하지 않는다. Scheduler/host의 현재 authoritative configuration을 따른다.

## Scheduled State

Lead는 시작 시 `README.md`에 scheduled execution과 확인 가능한 session state를 기록한다.

```yaml
execution: scheduled
participants: [a, b]
```

Scheduler/host가 shared session start/end를 명시적으로 제공하면 해당 값을 기록할 수 있다. 제공되지 않은 deadline을 추정하지 않는다.

Phase, topic, scope, decision criteria, current state, references와 synthesis는 `discuss.md`의 common bundle contract를 따른다.

## One Invocation = One Contribution

각 scheduled invocation은 다음 중 하나만 수행한다.

```text
read persisted state
→ check phase + eligibility
→ run common Turn Workflow
→ persist one participant turn or allowed shared-state update
→ exit
```

Lead가 Converge phase에서 synthesis eligible이면:

```text
read persisted state
→ verify convergence state
→ synthesize or revise synthesis
→ persist shared state
→ exit
```

하나의 invocation 안에서 상대의 미래 turn을 기다리거나 delayed second participant turn을 시도하지 않는다. 다음 exchange는 scheduler/host의 다음 invocation이 진행한다.

## Phase-Aware Scheduling

Scheduler는 phase를 결정하지 않는다. Persisted discussion state와 `discuss.md`의 phase transition criteria가 다음 useful contribution을 결정한다.

### Frame

- Lead가 frame proposal을 작성한다.
- 상대 participant가 framing bias, missing alternative, scope와 criteria를 검토할 invocation 기회를 가진다.
- Material framing objection이 남으면 Lead invocation이 이를 무시하고 Evidence로 전환하지 않는다.

### Evidence

- 가능한 경우 A와 B 각각에게 independent evidence contribution 기회를 준다.
- Scheduler가 같은 participant만 반복 호출해 evidence diversity를 대체하지 않는다.
- Participant가 아직 자신의 independent evidence pass를 하지 않았다면 상대 recommendation에 대한 단순 반응보다 independent evidence를 우선한다.

### Dialectic

- Scheduler는 persisted move에 따라 next eligible participant를 호출한다.
- Thesis, antithesis, synthesis authorship을 Lead에게 고정하지 않는다.
- Synthesis candidate가 게시되면 상대 participant에게 adversarial challenge 기회를 먼저 준 뒤 Converge eligibility를 판단한다.

### Converge

- Lead가 synthesis를 작성할 수 있다.
- Scheduler/host가 허용하면 non-lead에게 synthesis omission/misrepresentation review 기회를 제공한다.
- Review 기회가 없었다면 synthesis는 persisted explicit agreement 이상을 mutual consensus로 표현하지 않는다.

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

Phase transition을 위해 shared state를 갱신하는 Lead invocation도 persisted objections를 먼저 확인한다. Lead privilege는 turn eligibility나 phase criteria를 우회하지 않는다.

## Lead Workflow

Lead는 common participant role에 coordination을 추가로 맡는다.

1. Frame에서 question, scope, criteria, role과 phase state를 제안한다.
2. 상대의 material framing objection을 summary에 정확히 반영한다.
3. Phase transition criteria를 충족한 경우에만 `README.md` phase를 갱신한다.
4. Dialectic에서는 Lead 자신의 proposal을 shared truth로 취급하지 않는다.
5. Converge에서는 persisted strongest case, agreement, disagreement와 evidence gap을 보존해 synthesis한다.

Lead는 `README.md`, 자신의 turns와 synthesis authoring을 소유하지만 truth, tie-break 또는 decision authority를 소유하지 않는다.

## Counterpart Workflow

Non-lead participant는 common Turn Workflow를 독립적으로 수행한다.

1. Frame에서 lead framing 자체를 challenge할 수 있다.
2. Evidence에서 상대가 제시하지 않은 evidence path를 우선 탐색한다.
3. Dialectic에서 반박 전에 상대 strongest claim을 steelman한다.
4. Synthesis candidate를 challenge할 때 omitted constraint, unsupported assumption과 false compromise를 우선 확인한다.
5. Material objection이 없으면 convergence/no-finding signal을 한 번 남길 수 있다.

Non-lead는 자신의 turns만 소유한다. Shared-state 변경은 turn에서 제안한다.

## Session Window

- 한 번에 하나의 topic만 active로 유지한다.
- 시간이 남는다는 이유로 topic, dialectic cycle 또는 turn을 추가하지 않는다.
- Common stop condition이 먼저 충족되면 session window가 남아 있어도 Converge/synthesis로 이동할 수 있다.
- Shared session expiry가 확인되면 새 argumentative turn을 시작하지 않는다.
- Expiry 이후 Lead가 별도 synthesis invocation을 받을 수 있다면 persisted turns만 기준으로 synthesis한다.

Scheduler가 호출을 놓쳤더라도 sequence나 phase를 추측으로 건너뛰지 않는다. Latest valid persisted state에서 다시 시작한다.

## Recovery

- Missing prerequisite 또는 duplicate invocation → no-op.
- Stale state 또는 write conflict → refresh 후 current phase/eligibility에서 재시도.
- Missed turn → latest valid turn에서 resume.
- Phase state가 turn evidence와 모순 → turn evidence를 재검토하고 shared state를 정정한 뒤 계속.
- Missing material evidence → participant가 `Next: research`를 기록하고 필요한 경우 Lead가 topic을 blocked/paused로 표시.
- Session expiry → 새 argumentative turn 금지; 가능한 경우 Converge/synthesis로 전환.
- Scheduler failure → discussion state를 추측으로 advance하지 않는다.

Scheduled protocol은 scheduler가 A/B를 호출할 수 있다는 것만 가정한다. Scheduler-specific retry policy, recurrence expression, queue semantics와 notification은 외부 runtime이 소유한다.

## Boundaries

- 이 extension은 `discuss.md`의 phase lifecycle, bundle, ownership, turn quality, topic scope, synthesis와 decision authority를 변경하지 않는다.
- `discuss-chatbot.md`와 같은 participant 실행에 동시에 적용하지 않는다.
- Scheduling infrastructure 자체를 discussion artifact 안에서 구현하지 않는다.
- Elapsed time, invocation 수 또는 scheduler order를 deeper reasoning이나 evidence quality의 대리값으로 사용하지 않는다.
- Shared session expiry를 확인하지 못했으면 임의로 deadline을 만들지 않는다.
