# Harness Compatibility

`CHATBOT.md`는 repository-aware chat runtime에서 native harness가 놓치는 repository guidance와 Agent Asset discovery만 보정하는 root compatibility entrypoint다.

## Loading

Active harness가 제공하지 않는 behavior만 현재 task 범위에서 보정한다.

1. **`AGENTS.md` hierarchy** — known target path마다 repository root부터 target directory까지 applicable `AGENTS.md`를 로드하고, 더 가까운 scoped override를 우선한다.
1. **Skills** — [`.agents/skills/`](.agents/skills/)의 `*/SKILL.md` metadata에서 task intent에 맞는 Skill만 선택한다. Skill body와 필요한 supporting resource는 선택된 경우에만 읽는다.
1. **Path Rules** — root `AGENTS.md`의 `Path Rules`를 따라 known target path와 일치하는 [`.rulesync/rules/`](.rulesync/rules/) canonical Rule만 읽는다.

추가 context는 현재 판단에 필요한 만큼만 읽는다. task intent나 target path가 바뀌면 Skill과 Rule applicability를 다시 계산한다.

## Boundary

Chatbot과 coding agent를 별도 policy actor로 구분하지 않는다. Root `CHATBOT.md` 하나만 사용하며, canonical guidance와 Agent Asset의 policy, authority, semantics를 복제·대체하거나 chatbot-specific policy, workflow, catalog를 만들지 않는다.
