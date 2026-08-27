---
name: prj-load-context-testing
description: >-
  Load repository testing context for pytest work: writing or changing tests,
  selecting or running tests, debugging failures, validating behavior, checking
  coverage, or working with markers, fixtures, assertions, test plans,
  scenarios, oracles, and test design.
targets: [claudecode, codexcli, copilot, copilotcli, antigravity-ide, antigravity-cli]
---

# Testing Context

현재 testing task의 다음 판단에 필요한 context만 선택한다. 상세 testing 규칙은 canonical 문서가 소유한다.

| Need | Load |
| --- | --- |
| `tests/` authored file 수정 또는 test 배치 판단 | [`tests/AGENTS.md`](../../../tests/AGENTS.md) |
| scenario, oracle, assertion, test level 또는 test design 판단 | [`docs/development/test-design-and-implementation.md`](../../../docs/development/test-design-and-implementation.md) |
| pytest 실행·선택·debug, marker, coverage, report 또는 CI test behavior | [`docs/development/testing.md`](../../../docs/development/testing.md) |
| 정확한 pytest default, marker 또는 plugin configuration | [`pyproject.toml`](../../../pyproject.toml) |

문서가 가리키는 config나 workflow의 현재 값이 실제 판단에 필요할 때만 해당 source를 추가로 확인한다. 다음 testing 결정을 내릴 수 있으면 context loading을 멈춘다.

## Boundary

- 이 Skill은 testing context를 선택할 뿐 test design, 실행, CI 또는 reporting policy를 소유하지 않는다.
- Context loading은 현재 task의 write authority나 scope를 확장하지 않는다.
- Canonical 문서의 command, 규칙, 예시를 이 Skill에 복제하지 않는다.
