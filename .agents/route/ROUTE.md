# Context Route

Known target path마다 repository root부터 target directory까지 applicable `AGENTS.md`를 로드한다. 충돌하지 않는 상위 guidance는 유지하고 더 가까운 scoped override를 우선한다.

[`skills.jsonl`](skills.jsonl)과 [`rules.jsonl`](rules.jsonl)은 derived discovery metadata다. JSONL에는 routing 지침을 두지 않고 canonical source만 가리킨다.

- `skills.jsonl`: `name`과 `description`으로 현재 task에 관련된 Skill을 모두 선택하고 선택한 `source`만 읽는다. 일치하는 Skill이 없으면 읽지 않는다.
- `rules.jsonl`: Known target path와 `globs`로 후보를 좁힌 뒤 `description`으로 현재 task에 관련된 Rule만 선택해 읽는다. Target path가 없으면 Rule source를 선로드하지 않는다.

선택된 source와 그 source가 요구하는 context만 추가로 읽는다. 각 `SKILL.md`와 canonical Rule이 behavior의 authoritative source다.

Task intent나 target path가 materially 바뀌면 applicable `AGENTS.md`, Skills, Rules를 다시 계산한다. 이미 로드했고 여전히 applicable한 context는 재사용한다.
