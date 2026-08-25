# AI Agent Instructions

이 directory는 repository에서 AI agent instruction surface를 선택하는 기준을 소유한다. 구분 기준은 **내용의 종류가 아니라 적용 범위와 loading 방식**이다.

## Surface Selection

| Scope | Owner | Use when |
| --- | --- | --- |
| repository-wide | `/AGENTS.md` | 전역 지침과 agent entrypoint |
| directory | nearest `AGENTS.md` | 하나의 directory subtree에 공통으로 적용할 지침 |
| shared path / extension | [Rulesync Rule](rule.md) | 여러 경로에서 반복되는 directory pattern, file type, extension처럼 glob selector가 필요한 지침 |
| task-selected | [Skill](skill.md) | 모델이 task intent와 relevance에 따라 선택적으로 load할 지침, workflow 또는 reusable capability |

같은 지침을 여러 owner에 복제하지 않는다. 하나의 directory subtree가 자연스럽게 소유할 수 있으면 nearest `AGENTS.md`를 사용하고, directory hierarchy로 표현하기 어려운 cross-cutting path scope는 Rule을 사용한다. Task 의미에 따라 선택해야 하는 context는 Skill을 사용한다.

Rule과 Skill은 내용으로 구분하지 않는다. Skill도 정책, 제약, 판단 기준처럼 Rule과 유사한 **instruction-oriented content**를 가질 수 있다. Path나 glob이 applicability를 결정하면 Rule이고, task intent가 applicability를 결정하면 Skill이다.

## Documents

- [Rule](rule.md): path, glob, extension 기반 instruction scope와 Rulesync 관리 기준
- [Skill](skill.md): task-selected instruction과 reusable Skill의 source·dependency 기준

## Boundary

이 directory는 instruction owner와 loading 기준만 소유한다. Rulesync generation과 projection, Skills CLI 동작, target별 runtime semantics는 해당 tool과 runtime의 owning source를 따른다.
