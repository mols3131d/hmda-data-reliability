# Harness Compatibility

Root `CHATBOT.md`는 chatbot harness에서 누락되는 context와 Agent Asset loading을 보정한다.

## Instructions

- Native harness가 이미 제공하는 behavior는 반복하지 않는다.
- Known target path마다 repository root부터 target directory까지 applicable [`AGENTS.md`](AGENTS.md)를 로드하고, 더 가까운 scoped override를 우선한다.
- [`.agents/skills/`](.agents/skills/)의 `*/SKILL.md` metadata에서 task intent에 맞는 Skill만 선택하고, 선택한 Skill body와 필요한 supporting resource만 읽는다.
- Root `AGENTS.md`의 `Path Rules`에 따라 known target path와 일치하는 [`.rulesync/rules/`](.rulesync/rules/) canonical Rule만 읽는다.
- 추가 context는 현재 판단에 필요한 만큼만 읽는다.
- Task intent나 target path가 바뀌면 Skill과 Rule applicability를 다시 계산한다.
- Canonical guidance와 Agent Asset의 policy, authority, semantics를 복제하거나 대체하지 않는다.
- Chatbot-specific policy, workflow, catalog 또는 nested `CHATBOT.md` hierarchy를 만들지 않는다.
