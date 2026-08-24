# Agent Instructions

Agent instruction은 **scope와 loading 방식**에 따라 다음 세 surface로 나눈다.

| Scope | Surface | Use when |
| --- | --- | --- |
| directory | `AGENTS.md` | 해당 directory subtree에 공통으로 적용할 지침 |
| shared path / extension | Rulesync Rule | 여러 하위 directory나 특정 확장자처럼 glob으로 표현되는 공통 지침 |
| task-selected | `SKILL.md` | 모델이 현재 task에 필요하다고 판단할 때 선택적으로 load할 지침 |

한 지침을 여러 surface에 중복하지 않는다. Directory 구조로 충분한 지침을 Rule이나 Skill로 옮기지 않고, glob으로 표현하는 편이 자연스러운 지침을 `AGENTS.md`에 반복하지 않는다.

## Root `AGENTS.md`

Root `AGENTS.md`는 repository-wide **전역 지침이자 agent 전용 entrypoint**다.

Harness가 native로 지원하는 nested `AGENTS.md`, scoped Rule, Skill discovery는 root에서 다시 구현하거나 일일이 route하지 않는다. Root entrypoint에는 전역 규칙과 harness가 직접 지원하지 않는 compatibility routing만 둔다.

현재 Codex CLI와 Antigravity CLI의 path-scoped Rule routing은 이 예외에 해당하며 `.rulesync/rules/codex-root.md`가 소유한다.

## Asset Management

Repository-owned Rule과 Skill의 canonical source는 `.rulesync/`다. Generated target asset은 projection이므로 직접 수정하지 않는다. Rulesync 설정과 실행 방법은 `rulesync.jsonc`와 `scripts/rulesync.py`를 기준으로 한다.

외부 non-Rulesync Agent Asset은 **Rulesync로 직접 관리하는 것보다 Skills CLI가 더 효율적인 경우에만** Skills CLI를 사용한다. 설치 상태와 source는 `skills-lock.json`을 기준으로 하며 upstream source가 authority를 유지한다.

다른 tool이나 framework가 자체 lifecycle로 관리하는 asset은 그 source를 유지한다.

## Exceptions

- Rulesync의 `delete: true`는 shared output surface의 잘못된 orphan cleanup을 피하기 위해 사용하지 않는다. Asset 삭제나 retarget 후 stale projection은 확인하여 명시적으로 정리한다.
- Harness가 새로 native 지원하는 기능은 compatibility routing에서 제거하는 방향을 우선한다.
