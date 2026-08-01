# Subagents and Context Isolation

## Goal

Research와 Review를 구현 context에서 분리해 confirmation bias와 context pollution을 줄인다.
ROR는 subagent를 활용할 수 있지만 subagent가 없는 환경에서도 동일한 artifact contract로 동작해야 한다.

## Execution Modes

| Mode | 사용 조건 | 실행 방식 |
| --- | --- | --- |
| **Native subagent** | runtime이 독립 agent delegation을 지원 | Research와 Review를 별도 agent에 위임 |
| **Forked context** | 별도 agent는 없지만 fresh context 생성 가능 | 필요한 artifact만 로드한 새 context에서 실행 |
| **Sequential fallback** | context 분리 기능이 없음 | 같은 agent가 역할을 재설정하고 이전 대화 대신 durable artifact만 사용 |

기능 지원 여부가 verdict 의미나 artifact 형식을 바꾸면 안 된다.

## Roles

| Role | Allowed work | Must not do |
| --- | --- | --- |
| Orchestrator | phase routing, human gate, artifact 위치 관리 | 숨은 추론을 handoff로 사용 |
| Researcher | 근거 충분성 평가, gap 조사, uncertainty 정리 | solution·OpenSpec requirement 최종 확정 |
| Specifier | OpenSpec proposal·requirements·design·tasks 관리 | 별도 competing plan 생성 |
| Implementer | 승인된 task 구현과 검증 | requirement를 코드에서 조용히 변경 |
| Reviewer | active OpenSpec·diff·checks 독립 대조 | finding을 직접 수정하거나 구현 summary를 무검증 수용 |

## Durable Handoff

agent 사이에는 transcript나 private reasoning이 아니라 다음만 전달한다.

- 대상 repository와 `{change-id}`
- 현재 phase와 rigor
- 읽어야 할 authoritative artifact
- observed evidence와 실제 validation result
- unresolved conflict·assumption·risk
- 요청된 output path와 허용 status 또는 verdict

[Handoff template](../templates/handoff.yaml)을 사용한다.

## Isolation Rules

1. Research와 Review는 가능하면 fresh context에서 시작한다.
1. Reviewer에게 구현자의 결론이나 설득용 설명을 필수 input으로 주지 않는다.
1. 동일 agent fallback에서는 phase가 바뀔 때 역할·목표·입력 목록을 다시 선언한다.
1. 이전 phase의 artifact에 없는 주장은 새로운 evidence로 취급하지 않는다.
1. independent read-only investigation은 병렬화할 수 있다.
1. 같은 file·branch·OpenSpec artifact를 수정하는 작업은 하나의 owner가 직렬로 수행한다.

## Routing Contract

| Result | Owner | Route |
| --- | --- | --- |
| Research `Ready` | Orchestrator | OpenSpec |
| Research `Revise` | Research 또는 Human | 지정 gap만 보완 |
| Research `Blocked` | Human 또는 Environment | resume condition 해결 |
| Review `Pass` | OpenSpec | archive |
| Review `Revise` | Research / OpenSpec / Implement | finding owner로 복귀 후 fresh Review |
| Review `Blocked` | Human 또는 Environment | blocker 해결 후 fresh Review |

## Failure Handling

subagent가 timeout·tool failure·missing access로 끝나면 성공으로 간주하지 않는다.

- partial evidence를 durable artifact에 남긴다.
- status 또는 verdict를 `Blocked`나 `Revise`로 판정한다.
- 재개에 필요한 최소 input·permission·command를 명시한다.
- 동일 실패를 근거 없이 반복하지 않는다.

## Portability Test

ROR가 portable하려면 다음 두 실행이 같은 의미를 가져야 한다.

```text
Orchestrator → Research subagent → OpenSpec → Implement subagent → Review subagent
```

```text
Single agent: Research role → OpenSpec role → Implement role → Review role
```

차이는 context isolation 수준뿐이며, phase contract·artifact·routing은 동일해야 한다.
