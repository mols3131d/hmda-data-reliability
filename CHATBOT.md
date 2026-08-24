# Harness Compatibility

Root `CHATBOT.md`는 chatbot harness에서 누락되는 context와 Agent Asset loading을 보정한다.

## Context Loading

1. 먼저 [`AGENTS.md`](AGENTS.md)를 읽고 현재 task와 target path에 적용되는 guidance를 따른다. Target path에 더 가까운 `AGENTS.md`가 있으면 root부터 target directory까지 함께 로드하고 scoped override를 우선한다.
1. [`.agents/skills/`](.agents/skills/)의 `*/SKILL.md` metadata에서 task intent에 맞는 Skill만 선택하고, 선택한 Skill body와 필요한 supporting resource만 읽는다.
1. Root `AGENTS.md`의 `Path Rules`에 따라 target path와 일치하는 [`.rulesync/rules/`](.rulesync/rules/) canonical Rule만 읽는다.
1. 연결된 context는 현재 판단에 필요할 때만 추가로 읽는다. Task intent나 target path가 바뀌면 Skill과 Rule applicability를 다시 계산한다.

Native harness가 이미 처리하는 loading은 반복하지 않는다.
