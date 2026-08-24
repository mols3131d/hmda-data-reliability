# Agent Instructions

Agent instruction은 중복을 최소화하기 위해 하나의 책임 surface만 둔다. Scope와 loading 방식에 따라 다음 기준으로 구분한다.

| Scope | Surface | Use when |
| --- | --- | --- |
| repository-wide | `/AGENTS.md` | 전역 지침과 agent entrypoint |
| directory | nearest `AGENTS.md` | 하나의 directory subtree에 공통으로 적용할 지침 |
| shared path / extension | Rulesync Rule | 여러 위치에서 반복되는 하위 directory pattern이나 특정 확장자처럼 glob selector가 자연스러운 지침 |
| task-selected | `SKILL.md` | 모델이 task intent에 따라 선택적으로 load할 지침 또는 reusable capability |

같은 지침을 여러 surface에 복제하지 않는다. 하나의 자연스러운 directory subtree가 owner가 될 수 있으면 nested `AGENTS.md`를 사용하고, directory hierarchy만으로 자연스럽게 표현하기 어려운 shared path/extension scope만 Rulesync Rule로 둔다.

`SKILL.md`는 일반적인 reusable Skill도 포함한다. 이 문서는 그중 agent instruction을 어디에 둘지 구분하는 ownership 기준만 다룬다.

Generation, projection, installation, target compatibility와 각 tool의 실행 방법은 이 문서의 책임이 아니다.
