# Chatbot Discussion

이 guide는 두 개의 챗봇이 같은 repository의 `inbox/`를 공유하면서 **각자 하나의 response runtime 안에서 지속적으로 조사하고 상대 turn을 확인하며 토론하는 방식**을 정의한다.

기본 bundle, turn ownership, immutable turn, turn quality, synthesis와 discussion artifact 원칙은 [`discuss.md`](discuss.md)를 따른다. 이 guide가 명시적으로 선택된 경우에만 **runtime cadence와 invocation lifecycle**에 한해 `discuss.md`의 `One Invocation = One Turn` 규칙 대신 이 guide를 적용한다.

## Use When

다음 조건을 모두 만족할 때 사용한다.

- 두 chatbot이 같은 discussion bundle을 읽고 쓸 수 있다.
- 각 chatbot이 현재 하나의 response runtime 동안 shared state를 여러 번 새로 읽을 수 있다.
- 상대를 기다리는 동안 idle하지 않고 관련 Research를 계속해야 한다.
- chatbot vendor 또는 host가 하나의 response 안에서 반복적인 tool/read/write 작업을 허용한다.

이 mode는 scheduler가 나중에 chatbot을 다시 호출하는 방식이 아니다. **각 chatbot이 현재 단일 response를 계속 실행하면서** Research와 shared-state refresh를 반복한다.

환경이 이 실행 모델을 지원하지 않으면 active session을 수행했다고 가장하지 않고 일반 `discuss.md`의 Manual 또는 Scheduled cadence를 사용한다.

## Core Contract

Response runtime이 살아 있는 동안 다음 loop를 계속 수행한다.

```text
상대 상태 확인
→ 새 상대 turn이 있으면 읽고 필요한 최소 검증
→ 응답할 material delta가 있으면 내 turn publish
→ bounded Research slice 1개
→ 상대 상태 다시 확인
→ 반복
```

다음은 **response 종료 사유가 아니다.**

1. 자신의 turn을 publish했다.
2. 상대가 아직 새 turn을 publish하지 않았다.
3. 현재 latest turn이 자신의 것이다.
4. 잠정 convergence가 생겼다.
5. 당장 새로운 반론이 떠오르지 않는다.

이 경우에도 Research와 상대 상태 확인을 계속한다. `sleep`, idle wait 또는 의미 없는 polling으로 시간을 소비하지 않는다. **대기 시간은 Research 시간이다.**

## Runtime Boundary

이 guide는 session duration을 정하지 않는다. 고정된 분 단위 기본값을 두거나 vendor limit를 추정해서는 안 된다.

각 participant는 **자신을 실행하는 chatbot vendor 또는 host가 실제로 제공하는 현재 response runtime boundary**를 따른다. A와 B의 runtime 길이나 종료 시점이 같다고 가정하지 않는다.

- vendor/host가 명시적인 deadline 또는 remaining runtime을 제공하면 해당 participant는 그것을 사용한다.
- vendor/host가 runtime limit를 노출하지 않으면 임의의 deadline을 만들지 않고 현재 response가 실제로 유지되는 동안 Core Contract를 계속한다.
- caller나 host가 두 participant에 공통된 shared deadline을 명시적으로 제공한 경우에만 그것을 discussion-level boundary로 사용할 수 있다.
- 한 participant의 runtime 종료는 다른 participant의 runtime 종료를 의미하지 않는다.

Runtime boundary는 원칙적으로 host state이며 discussion artifact가 새로 정의하지 않는다. A는 `README.md`에 최소한 다음 mode만 기록한다.

```yaml
mode: chatbot-active-session
participants: [a, b]
```

실제로 제공된 shared deadline처럼 discussion 전체에 적용되는 runtime metadata가 있을 때만 추가로 기록한다.

Vendor/host가 종료가 임박했음을 신뢰 가능하게 알려주면 새 큰 Research question이나 새 topic을 시작하지 않는다. 종료 예고가 없다면 finalization 시간을 추측하기 위해 active loop를 임의로 줄이지 않는다.

## Roles

A는 participant이면서 coordination을 소유한다.

- discussion bundle과 `README.md`를 생성한다.
- 첫 eligible turn을 작성한다.
- A turn과 shared topic state를 관리한다.
- 자신의 runtime이 허용하는 범위에서 synthesis를 관리한다.

B는 independent challenger다.

- A가 만든 bundle에 참여한다.
- B turn만 작성한다.
- A의 framing을 기본적으로 신뢰하지 않고 evidence와 counterexample을 확인한다.
- shared state 변경이 필요하면 자신의 turn에서 제안한다.

A와 B는 고정된 찬반 진영이 아니다. 더 강한 evidence가 나오면 입장을 바꾼다.

## Bootstrap

A는 discussion bundle을 만든 뒤 `discuss.md`의 공통 Turn Workflow에 따라 초기 `Research → Plan → Implement → Review`를 수행하고 첫 turn을 publish한다. Publish 직후 종료하지 않고 Active Research Loop로 들어간다.

B가 시작했을 때 bundle 또는 첫 A turn이 아직 없다면 **종료하지 않는다.** Caller가 제공한 topic과 repository context를 기준으로 bounded Research slice를 수행하고, slice가 끝날 때마다 bundle과 A turn 생성 여부를 다시 확인한다.

```text
B 시작
→ bundle/A turn 확인
→ 없음: Research slice
→ 다시 확인
→ 없음: 다음 Research slice
→ 발견: 읽고 검증 후 eligible response
```

B는 A보다 먼저 discussion bundle이나 B turn을 만들지 않는다.

## Turn Order And Concurrency

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

상대 turn을 읽은 뒤 publish 전에 persisted state가 바뀌면 stale response를 그대로 쓰지 않는다. 최신 turn과 eligibility를 다시 확인하고 필요한 경우 자신의 response를 다시 계산한다.

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
→ new turn: read + minimal verify
→ material response가 있으면 publish
→ Research 계속
```

새 상대 turn이 발견되면 unrelated Research를 계속하지 않는다. 상대 주장을 판정하는 데 필요한 최소 검증만 수행한 뒤 response 여부를 결정한다.

Research 결과가 중요하지만 아직 자신의 turn 차례가 아니라면 새 self-turn을 만들지 않는다. 다음 eligible turn에서 반영한다.

## Research Saturation

새로운 자료를 찾는 것만 Research로 취급하지 않는다. 새 source가 더 이상 현재 topic의 판단을 바꾸지 않는다면 범위를 넓히지 말고 다음 방향으로 전환한다.

1. 가장 강한 현재 근거를 다시 검증한다.
2. 핵심 가정의 반례를 찾는다.
3. 상충하는 evidence나 누락 조건을 확인한다.
4. 상대의 strongest claim을 adversarial하게 재검토한다.
5. 잠정 합의가 evidence와 반례를 견디는지 확인한다.

각 bounded slice 뒤에는 상대 상태를 다시 확인한다. 시간을 채우기 위해 unrelated source, 새 topic 또는 speculative architecture를 추가하지 않는다.

## Response Workflow

새 상대 turn이 있고 자신이 eligible하면 다음 순서로 처리한다.

1. 상대 turn을 끝까지 읽는다.
2. 가장 강한 claim, evidence 또는 objection을 식별한다.
3. 필요한 evidence만 짧게 검증한다.
4. 자신의 기존 position이 틀렸으면 수정한다.
5. material response가 있는지 판정한다.
6. Publish 직전 persisted state와 eligibility를 다시 확인한다.
7. 필요한 turn을 publish한 뒤 Active Research Loop로 돌아간다.

Material response는 새로운 또는 수정된 evidence, 반례, concession, 좁혀진 disagreement, recommendation 변경처럼 후속 판단을 바꾸는 내용이다.

상대 turn을 검토했지만 material objection이나 수정이 없다면 억지로 반론을 만들지 않는다. 필요하면 **한 번의 no-finding 또는 convergence signal**로 검토 결과를 알릴 수 있다. 이런 signal 자체는 상대에게 또 다른 no-finding 응답을 요구하지 않으며 active runtime도 닫지 않는다.

각 substantive turn은 가능하면 다음만 남긴다.

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

## Convergence

잠정 convergence는 **새 논쟁을 만들지 말라는 신호**이지 response runtime 종료 신호가 아니다.

Convergence 이후에는 새로운 opposition을 억지로 생성하지 않고 Active Research Loop를 다음 목적으로 사용한다.

- 합의가 의존하는 핵심 evidence 재검증
- 합의를 깨뜨릴 수 있는 반례 확인
- 누락된 조건이나 boundary 확인
- 상대가 새 material turn을 게시했는지 확인

새 material finding이 생기면 다음 eligible turn에서 토론을 다시 연다. 새 finding이 없으면 turn을 추가하지 않고 Research와 상대 확인을 계속한다.

## Stop

정상적인 종료는 **각 participant 자신의 vendor/host response runtime boundary**에 도달했을 때다.

그 외에는 다음 경우에만 조기 종료할 수 있다.

- 사용자가 명시적으로 해당 participant의 active session을 중단했다.
- safety, permission 또는 tool failure로 Research와 상대 상태 확인을 모두 더 이상 수행할 수 없다.

단순히 자신의 turn을 끝냈거나 상대가 늦거나 잠정 합의에 도달했다는 이유로 종료하지 않는다.

한 participant가 먼저 종료되어도 남은 participant는 자신의 runtime이 살아 있는 동안 Research와 shared-state 확인을 계속한다. 상대가 다시 응답할 수 있다고 추측하지는 않는다.

## Synthesis And Checkpoint

최종 synthesis는 A가 소유하지만 **synthesis를 보장하기 위해 active runtime을 임의로 일찍 끝내지 않는다.**

A는 자신의 substantive turn 또는 shared-state 변경 뒤 `README.md`의 Current State를 필요한 만큼 갱신해, 갑작스러운 runtime 종료가 발생해도 persisted turns만으로 현재 상태를 복구할 수 있게 한다.

A의 vendor/host가 종료가 임박했음을 신뢰 가능하게 알려주면 남은 시간에 새 큰 Research를 시작하지 않고 persisted turns를 다시 확인한 뒤 synthesis를 갱신한다.

종료 예고 없이 runtime이 끝난 경우 final synthesis가 없거나 최신 turn을 반영하지 못할 수 있다. 이를 성공적으로 완료한 synthesis로 가장하지 않는다. 이 경우 persisted turns와 마지막 Current State가 discussion evidence다.

Synthesis는 필요한 경우 다음만 포함한다.

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
- 한 participant의 runtime 종료는 다른 participant의 deadline을 만들지 않는다.
- Vendor/host가 실제 runtime을 종료하면 해당 participant는 더 이상 작업을 수행할 수 없다는 limitation으로 취급한다.

## Boundaries

- 이 guide는 topic 자체를 정의하지 않는다.
- 시간을 채우기 위해 새로운 topic이나 turn을 만들지 않는다.
- 상대 확인만 반복하는 polling loop를 만들지 않는다.
- Research를 핑계로 상대의 새 turn 응답을 과도하게 지연하지 않는다.
- 자신의 turn 뒤에 또 자신의 turn을 연속으로 만들지 않는다.
- 상대가 없다는 이유로 독백형 artifact를 쌓지 않는다.
- vendor/host가 노출하지 않은 runtime limit, deadline 또는 capability를 추측하지 않는다.
- `inbox/AGENTS.md`와 `discuss.md`의 artifact ownership과 lifecycle을 유지한다.
