---
name: pivot-clarify-runtime
description: Use this skill to reduce runtime understanding debt in existing Project Pivot code without changing domain behavior. Trigger when important execution paths, decisions, state transitions, external actions, or failure causes are difficult to reconstruct from results, metadata, exception context, logs, or other runtime evidence. Use logging only when it is the smallest useful intervention. Do not use for defect debugging, correctness review, test design, monitoring, telemetry-platform design, performance profiling, or feature implementation.
---

# Clarify Runtime

기능을 추가하지 않고 runtime 이해 부채를 줄인다. 실행 후 무엇이 일어났는지 복원하기 어려운 가장 중요한 관찰 공백을 가장 작은 evidence로 해소한다.

코드를 읽기 쉽게 만드는 일은 `pivot-clarify-code`, defect 판단은 review/debugging 책임이다. 이 스킬은 **실행을 이해할 수 있게 만드는 것**에 집중한다.

## Arguments

```yaml
target: auto
scope: auto
evidence: auto
validation: auto
```

| Argument | `auto` 동작 |
| --- | --- |
| `--target <value\|auto>` | 요청, 실행 경계 또는 현재 변경에서 runtime 이해 대상을 식별한다. |
| `--scope <value,...\|auto>` | target과 실제 entrypoint/caller, 관련 runtime surface와 test까지만 포함한다. |
| `--evidence <value\|auto>` | 기존 surface를 우선해 가장 작은 유효한 evidence를 선택한다. |
| `--validation <command\|auto\|none>` | domain behavior 보존과 의도한 evidence를 확인할 가장 작은 기존 validation을 선택한다. |

명시된 argument를 우선한다. 실행 의미나 책임 경계가 불명확하면 추측으로 instrumentation을 확대하지 않는다.

## Workflow

1. 적용되는 repository/source instructions와 target, entrypoint/caller, 관련 test, 기존 result·metadata·exception·log를 읽어 현재 실행 경계를 복원한다.
1. 실행 결과만 보고 답하기 어려운 질문 하나를 정한다: 어떤 경로를 탔는가, 왜 결정됐는가, 어떤 상태가 바뀌었는가, 무엇이 실패했는가.
1. 오해 비용이 가장 큰 runtime 관찰 공백 하나를 선택한다. 위험한 mutation, approval/validation gate, 외부 실행과 실패 원인을 우선한다.
1. 기존 surface로 해결 가능한지 먼저 확인하고 가장 작은 evidence를 선택한다. caller 결과는 result, 실패 진단은 exception context, framework 실행 사실은 metadata, 시간적 흐름이나 내부 결정은 logging을 우선 고려한다.
1. 결정이나 상태 변화가 발생하는 책임 경계 가까이에 필요한 정보만 남긴다. 같은 의미를 여러 surface에 반복하지 않는다.
1. 선택한 공백만 수정하고 포괄적 logging, tracing, monitoring 또는 미래용 observability abstraction을 추가하지 않는다.
1. 가능한 경우 같은 좁은 validation으로 domain behavior 보존과 의도한 runtime evidence를 확인한다.
1. 실행을 다시 복원해 보고 불필요한 event, field와 중복 evidence를 제거한 뒤 변경·근거·validation·남은 risk만 짧게 보고한다.

관찰 공백이 해소되면 중단한다. 기존 evidence로 충분하면 수정하지 않는다.

## Progressive Disclosure

현재 판단에 필요한 reference만 읽는다.

- 관찰 공백의 종류나 책임 경계가 불명확하면 [Diagnosis](references/diagnosis.md)를 읽는다.
- result, metadata, exception context, logging 중 evidence surface를 선택하거나 구성하려면 [Evidence](references/evidence.md)를 읽는다.
- logging을 추가·수정하려면 [Logging](references/logging.md)을 읽는다.
- domain behavior 보존 또는 evidence 검증 방법이 불명확하면 [Validation](references/validation.md)을 읽는다.

## Completion

가장 중요한 runtime 관찰 공백 하나가 해소되어 대상 실행의 경로·결정·상태 변화 또는 실패 원인 중 필요한 내용을 기존보다 직접 복원할 수 있고, 중복 evidence와 불필요한 instrumentation이 없으면 완료한다.

## Boundaries

- runtime clarification 명목으로 domain behavior, public contract, approval/validation 기준 또는 architecture를 변경하지 않는다.
- logging을 기본 해법으로 가정하지 않는다. 기존 result, metadata 또는 exception context가 더 적합하면 그것을 사용한다.
- 모든 함수의 entry/exit, 모든 분기, 모든 상태를 기록하지 않는다.
- secret, credential, 민감 정보, 불필요한 raw payload 또는 대용량 데이터를 남기지 않는다.
- 같은 사건을 여러 계층에서 반복 기록해 noise를 만들지 않는다.
- debugging, correctness review, test design, monitoring, telemetry platform, performance profiling을 대신하지 않는다.
- instrumentation을 위해 새로운 framework나 dependency를 도입하지 않는다.
- 실행하지 않은 validation이나 관찰 결과를 수행했다고 보고하지 않는다.
