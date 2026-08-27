# Context Route

## Start

작업을 시작할 때 [`skills.jsonl`](skills.jsonl)과 [`rules.jsonl`](rules.jsonl)을 반드시 끝까지 읽는다. 두 파일은 작업 전체에서 재사용하는 derived discovery index이며 routing 지침 자체를 소유하지 않는다.

Known target path마다 repository root부터 target directory까지 applicable `AGENTS.md`를 로드한다. 충돌하지 않는 상위 guidance는 유지하고 더 가까운 scoped override를 우선한다.

초기 task intent와 known target path에 맞는 context만 선택한다.

- `skills.jsonl`: `name`과 `description`으로 관련 Skill을 선택하고 해당 `source`를 읽는다.
- `rules.jsonl`: target path와 `globs`로 후보를 좁힌 뒤 `description`으로 관련 Rule을 선택하고 해당 `source`를 읽는다. Target path가 없으면 Rule source를 선로드하지 않는다.

## During Work

`skills.jsonl`과 `rules.jsonl`은 처음 source를 고르는 일회성 링크 목록이 아니라 작업 중 계속 사용하는 routing index다.

새로운 concern, operation, target path, 또는 task intent가 생기면 두 index를 다시 기준으로 필요한 Skill과 Rule을 선택하고 **그 작업을 진행하기 전에** 읽는다. 처음 선택한 source에 고정하지 않는다. 이미 로드했고 여전히 applicable한 context는 재사용한다.

## Authority

선택된 source와 그 source가 요구하는 context만 추가로 읽는다. 각 `SKILL.md`와 canonical Rule이 해당 behavior의 authoritative source다.
