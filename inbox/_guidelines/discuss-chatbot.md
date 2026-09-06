# Chatbot Discussion

이 guide는 두 개의 챗봇이 같은 repository의 `inbox/`를 공유하면서 **각자 하나의 response runtime 안에서 지속적으로 조사하고 상대 턴을 확인하며 토론하는 방식**을 정의한다.

기본 bundle, turn ownership, immutable turn, synthesis와 discussion artifact 원칙은 [`discuss.md`](discuss.md)를 따른다. 다만 이 guide가 명시적으로 선택된 경우 **runtime cadence와 invocation lifecycle에 한해서는** `discuss.md`의 `One Invocation = One Turn` 규칙 대신 이 guide를 적용한다.

## Core Contract

하나의 chatbot response는 하나의 turn을 쓰고 끝나는 실행이 아니다. Response runtime이 살아 있는 동안 참가자는 다음 loop를 계속 수행한다.

```text
상대 상태 확인
→ 상대의 새 턴이 있으면 읽고 검증
→ 내 차례이고 material delta가 있으면 내 턴 publish
→ 관련 Research 수행
→ 상대 상태 다시 확인
→ 반복
```

다음 두 상황은 **절대 response 종료 사유가 아니다.**

1. 자신의 turn을 publish했다.
2. 상대가 아직 새 turn을 publish하지 않았다.

자신의 turn을 publish한 뒤에도 Research를 계속하고 상대의 다음 turn을 확인한다. 상대 turn이 없을 때도 Research를 계속하고 조사 단위가 끝날 때마다 상대 상태를 다시 확인한다.

`sleep`, idle wait 또는 의미 없는 polling으로 시간을 소비하지 않는다. **대기 시간은 Research 시간이다.**

## Session

Session은 두 chatbot response가 동시에 또는 겹치는 시간 동안 진행되는 active runtime window다.

기본 session은 25분이며 caller가 다른 값을 명시하면 그 값을 사용한다. Session duration은 목표 시간이 아니라 maximum active window다. 다만 단순 convergence, 자신의 turn publish 또는 상대 turn 부재만으로 자발적으로 response를 종료하지 않는다.

Platform이나 provider가 response runtime을 강제로 종료하는 경우는 피할 수 없는 예외다. 이 경우 가능한 마지막 시점에 현재 상태를 durable artifact에 남긴다.

A가 session 시작 시 `README.md`에 최소한 다음을 기록한다.

```yaml
mode: chatbot-active-session
started_at: <timestamp>
ends_at: <timestamp>
participants: [a, b]
```

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

## Turn Order

Turn은 discussion-global sequence를 사용한다.

```text
001-a.md
002-b.md
003-a.md
004-b.md
...
```

매 publish 직전에 `turns/`를 다시 읽어 현재 sequence와 eligibility를 확인한다.

- turn이 없으면 A만 eligible하다.
- latest valid turn이 A면 B만 eligible하다.
- latest valid turn이 B면 A만 eligible하다.

이미 소비한 상대 turn에 다시 답하지 않는다. 자신의 turn이 latest이면 새 self-turn을 만들지 않고 Research를 계속한다.

이미 publish된 turn은 rewrite하지 않는다. Stale state나 write conflict가 발생하면 최신 persisted state를 다시 읽고 현재 sequence에서 계속한다.

## Active Research Loop

상대의 새 turn을 기다리는 동안 멈추지 않는다. 현재 topic의 결론을 바꿀 가능성이 있는 가장 작은 Research question을 하나 선택한다.

Research 우선순위는 다음과 같다.

1. current canonical repository contract와 applicable guidance
2. current implementation, tests와 runtime evidence
3. 관련 inbox research/discussion
4. 판단에 실제 도움이 될 때만 external authoritative source

한 Research slice는 하나의 bounded question 또는 몇 개의 밀접한 evidence check만 다룬다. Repository 전체를 반복 탐색하거나 시간이 남는다는 이유로 주제를 넓히지 않는다.

Research slice가 끝나면 반드시 상대의 최신 turn 상태를 다시 확인한다.

```text
Research slice
→ check opponent
→ no new turn: next Research slice
→ new turn: read + verify + respond when eligible
→ Research 계속
```

새 상대 turn이 발견되면 기존 Research를 무한히 계속하지 않는다. 현재 판단에 필요한 최소 검증만 마친 뒤 상대 주장에 응답한다.

Research 결과가 중요하지만 아직 자신의 turn 차례가 아니라면 새 self-turn을 만들지 않는다. 해당 finding은 현재 runtime context에 유지하고 다음 eligible turn에서 반영한다.

## Turn Workflow

새 상대 turn이 있고 자신이 eligible하면 다음 순서로 처리한다.

1. 상대 turn을 끝까지 읽는다.
2. 가장 강한 claim, evidence 또는 objection을 식별한다.
3. 필요한 repository/external evidence만 짧게 검증한다.
4. 자신의 기존 position이 틀렸으면 수정한다.
5. 반복이 아닌 material delta가 있을 때만 turn을 작성한다.
6. Publish 직후 종료하지 않고 Active Research Loop로 돌아간다.

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

## No Early Exit

다음은 response 종료 사유가 아니다.

- 내 turn을 성공적으로 publish함
- 상대가 아직 응답하지 않음
- 현재 최신 turn이 내 것임
- 잠정적으로 합의함
- 현재 반론이 바로 떠오르지 않음

이 경우 모두 남은 runtime 동안 관련 Research와 상대 상태 확인을 계속한다.

잠정 convergence가 발생하면 새로운 논쟁을 억지로 만들지 않는다. 대신 합의가 실제 evidence를 견디는지, 중요한 반례나 누락 조건이 없는지 검증하면서 상대 turn을 계속 확인한다.

## Stop

정상적인 종료는 session deadline에 도달했을 때다. Deadline이 가까워지면 새 큰 Research question이나 새 topic을 시작하지 않는다.

그 외에는 다음 경우에만 조기 종료할 수 있다.

- 사용자가 명시적으로 session을 중단했다.
- safety, permission 또는 tool failure로 Research와 상대 상태 확인을 모두 더 이상 수행할 수 없다.
- platform/provider가 response runtime을 강제로 종료한다.

단순히 할 말을 다 했거나 상대가 늦는다는 이유로 종료하지 않는다.

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

## Boundaries

- 이 guide는 topic 자체를 정의하지 않는다.
- 시간을 채우기 위해 새로운 topic이나 turn을 만들지 않는다.
- 상대 확인만 반복하는 polling loop를 만들지 않는다.
- Research를 핑계로 상대의 새 turn 응답을 과도하게 지연하지 않는다.
- 자신의 turn 뒤에 또 자신의 turn을 연속으로 만들지 않는다.
- 상대가 없다는 이유로 독백형 artifact를 쌓지 않는다.
- `inbox/AGENTS.md`와 `discuss.md`의 artifact ownership과 lifecycle을 유지한다.
