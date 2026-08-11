---
name: pivot-clarify-runtime
description: Use this skill to reduce runtime understanding debt in Project Pivot when important execution paths, decisions, state transitions, external actions, or failure causes are hard to reconstruct, or when existing runtime evidence is duplicated, noisy, disconnected, or owned at the wrong boundary. Preserve domain behavior and established caller/consumer contracts. Clarify one reconstruction question at a time by reusing, moving, reducing, removing, or adding the smallest evidence needed. Do not use for defect debugging, correctness review, test design, monitoring, telemetry-platform design, performance profiling, or feature implementation.
---

# Clarify Runtime

기능을 추가하지 않고 runtime 이해 부채를 줄인다. **실행 후 답하기 어려운 가장 중요한 질문 하나를, 가장 작은 runtime evidence 변경으로 답할 수 있게 만든다.**

코드를 읽기 쉽게 만드는 일은 `pivot-clarify-code`, defect 판단은 review/debugging 책임이다. 이 스킬은 실행 경로·결정·상태 변화·실패 원인을 복원하는 데 집중한다.

## Arguments

```yaml
target: auto
scope: auto
evidence: auto
validation: auto
```

| Argument | `auto` 동작 |
| --- | --- |
| `--target <value\|auto>` | 요청이나 실행 경계에서 runtime 이해 대상을 식별한다. |
| `--scope <value,...\|auto>` | target과 직접 관련된 entrypoint, caller, runtime surface와 test까지만 포함한다. |
| `--evidence <value\|auto>` | 기존 surface를 우선해 가장 작은 유효한 evidence 변경을 선택한다. |
| `--validation <command\|auto\|none>` | domain behavior 보존과 evidence 유효성을 확인할 가장 작은 기존 validation을 선택한다. |

명시된 argument를 우선한다. 실행 의미나 책임 경계가 불명확하면 추측으로 instrumentation을 확대하지 않는다.

## Workflow

1. 적용되는 지침과 target, entrypoint/caller, 관련 test, 기존 result·exception·artifact·metadata·log를 읽어 현재 실행 경계를 복원한다.
1. 먼저 문제를 분류한다. 핵심 문제가 runtime evidence가 아니면 instrumentation하지 말고 `pivot-clarify-code`, review/debugging, monitoring 또는 performance 책임으로 넘긴다.
1. **복원 질문 하나**를 정한다: 어떤 경로를 탔는가, 왜 결정됐는가, 어떤 상태가 바뀌었는가, 무엇이 실패했는가, 어떤 실행과 연결되는가.
1. 관찰 공백의 형태를 진단한다: evidence가 부족한가, 중복됐는가, 잘못된 boundary가 소유하는가, noise가 과한가, 서로 연결되지 않는가.
1. 가장 작은 intervention과 owner를 고른다. 기존 evidence를 재사용·보강·이동·병합·제거하는 것을 새 evidence 추가보다 먼저 고려한다. caller 결과는 result, 실패 진단은 exception context, framework/tool 실행 사실은 artifact·metadata, 시간적 흐름이나 내부 결정은 logging을 우선한다.
1. 선택한 책임 경계만 수정한다. 같은 사실을 여러 surface에 반복하거나 포괄적 observability 체계를 만들지 않는다.
1. 가능한 경우 같은 좁은 validation으로 domain behavior와 기존 contract가 보존되고, 변경 후 남은 evidence만으로 복원 질문에 답할 수 있는지 확인한다. 불필요한 field·event를 제거하고 질문이 해소되면 중단한다.

기존 evidence만으로 이미 질문에 답할 수 있으면 수정하지 않는다. 넓은 audit에서는 여러 관찰 공백을 찾을 수 있지만 변경은 복원 질문 하나씩 같은 절차로 처리한다.

## Progressive Disclosure

현재 판단에 필요한 reference만 읽는다.

| Need | Reference |
| --- | --- |
| 복원 질문, 문제 형태, 우선순위 또는 책임 경계 진단 | [Diagnosis](references/diagnosis.md) |
| result, exception, artifact/metadata, log의 owner와 intervention 선택 | [Evidence](references/evidence.md) |
| 좋은 log event, context, level, 중복과 noise 판단 | [Logging](references/logging.md) |
| Python 표준 `logging` 구현 | [Python Standard Logging](references/python-logging.md) |
| dbt command, artifact와 log evidence | [dbt Runtime Evidence](references/dbt-evidence.md) |
| behavior와 contract 보존, evidence 검증 | [Validation](references/validation.md) |

## Boundaries

- runtime clarification 명목으로 domain behavior, public contract, approval/validation 기준 또는 architecture를 변경하지 않는다.
- logging이나 evidence 추가를 기본 해법으로 가정하지 않는다. 정리·이동·병합·제거가 더 작은 해법이면 그것을 사용한다.
- 모든 함수 entry/exit, branch, 상태를 기록하지 않는다.
- 같은 사건을 여러 계층이나 surface에 반복 기록하지 않는다.
- secret, credential, 불필요한 raw payload 또는 대용량 데이터를 남기지 않는다.
- debugging, correctness review, test design, monitoring, telemetry platform, performance profiling을 대신하지 않는다.
- instrumentation을 위해 새로운 framework나 dependency를 도입하지 않는다.
- 실행하지 않은 validation이나 관찰 결과를 수행했다고 보고하지 않는다.
