# Harness Compatibility

`CHATBOT.md`는 repository-aware chat runtime에서 agent harness의 자동 context·asset loading이 누락될 때 이를 보정하는 compatibility entry다.

Chatbot과 coding agent를 별도 actor로 구분하지 않는다. 이 파일은 별도 project policy를 소유하지 않으며, 아래 source의 authority를 복제하거나 대체하지 않는다.

## Loading

현재 task에 필요한 범위에서 다음 behavior를 보정한다.

1. **`AGENTS.md` hierarchy** — known target path마다 repository root부터 target directory까지 applicable `AGENTS.md`를 로드한다. 더 가까운 `AGENTS.md`의 scoped override만 우선하고 독립적인 상위 guidance는 유지한다.
1. **Skills** — [`.agents/skills/`](.agents/skills/)의 `*/SKILL.md` metadata를 기준으로 task intent에 맞는 Skill만 선택해 로드한다. Skill body와 필요한 supporting resource는 선택된 경우에만 읽는다.
1. **Path-scoped Rules** — [`.agents/rules/`](.agents/rules/)와 [`.github/instructions/`](.github/instructions/)의 Rule selector를 known target path와 대조해 일치하는 Rule만 로드한다.
1. **Progressive context** — 선택된 guidance나 Agent Asset이 연결하는 source는 현재 판단에 필요한 만큼만 추가로 읽는다.

active harness가 같은 behavior를 이미 제공하면 중복 수행하지 않는다. task intent나 target path가 바뀌면 Skill과 Rule applicability를 다시 계산한다.

## Boundary

- project/repository policy는 applicable `AGENTS.md`와 Rule이 소유한다.
- Skill의 trigger, procedure, authority와 output semantics는 각 `SKILL.md`가 소유한다.
- `CHATBOT.md`를 `AGENTS.md` 또는 `README.md`와 연결한 filename fallback chain을 만들지 않는다.
- target path가 정해지지 않았으면 path-scoped Rule 전체를 선로드하지 않는다.
- Skill catalog, Rule body, path/glob table을 이 파일에 복제하지 않는다.
