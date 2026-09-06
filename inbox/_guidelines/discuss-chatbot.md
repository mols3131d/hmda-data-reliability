# Chatbot Discussion

이 guide는 두 개의 챗봇이 같은 repository의 `inbox/`를 공유하면서 **각자 하나의 response runtime 안에서 지속적으로 조사하고 상대 턴을 확인하며 토론하는 방식**을 정의한다.

기본 bundle, turn ownership, immutable turn, turn quality, synthesis와 discussion artifact 원칙은 [`discuss.md`](discuss.md)를 따른다. 이 guide가 명시적으로 선택된 경우에만 **runtime cadence와 invocation lifecycle**에 한해 `discuss.md`의 `One Invocation = One Turn` 규칙 대신 이 guide를 적용한다.

## Use When

다음 조건을 모두 만족할 때 사용한다.

- 두 chatbot이 같은 discussion bundle을 읽고 쓸 수 있다.
- 각 chatbot이 하나의 response runtime 동안 shared state를 여러 번 새로 읽을 수 있다.
- 상대를 기다리는 동안 idle하지 않고 관련 Research를 계속해야 한다.
- caller가 active session duration을 지정했거나 기본 25분 session을 사용한다.

이 mode는 scheduler가 나중에 chatbot을 다시 호출하는 방식이 아니다. **각 chatbot이 현재 단일 response를 계속 실행하면서** Research와 shared-state refresh를 반복한다.

환경이 이 실행 모델을 지원하지 않으면 active session을 수행했다고 가장하지 않고 일반 `discuss.md`의 Manual 또는 Scheduled cadence를 사용한다.

## Core Loop

Response runtime이 살아 있는 동안 다음 loop를 계속 수행한다.

```text
상대 상태 확인
→ 새 상대 turn이 있으면 읽고 필요한 최소 검증
→ 내 차례이면 response turn publish
→ bounded Research slice 1개
→ 상대 상태 다시 확인
→ 반복
```

### Non-Termination Invariants

다음은 **response 종료 사유가 아니다.**

1. 자신의 turn을 publish했다.
2. 상대가 아직 새 turn을 publish하지 않았다.
3. 현재 latest turn이 자신의 것이다.
4. 잠정 convergence가 생겼다.
5. 당장 새로운 반론이 떠오르지 않는다.

이 경우에도 Research와 상대 상태 확인을 계속한다. `sleep`, idle wait 또는 의미 없는 polling으로 시간을 소비하지 않는다. **대기 시간은 Research 시간이다.**

## Session

기본 session은 25분이며 caller가 다른 값을 명시하면 그 값을 사용한다. A는 session 시작 시 `README.md`에 최소한 다음을 기록한다.

```yaml
mode: chatbot-active-session
started_at: <timestamp>
ends_at: <timestamp>
participants: [a, b]
```

A와 B는 같은 `ends_at`을 따르고 각 loop에서 deadline을 확인한다.

Deadline이 가까워지면 새 큰 Research question이나 새 topic을 시작하지 않는다. Platform이나 provider가 response runtime을 강제로 종료하는 경우 가능한 마지막 시점에 현재 상태를 durable artifact에 남긴다.

## Roles

A는 participant이면서 coordination과 synthesis를 소유한다.

- discussion bundle과 `README.md`를 생성한다.
- 첫 eligible turn을 작성한다.
- A turn과 shared topic state를 관리한다.
- session 종료 시 synthesis를 작성한다.

B는 independent challenger다.

- A가 만든 bundle에 참여한다.
- B turn만 작성한다.
- A의 framing을 기본적으로 신뢰하지 않고 evidence와 counterexample을 확인한다.
- shared state 변경이 필요하면 자신의 turn에서 제안한다.

A와 B는 고정된 찬반 진영이 아니다. 더 강한 evidence가 나오면 입장을 바꾼다.

## Bootstrap

A는 discussion bundle과 session metadata를 만든 뒤 `discuss.md`의 공통 Turn Workflow에 따라 **초기 Research → Plan → Implement → Review**를 수행하고 첫 turn을 publish한다. Publish 직후 종료하지 않고 Active Research Loop로 들어간다.

B가 시작했을 때 bundle 또는 첫 A turn이 아직 없다면 **종료하지 않는다.** Caller가 제공한 topic과 repository context를 기준으로 bounded Research slice를 수행하고, slice가 끝날 때마다 bundle과 A turn 생성 여부를 다시 확인한다.

```text
B 시작
→ bundle/A turn 확인
→ 없음: Research slice
→ 다시 확인
→ 없음: 다음 Research slice
→ 발견: 읽고 검증 후 eligible turn publish
```

B는 A보다 먼저 discussion bundle이나 B turn을 만들지 않는다.

## Turn Order

Turn은 discussion-global sequence를 사용한다.

```text
001-a.md
002-b.md
003-a.md
004-b.md
...
```

매 publish 직전에 `turns/`를 다시 읽어 current sequence와 eligibility를 확인한다.

- turn이 없으면 A만 eligible하다.
- latest valid turn이 A면 B만 eligible하다.
- latest valid turn이 B면 A만 eligible하다.

이미 소비한 상대 turn에 다시 답하지 않는다. 자신의 turn이 latest이면 새 self-turn을 만들지 않고 Research를 계속한다.

이미 publish된 turn은 rewrite하지 않는다. Stale state나 write conflict가 발생하면 최신 persisted state를 다시 읽고 current sequence에서 계속한다.

## Active Research Loop

상대의 새 turn을 기다리는 동안 현재 topic의 결론을 바꿀 가능성이 있는 **가장 작은 Research question 하나**를 선택한다.

Research 우선순위는 다음과 같다.

1. current canonical repository contract와 applicable guidance
2. current implementation, tests와 runtime evidence
3. 관련 inbox research/discussion
4. 판단에 실제 도움이 될 때만 external authoritative source

한 Research slice는 하나의 bounded question 또는 몇 개의 밀접한 evidence check만 다룬다. **Research slice 하나가 끝나면 다음 slice를 시작하기 전에 반드시 상대 상태를 확인한다.**

```text
Research slice
→ check opponent
→ no new turn: next Research slice
→ new turn: read + minimal verify + respond when eligible
→ Research 계속
```

새 상대 turn이 발견되면 새로운 Research slice를 시작하지 않는다. 상대 주장을 판정하는 데 필요한 최소 검증만 수행한 뒤 turn에 응답한다.

Research 결과가 중요하지만 아직 자신의 turn 차례가 아니라면 새 self-turn을 만들지 않는다. 다음 eligible turn에서 반영한다.

## Research Saturation

새로운 자료를 찾는 것만 Research로 취급하지 않는다. 새 source가 더 이상 현재 topic의 판단을 바꾸지 않는다면 범위를 넓히지 말고 다음 방향으로 전환한다.

1. 가장 강한 현재 근거를 다시 검증한다.
2. 핵심 가정의 반례를 찾는다.
3. 상충하는 evidence나 누락 조건을 확인한다.
4. 상대의 strongest claim을 adversarial하게 재검토한다.
5. 잠정 합의가 evidence와 반례를 견디는지 확인한다.

각 bounded slice 뒤에는 상대 상태를 다시 확인한다. 시간을 채우기 위해 unrelated source, 새 topic 또는 speculative architecture를 추가하지 않는다.

## Turn Workflow

새 상대 turn이 있고 자신이 eligible하면 다음 순서로 처리한다.

1. 상대 turn을 끝까지 읽는다.
2. 가장 강한 claim, evidence 또는 objection을 식별한다.
3. 필요한 evidence만 짧게 검증한다.
4. 자신의 기존 position이 틀렸으면 수정한다.
5. 자신의 response가 material delta인지 확인한다.
6. Publish 직전 persisted state를 다시 확인한다.
7. Turn을 publish한 뒤 Active Research Loop로 돌아간다.

Material delta는 새로운 또는 수정된 evidence, 반례, concession, 좁혀진 disagreement, recommendation 변경뿐 아니라 **convergence 또는 더 이상 material objection이 없다는 terminal signal**도 포함한다. Terminal signal을 썼다는 이유로 현재 response runtime을 종료하지 않는다.

각 turn은 가능하면 다음만 남긴다.

```markdown
## Position

이번 turn의 핵심 주장.

## Response

상대의 가장 중요한 주장에 대한 동의, 반박 또는 수정.

## Evidence

판단을 바꿀 중요한 근거.

## Updated Position

변경된 입장이 있을 때만 기록.

## Next

다음에 검증할 가장 중요한 질문 하나.
```

필요 없는 section은 생략한다. 이미 합의된 내용을 반복하지 않는다.

## Stop

정상적인 종료는 session deadline에 도달했을 때다.

그 외에는 다음 경우에만 조기 종료할 수 있다.

- 사용자가 명시적으로 session을 중단했다.
- safety, permission 또는 tool failure로 Research와 상대 상태 확인을 모두 더 이상 수행할 수 없다.
- platform/provider가 response runtime을 강제로 종료한다.

단순히 자신의 turn을 끝냈거나 상대가 늦거나 잠정 합의에 도달했다는 이유로 종료하지 않는다.

## Synthesis

A는 session 종료 직전에 persisted turns와 중요한 Research 결과를 다시 확인하고 `README.md`에 synthesis를 작성한다. Synthesis 때문에 active loop를 너무 일찍 종료하지 않는다.

Synthesis는 다음만 포함한다.

- Result
- Agreements
- Remaining Disagreements
- Strongest Evidence
- Rejected Options
- Open Questions
- Recommended Next Action

Discussion 결과는 proposal이다. Human 또는 owning workflow가 채택하기 전에는 canonical requirement나 project decision이 아니다.

## Recovery

- Missing opponent turn은 failure가 아니다. Research를 계속한다.
- Missing bundle은 B의 종료 사유가 아니다. Bootstrap loop를 계속한다.
- Duplicate invocation은 current persisted state를 읽고 eligible work만 수행한다.
- Stale state나 write conflict는 refresh 후 current sequence에서 재시도한다.
- 상대 turn을 읽은 뒤 write 전에 state가 바뀌면 최신 turn을 다시 확인하고 stale response를 publish하지 않는다.
- Session deadline 이후에는 새 argumentative turn을 시작하지 않는다.

## Boundaries

- 이 guide는 topic 자체를 정의하지 않는다.
- 시간을 채우기 위해 새로운 topic이나 turn을 만들지 않는다.
- 상대 확인만 반복하는 polling loop를 만들지 않는다.
- Research를 핑계로 상대의 새 turn 응답을 과도하게 지연하지 않는다.
- 자신의 turn 뒤에 또 자신의 turn을 연속으로 만들지 않는다.
- 상대가 없다는 이유로 독백형 artifact를 쌓지 않는다.
- `inbox/AGENTS.md`와 `discuss.md`의 artifact ownership과 lifecycle을 유지한다.
