# Rulesync

Repository-owned Agent Asset은 `.rulesync/`를 canonical source로 사용한다. Generated target asset은 derived projection이므로 직접 수정하지 않는다.

설정은 [`rulesync.jsonc`](../../rulesync.jsonc), 실행 방법은 [`scripts/rulesync.py`](../../scripts/rulesync.py)를 기준으로 한다. 변경할 때는 `preview → generate → validate` 순서로 확인하고, Skill projection이 바뀌면 chatbot route도 다시 생성한다.

## Exceptions

- `delete: true`는 shared output surface의 잘못된 orphan cleanup을 피하기 위해 사용하지 않는다. Asset을 삭제하거나 retarget하면 stale projection을 확인 후 명시적으로 정리한다.
- Codex CLI와 Antigravity CLI의 path-scoped Rule은 current adapter 제약 때문에 root `AGENTS.md`에서 canonical Rule로 route한다. 이 routing은 `.rulesync/rules/codex-root.md`가 소유한다.
- 다른 tool이나 framework가 자체 lifecycle로 관리하는 자산은 Rulesync로 복제하거나 재정의하지 않는다.
