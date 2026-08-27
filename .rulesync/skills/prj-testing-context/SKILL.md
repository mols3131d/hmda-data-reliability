---
name: prj-testing-context
description: >-
  Select repository context for testing tasks: test design, pytest execution and
  debugging, or changes under the tests path.
targets: [claudecode, codexcli, copilot, copilotcli, antigravity-ide, antigravity-cli]
---

# Testing Context

현재 testing task에 필요한 canonical context만 선택한다. 상세 testing 규칙은 각 owner가 소유한다.

| Need | Load |
| --- | --- |
| `tests/` authored file 수정 또는 test 배치 판단 | [`tests/AGENTS.md`](../../../tests/AGENTS.md) |
| requirement, scenario, oracle, assertion 또는 test level 설계 | [`docs/development/test-design.md`](../../../docs/development/test-design.md) |
| pytest 실행·선택·debug, marker, coverage, report 또는 CI test behavior | [`docs/development/testing.md`](../../../docs/development/testing.md) |
| 정확한 pytest default, marker 또는 plugin configuration | [`pyproject.toml`](../../../pyproject.toml) |

CI 또는 Git hook의 구체적인 실행 동작이 직접 필요할 때만 해당 workflow/config를 추가로 확인한다. 필요한 testing 결정을 내릴 수 있으면 context loading을 멈춘다.

## Boundary

- 이 Skill은 testing context를 선택할 뿐 test design, 실행, CI 또는 reporting policy를 소유하지 않는다.
- Context loading은 현재 task의 write authority나 scope를 확장하지 않는다.
- Canonical 문서의 command, 규칙, 예시를 이 Skill에 복제하지 않는다.
