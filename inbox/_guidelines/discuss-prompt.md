# Discussion Prompt

이 guide는 `discuss` participant prompt를 생성하는 규칙만 소유한다. Prompt는 토론 규칙을 복제하는 문서가 아니라 participant를 올바른 discussion, persisted state와 execution contract에 연결하는 invocation surface다.

기본 토론 계약은 [`discuss.md`](discuss.md)가 소유한다. Live 실행은 [`discuss-live.md`](discuss-live.md), scheduled 실행은 [`discuss-scheduled.md`](discuss-scheduled.md)가 추가 계약을 소유한다. 이 guide는 phase lifecycle, turn eligibility, sublation 또는 decision authority를 재정의하지 않는다.

## Inputs

Prompt를 만들기 전에 필요한 값만 확정한다.

| Input | Rule |
| --- | --- |
| `goal` | 사람이 판단하려는 질문을 중립적으로 표현한다. |
| `topic` | stable lowercase kebab-case slug를 사용한다. |
| `participant` | `A` 또는 `B`다. |
| `lead` | persisted discussion state를 따른다. |
| `execution` | 실제 `manual`, `scheduled`, `live`와 일치시킨다. |
| `bundle` | 기존 discussion은 exact path를 사용한다. Live 병렬 bootstrap은 아직 존재하지 않아도 shared exact path를 먼저 고정한다. |
| `decision_authority` | `human` 또는 owning workflow를 명시한다. |
| `scope`, `decision_criteria` | 알려진 경우 양쪽 prompt에 같은 값을 전달한다. |

모르는 값은 추측하지 않는다. 특히 expected result, 상대의 현재 입장, runtime duration과 shared deadline을 임의로 만들지 않는다.

## Authoring Rules

- **Reference, do not restate.** `discuss.md`와 applicable execution guide가 소유하는 세부 phase, evidence, dialectic, sublation, recovery 규칙을 prompt에 다시 정의하지 않는다.
- **Keep the shared core symmetric.** A/B에 같은 goal, scope, decision criteria, decision authority와 protocol reference를 준다.
- **Do not assign conclusions.** `A=찬성`, `B=반대`, expected winner, preferred answer 또는 forced consensus를 주입하지 않는다. 서로 다른 관점이 필요하면 결론이 아니라 evidence-search lens를 다르게 둔다.
- **Lead adds coordination only.** Lead 여부는 bootstrap, shared-state authoring과 final synthesis coordination의 차이만 만든다. Evidence weight, tie-break, phase override 또는 final decision 권한을 추가하지 않는다.
- **Persisted state outranks prompt summary.** 기존 bundle에서는 실행 시작과 publish 직전에 `README.md`와 relevant turns를 읽어 current phase, topic, eligibility와 latest state를 확인하게 한다.
- **Prompt does not grant authority.** Discussion 외 repository mutation, Git/GitHub action, external action 또는 노출되지 않은 runtime capability를 새로 허용하지 않는다.

합의 자체를 성공 조건으로 두지 않는다. Participant는 `discuss.md`의 Dialectic/Sublation contract를 따르며, 승화가 불가능하면 해당 guide가 허용하는 disagreement, research 또는 human-decision outcome을 그대로 남긴다.

## Generation

1. **Shared core** — discussion identity, goal, scope, criteria, decision authority와 authoritative guides를 적는다.
1. **Participant delta** — A/B identity와 Lead 여부에 필요한 차이만 추가한다.
1. **Execution delta** — 실제 execution mode의 invocation lifecycle만 추가한다.
1. **Review** — fixed side, expected answer, forced consensus, asymmetric authority, stale-state assumption 또는 unauthorized mutation이 생기지 않았는지 확인한다.

A/B prompt를 별도로 작성해도 shared core의 의미가 달라지면 안 된다.

## Participant Delta

### Lead

Lead prompt에는 다음 의미만 추가한다.

```text
당신은 Lead coordination을 맡는다. Lead는 truth, tie-break 또는 final decision을 소유하지 않는다.
Bundle/bootstrap과 shared state를 관리하되 persisted objection을 정확히 보존한다.
Phase transition과 final synthesis는 discuss.md의 현재 계약과 persisted turns를 기준으로 처리한다.
```

Prompt author가 Lead의 initial working hypothesis를 대신 정하지 않는다.

### Non-Lead

Non-lead prompt에는 다음 의미만 추가한다.

```text
당신은 독립 participant다. Lead의 framing이나 position을 authority로 취급하지 않는다.
독립 evidence path를 확보하고 material framing bias, omission 또는 counterevidence를 검증한다.
Shared-state 변경이 필요하면 자신의 turn에서 제안한다.
```

Non-lead에게 `반대 역할`, `악마의 변호인`, `무조건 공격` 같은 고정 opposition을 부여하지 않는다.

## Execution Delta

### Manual

한 번의 eligible contribution을 기본으로 한다. Publish 이후 continuation은 caller 또는 owning workflow가 소유한다.

### Scheduled

[`discuss-scheduled.md`](discuss-scheduled.md)를 적용하고 다음 delta만 명시한다.

```text
이번 invocation은 current persisted state에서 eligible contribution 또는 허용된 Lead shared-state update 하나만 수행한 뒤 종료한다.
미래 상대 turn을 기다리거나 sequence와 phase를 추측으로 advance하지 않는다.
```

Scheduler interval, recurrence, task ID, notification과 deadline은 외부 runtime이 실제 제공한 경우에만 넣는다.

### Live

[`discuss-live.md`](discuss-live.md)를 적용하고 다음 delta만 명시한다.

```text
자신의 turn 완료나 상대 turn 부재만으로 response를 끝내지 않는다.
Current phase에서 credible information gain이 있는 동안 bounded Research와 shared-state recheck를 반복하고, saturation과 participant-local 종료는 discuss-live.md를 따른다.
고정 runtime이나 shared deadline을 추측하지 않는다.
```

## Bundle Identity

기존 discussion이면 exact bundle path를 prompt에 넣는다. Participant는 prompt의 요약보다 persisted bundle을 source state로 사용한다.

Live discussion을 병렬로 시작할 때는 [`discuss-live.md`](discuss-live.md)의 path/naming contract에 맞는 **하나의 shared exact bundle path를 A/B prompt에 동일하게 넣는다.** Path는 아직 존재하지 않아도 된다. Exact path를 미리 고정할 수 없으면 Lead bootstrap invocation 하나를 먼저 실행해 bundle을 만든 뒤, 그 exact path를 후속 participant prompt에 전달한다.

Topic 검색만으로 concurrent bootstrap uniqueness를 보장한다고 가정하지 않는다.

## Minimal Template

```text
당신은 <topic> discussion의 participant <A|B>다. <participant-delta>

Repository guidance를 먼저 읽고 inbox/_guidelines/discuss.md를 적용한다. Scheduled 또는 Live 실행이면 해당 execution guide도 적용한다. Goal은 <goal>, decision authority는 <authority>다. 기존 discussion 또는 Live shared bootstrap이면 <exact-bundle-path>를 source identity로 사용한다.

실행 시작과 publish 직전에 persisted state를 확인하고 current phase에서 eligible한 material contribution만 수행한다. 독립적으로 evidence를 조사하고 더 강한 evidence가 나오면 working hypothesis를 갱신한다. 합의나 특정 결론을 강제하지 말고 discuss.md의 Dialectic/Sublation contract를 따른다.

Discussion 외 mutation은 별도 권한이 없으면 수행하지 않는다. <execution-delta>
```

Current discussion에 필요한 값만 채우고 repository guide의 세부 규칙을 prompt에 복제하지 않는다.

## Validation

Prompt를 전달하기 전에 다음만 확인한다.

- A/B의 goal, scope, criteria와 authority가 대칭인가.
- fixed side, expected answer 또는 forced consensus가 없는가.
- Lead의 추가 권한이 coordination으로만 제한되는가.
- persisted state를 읽고 refresh하게 하는가.
- Live 병렬 bootstrap이면 양쪽에 같은 exact bundle path가 있는가.
- execution mode와 delta가 실제 runtime과 일치하는가.
- 제공되지 않은 runtime/deadline/capability를 가정하지 않는가.
- prompt가 discussion 외 mutation 권한을 새로 만들지 않는가.
- `discuss*.md`가 소유하는 세부 규칙을 불필요하게 복제하지 않는가.

Material violation이 있으면 전달 전에 수정한다.
