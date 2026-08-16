# OpenSpec Chatbot Entry

`openspec/`를 다루는 AI chat service의 directory context entry다. OpenSpec Skill discovery와 routing만 추가한다.

## Routing

- OpenSpec Skill은 OpenSpec change, spec, artifact 또는 workflow를 직접 다룰 때만 사용한다.
- 비슷한 일반 Skill과 겹치면 OpenSpec 작업에는 OpenSpec Skill을, 그 외에는 일반 Skill을 사용한다.
- 아래 표는 discovery index다. 실제 trigger와 동작은 linked `SKILL.md`가 소유한다.

## Project Skill

| Skill | Trigger |
| --- | --- |
| [`pivot-spec-driven-tdd-rpi`](../.agents/skills/pivot-spec-driven-tdd-rpi/SKILL.md) | Research 또는 Review 결과를 OpenSpec change에 연결할 때 |

## OpenSpec Skills

| Skill | Trigger |
| --- | --- |
| [`openspec-propose`](https://github.com/Fission-AI/OpenSpec/blob/main/skills/openspec-propose/SKILL.md) | 새 change와 planning artifact를 한 번에 준비할 때 |
| [`openspec-update-change`](https://github.com/Fission-AI/OpenSpec/blob/main/skills/openspec-update-change/SKILL.md) | 기존 change의 planning artifact를 수정·정합화할 때 |
| [`openspec-explore`](https://github.com/Fission-AI/OpenSpec/blob/main/skills/openspec-explore/SKILL.md) | change 전·중 아이디어, 문제 또는 요구사항을 탐색할 때 |
| [`openspec-sync-specs`](https://github.com/Fission-AI/OpenSpec/blob/main/skills/openspec-sync-specs/SKILL.md) | archive 없이 delta spec을 main spec에 반영할 때 |
| [`openspec-archive-change`](https://github.com/Fission-AI/OpenSpec/blob/main/skills/openspec-archive-change/SKILL.md) | 완료된 change를 archive할 때 |

OpenSpec workflow와 schema의 authority는 적용되는 OpenSpec guidance, schema와 config가 소유한다.
