# Context Route

Known target path마다 repository root에서 target directory까지 applicable `AGENTS.md`를 로드한다. 충돌하지 않는 상위 guidance는 유지하고 더 가까운 scoped override를 우선한다.

[`skills.jsonl`](skills.jsonl)과 [`rules.jsonl`](rules.jsonl)을 끝까지 읽고 각 `_meta.instructions`를 따른다. 선택된 source와 그 source가 현재 task에 요구하는 context만 추가로 읽는다.

Task intent나 target path가 바뀌면 applicable `AGENTS.md`, Skill, Rule을 다시 계산한다. 이미 로드했고 여전히 applicable한 context는 재사용한다.
