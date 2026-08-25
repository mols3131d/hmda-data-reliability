# Skill

Skill은 **task intent와 semantic relevance에 따라 선택적으로 load하는 instruction, workflow 또는 reusable capability**다. `SKILL.md`는 Skill package의 entry surface이지 이 repository에서 Skill의 source나 ownership을 구분하는 이름이 아니다.

## Source Policy

이 repository의 Skill은 source에 따라 구분한다.

| Source | Policy |
| --- | --- |
| 이 repository에서 직접 작성·관리 | `.rulesync/skills/**`의 **Rulesync Skill**을 canonical source로 사용 |
| 외부 reusable Skill dependency | 필요하면 **Skills CLI**로 설치하고 `skills-lock.json`으로 dependency state를 관리 |

직접 관리하는 Skill은 Rulesync source를 수정한다. Generated target projection과 `.agents/route/skills.jsonl`은 derived surface이며 canonical Skill body를 대체하지 않는다.

외부 Skill을 설치했다는 이유만으로 이 repository가 그 Skill의 작성 권한을 인수하지 않는다. 외부 dependency는 upstream source와 lock state를 기준으로 사용하며, 필요하지 않은 local fork나 Rulesync 재작성으로 복제하지 않는다.

## Selection

Skill을 우선 사용하는 경우:

- task intent가 applicability를 결정한다.
- 특정 작업에서만 필요한 지침을 항상 context에 넣고 싶지 않다.
- 반복 가능한 workflow나 capability를 여러 작업에서 재사용한다.
- 정책, 제약, 판단 기준이 path가 아니라 작업 의미에 따라 필요하다.

Skill은 workflow나 tool procedure만을 위한 surface가 아니다. **Rule과 비슷한 instruction content도 task-selected라면 Skill에 둘 수 있다.** 반대로 특정 path나 extension에서 항상 적용되어야 하는 지침은 [Rule](rule.md)을 사용한다.

## Loading

Skill catalog 전체를 선로드하지 않는다. Routing metadata의 `name`과 `description`으로 task relevance를 판단한 뒤 필요한 Skill source만 읽는다. Task intent가 materially 바뀌면 applicability를 다시 평가한다.

정확한 discovery, invocation, target compatibility와 projection semantics는 실제 harness와 Rulesync의 current contract를 따른다.

## Boundary

- repository-wide / directory / Rule과 Skill 선택 기준: [AI Agent Instructions](README.md)
- structure-selected instruction: [Rule](rule.md)
- Rulesync integration detail: [`.rulesync/README.md`](../../../.rulesync/README.md)
- external Skill dependency state: [`skills-lock.json`](../../../skills-lock.json)
