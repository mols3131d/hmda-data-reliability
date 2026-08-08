---
name: pivot-clarify-code
description: Use this skill to make existing Project Pivot code easier to understand and maintain without changing behavior. Trigger for requests to clarify confusing code, names, caller contracts, domain semantics, rationale, responsibilities, control flow, or unnecessary indirection. Do not use for feature implementation, correctness review, performance optimization, architecture redesign, or user-facing documentation.
---

# Clarify Code

기능을 추가하지 않고 코드 이해 부채를 줄인다. 오해 비용이 가장 큰 reading bottleneck을 가장 작은 안전한 변경으로 해소한다.

호출자는 구현을 읽지 않고 필요한 contract를 알 수 있어야 하고, 유지보수자는 코드에서 의도와 제약을 복원할 수 있어야 한다.

## Arguments

```yaml
target: auto
scope: auto
validation: auto
```

| Argument | `auto` 동작 |
| --- | --- |
| `--target <value\|auto>` | 요청, 선택 영역 또는 현재 변경에서 개선 대상을 식별한다. |
| `--scope <value,...\|auto>` | target과 실제 사용 surface, 관련 test, 공유 contract까지만 포함한다. |
| `--validation <command\|auto\|none>` | behavior 보존을 확인할 가장 작은 기존 validation을 선택한다. |

명시된 argument를 우선한다. 범위나 기존 동작이 불명확하면 추측으로 확대하지 않는다.

## Workflow

1. 적용되는 repository/source instructions와 target, caller·entrypoint, 관련 test를 읽는다. 공유 contract가 걸릴 때만 범위를 넓힌다.
1. 보존할 observable behavior와 caller-visible contract를 확인한다.
1. 가장 중요한 reading bottleneck 하나를 진단한다. 오해가 misuse, destructive side effect, 잘못된 ordering 또는 invariant 위반을 만들 수 있으면 단순한 시각적 복잡성보다 우선한다.
1. 가장 작은 해법을 선택한다. 내부 이름과 코드 구조로 명확해질 수 있으면 prose보다 먼저 개선하되, caller-visible API는 contract 변경 없이 rename하지 않는다.
1. caller가 알아야 할 숨은 의미는 docstring, maintainer가 알아야 할 code-local 이유는 comment로 보완한다. 넓은 정책은 canonical owner에 둔다.
1. 선택한 병목만 수정하고 unrelated cleanup이나 미래용 abstraction을 섞지 않는다.
1. 가능한 경우 같은 validation을 변경 전후에 적용해 behavior 보존을 확인한다.
1. caller와 maintainer 관점에서 다시 읽고 중복 prose와 indirection을 제거한 뒤, 변경·보존 근거·validation·risk만 짧게 보고한다.

주된 병목이 해소되면 중단한다. 변경할 가치가 없으면 수정하지 않는다.

## Progressive Disclosure

현재 판단에 필요한 reference만 읽고, 관련 없는 reference는 로드하지 않는다.

- 병목 종류나 최소 intervention이 불명확하거나 rename·extraction을 고려하면 [Diagnosis](references/diagnosis.md)를 읽는다.
- docstring이나 comment를 추가·수정하려면 [Documentation](references/documentation.md)을 읽는다.
- 코드 구조를 바꾸거나 behavior 보존 근거가 불명확하면 [Validation](references/validation.md)을 읽는다.

## Boundaries

- 기능, public contract, 성능 목표 또는 architecture를 clarification 명목으로 변경하지 않는다.
- 이름이나 코드 구조로 표현 가능한 내용을 prose로 반복하지 않는다.
- line count만 줄이는 helper, one-use abstraction, future extension point를 만들지 않는다.
- 광범위한 style·formatting·rename을 섞지 않는다.
- test를 약화하거나 기존 failure를 숨겨 behavior 보존을 증명하지 않는다.
- correctness review를 대신하지 않는다. defect 의심은 별도 작업으로 분리한다.
- 실행하지 않은 validation을 수행했다고 보고하지 않는다.
