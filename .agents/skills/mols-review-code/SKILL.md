---
name: mols-review-code
description: Review implementation and test changes for intended behavior, correctness, regressions, reachable failure paths, maintainability risks, and validation evidence. Use for diffs, files, commits, pull requests, or working-tree changes. Works independently of any reviewer, workflow, VCS host, or review artifact.
---

# Code Review

변경이 의도한 contract를 충족하고 새로운 defect를 도입하지 않는지 근거로 검증한다.

구현 코드와 테스트 코드를 함께 검토할 수 있지만 서로 다른 기준을 적용한다. 리뷰 대상은 수정하지 않으며 severity와 verdict는 호출자의 Review 계약을 따른다.

## Arguments

```yaml
target: auto
baseline: auto
contract: auto
scope: auto
exclude: []
focus: auto
validation: auto
```

| Argument | `auto` 동작 |
| --- | --- |
| `--target <value\|auto>` | 요청, diff, 선택 영역 또는 현재 변경에서 검토 대상을 식별한다. |
| `--baseline <value\|auto>` | 비교 가능한 이전 revision이나 변경 기준을 사용한다. 유효한 기준이 없으면 만들지 않는다. |
| `--contract <value\|auto>` | 사용자 의도와 적용되는 spec, 문서, 규칙에서 기대 동작을 재구성한다. |
| `--scope <value,...\|auto>` | 대상과 실질적으로 영향을 받는 동작까지만 포함한다. |
| `--exclude <value,...>` | 지정한 path, relation 또는 concern을 검토에서 제외한다. |
| `--focus <auto\|implementation\|tests\|all>` | 대상에 포함된 구현·테스트 종류에 맞는 검토 기준을 선택한다. |
| `--validation <command\|auto\|none>` | 허용된 기존 검증 중 가장 작은 신뢰 가능한 범위를 선택한다. |

명시된 argument를 우선한다. 유효한 baseline이나 contract가 없으면 추측하지 않고 제한을 보고한다.

## Workflow

1. 검토 대상, baseline과 기대 contract를 확인한다.
2. 변경된 동작과 직접 영향을 받는 관계를 추적해 scope를 정한다.
3. 구현 코드와 테스트 코드에 해당하는 검토 기준을 적용한다.
4. 가능한 경우 가장 작은 안전한 기존 validation을 실행한다.
5. candidate finding을 기존 safeguard, baseline과 실제 reachability로 재검증한다.
6. 근거 있는 finding과 해소되지 않은 불확실성만 반환한다.

Finding 수보다 실제 영향과 신뢰성을 우선한다.

## Progressive Disclosure

현재 대상에 필요한 문서만 읽는다.

| 필요 | Reference |
| --- | --- |
| 대상·baseline·contract·scope·validation | [Workflow](references/workflow.md) |
| production code와 runtime behavior 검토 | [Implementation](references/implementation.md) |
| test design, oracle와 false green 검토 | [Tests](references/tests.md) |
| candidate 검증과 evidence-linked finding 작성 | [Findings](references/findings.md) |

## Completion

요청된 대상과 직접 영향을 받는 동작을 검토했고, 중요한 candidate를 검증하거나 기각했으며, 실행한 validation과 남은 불확실성을 정확히 보고하면 완료한다.

## Boundaries

- source, test, fixture, config 또는 repository 상태를 수정하지 않는다.
- 무관한 기존 defect, 일반 정리나 선택적 redesign으로 scope를 넓히지 않는다.
- style 선호만으로 finding을 만들지 않는다.
- 실행하지 않은 validation이나 재현을 수행한 것처럼 주장하지 않는다.
- test, lint와 automation 결과를 correctness의 완전한 증명으로 취급하지 않는다.
- 현재 변경으로 발생한 문제와 기존 상태를 구분한다.
- 특정 Agent, Review workflow, VCS 또는 artifact format을 필수로 가정하지 않는다.
