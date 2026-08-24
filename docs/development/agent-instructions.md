# Agent Instructions

이 문서는 agent instruction의 owner를 정해 중복을 최소화한다. Scope와 loading 방식에 따라 다음 기준을 사용한다.

| Scope | Owner | Use when |
| --- | --- | --- |
| repository-wide | `/AGENTS.md` | 전역 지침과 agent entrypoint |
| directory | nearest `AGENTS.md` | 하나의 directory subtree에 공통으로 적용할 지침 |
| shared path / extension | Rulesync Rule | 여러 경로에서 공통으로 나타나는 하위 directory pattern이나 특정 확장자처럼 glob selector가 필요한 지침 |
| task-selected | `SKILL.md` | 모델이 task intent에 따라 선택적으로 load하는 지침. 일반적인 reusable Skill도 같은 surface를 사용한다. |

같은 지침을 여러 owner에 복제하지 않는다. 하나의 directory subtree가 자연스럽게 소유할 수 있으면 nearest `AGENTS.md`를 사용하고, directory hierarchy만으로 자연스럽게 표현하기 어려운 shared path/extension scope만 Rulesync Rule로 둔다.

이 문서는 지침의 owner 구분만 다룬다. 일반 Skill 설계와 generation, projection, installation, target compatibility, tool 실행 방법은 각 owning source가 소유한다.
