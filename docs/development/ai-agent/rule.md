# Rule

Rule은 **repository structure로 applicability가 결정되는 instruction surface**다. 이 project에서는 여러 경로에 반복되는 path, glob, file type, extension scope를 표현할 때 Rulesync Rule을 사용한다.

## Selection

Rule을 우선 사용하는 경우:

- 같은 종류의 파일에 동일한 지침이 반복해서 필요하다.
- 여러 위치에 같은 하위 directory pattern이 반복된다.
- applicability를 task 의미가 아니라 path, glob, extension으로 안정적으로 결정할 수 있다.
- 여러 `AGENTS.md`에 같은 cross-cutting 지침을 복제하는 것보다 하나의 selector가 책임을 더 정확하게 표현한다.

하나의 directory subtree가 자연스럽게 지침을 소유할 수 있으면 nearest `AGENTS.md`를 우선한다. Rule은 directory hierarchy로 자연스럽게 표현하기 어려운 shared scope에 사용한다.

## Rule and Skill

**지침이라고 해서 반드시 Rule인 것은 아니다.** Skill도 정책, 제약, 판단 기준, 작업 원칙처럼 Rule과 유사한 instruction을 담을 수 있으며, 이 project는 이런 instruction-oriented Skill을 허용한다.

구분 기준은 내용이 아니라 activation 방식이다.

| Applicability | Surface |
| --- | --- |
| path, glob, file type, extension 등 repository structure가 결정 | Rule |
| task intent와 semantic relevance가 결정 | [Skill](skill.md) |

따라서 "정책이면 Rule, workflow면 Skill"처럼 분류하지 않는다. 같은 성격의 지침도 항상 특정 file scope에서 필요하면 Rule이고, 특정 task에서만 필요하면 Skill이 될 수 있다.

## Source

이 repository에서 직접 작성·관리하는 cross-cutting Rule은 `.rulesync/rules/**`의 **Rulesync Rule**을 canonical source로 사용한다.

외부에서 도입하는 Rule 또는 Skill이 **Rulesync asset으로 제공된다면 Rulesync 경로로 관리한다.** Rulesync-native asset을 다른 형식으로 다시 포장해 별도 source를 만들지 않는다.

Generated projection과 `.agents/route/rules.jsonl`은 runtime 또는 discovery를 위한 derived surface이며 독립적인 policy owner가 아니다. Selector와 target별 projection semantics는 Rulesync와 실제 target runtime의 current contract를 따른다.

## Boundary

- repository-wide / directory instruction ownership과 asset management: [AI Agent Instructions](README.md)
- task-selected instruction과 표준 Skill dependency: [Skill](skill.md)
- Rulesync integration detail: [`.rulesync/README.md`](../../../.rulesync/README.md)
