---
name: pivot-implement-test
description: "Design and author test-side implementation for an active OpenSpec change. Use for requirement-to-scenario traceability, independent oracles, intentional red tests, test-side self-review, and handoff to the production implementation owner."
---

# Implement Test

OpenSpec Implement 작업의 test-side design, implementation과 self-review를 수행한다.

상위 workflow가 할당한 behavior contract와 task를 입력으로 사용하며, OpenSpec 결정이나 production behavior를 다시 정의하지 않는다.

## Workflow

| Stage | Responsibility | Completion signal |
| --- | --- | --- |
| Design | 각 in-scope behavior를 scenario 또는 명시적인 exclusion에 연결하고 observable result, independent oracle과 필요한 test level을 정한다. | Test로 구현할 수 있거나 빠진 결정을 명확히 반환한다. |
| Design Self-Review | requirement부터 scenario와 test까지의 추적성, oracle 독립성, observable boundary와 test level을 재검토한다. | Test-side finding을 수정했고 남은 specification 또는 architecture gap을 분리했다. |
| Implement | 검토된 design을 test-side authored files로 구현하며 scenario, oracle과 assertion strength를 보존한다. | 작성된 test가 design을 표현한다. |
| Implementation Self-Review | 구현을 design과 대조하고 false green, test defect 위장, 불필요한 implementation coupling과 runtime dependency를 검토한다. | Test-side finding을 수정했고 handoff할 수 있다. |
| Handoff | 작성 결과와 범위 밖 finding을 caller에게 반환한다. | Production owner가 test를 실행하고 구현을 계속할 수 있다. |

Intentional red test는 collection, fixture 또는 environment가 아니라 요구된 observable behavior에서 실패하도록 작성한다. 실행하지 않은 test를 `red` 또는 `green`으로 분류하지 않는다.

## Handoff

- 적용한 behavior와 scenario 또는 exclusion
- 작성한 test-side files
- design과 implementation self-review 결과
- 실행 가능한 focused test command
- specification gap, production capability 필요 또는 남은 risk

Test 실행과 production validation은 caller가 소유한다. 이 skill은 RPI phase 완료를 판정하지 않는다.

## Assets

| Responsibility | Asset |
| --- | --- |
| Active change와 apply contract | `openspec/changes/{change-id}/`, `openspec/schemas/{schema}/schema.yaml` |
| Test design 기준 | `docs/development/test-design-and-implementation.md` |
| Pytest command와 runtime context | `.agents/skills/prj-testing/SKILL.md` |
| Local test ownership과 write boundary | `tests/AGENTS.md` |

각 asset이 자신의 contract와 세부 기준을 소유한다. 이 skill은 test-side design, implementation, self-review와 handoff만 소유한다.
