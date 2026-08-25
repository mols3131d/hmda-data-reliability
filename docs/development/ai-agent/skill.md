# Skill

Skill은 **task intent와 semantic relevance에 따라 선택적으로 load하는 instruction, workflow 또는 reusable capability**다. `SKILL.md`는 Skill package의 entry surface이지 source나 ownership의 분류명이 아니다.

## Selection

Skill을 우선 사용하는 경우:

- task intent가 applicability를 결정한다.
- 특정 작업에서만 필요한 context를 항상 로드하고 싶지 않다.
- 반복 가능한 workflow나 capability를 재사용한다.
- 정책, 제약, 판단 기준이 path가 아니라 작업 의미에 따라 필요하다.

Skill은 workflow나 tool procedure만을 위한 surface가 아니다. **Rule과 비슷한 instruction content도 task-selected라면 Skill에 둘 수 있다.** Rule과 Skill의 선택 기준은 [AI Agent](README.md)가 소유한다.

## Loading

Skill catalog 전체를 선로드하지 않는다. Routing metadata의 `name`과 `description`으로 task relevance를 판단한 뒤 필요한 Skill source만 읽는다. Task intent가 materially 바뀌면 applicability를 다시 평가한다.

Project-authored Skill의 canonical source는 `.rulesync/skills/**`다. External standard Agent Skill의 설치·dependency 관리 경로를 포함한 asset management policy는 [AI Agent](README.md#asset-management)를 따른다.

Generated target projection과 `.agents/route/skills.jsonl`은 derived surface다. 정확한 discovery, invocation과 target compatibility는 실제 harness와 Rulesync의 current contract를 따른다.

## Boundary

이 문서는 **Skill의 task-based applicability와 loading**만 소유한다.

- surface 선택과 asset management: [AI Agent](README.md)
- structural instruction: [Rule](rule.md)
- Rulesync integration detail: [`.rulesync/README.md`](../../../.rulesync/README.md)
- external standard Skill dependency state: Skills CLI가 생성·관리하는 lock state
