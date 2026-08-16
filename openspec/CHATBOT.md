# OpenSpec Chatbot Entry

`openspec/CHATBOT.md`는 OpenSpec 작업을 수행하는 AI chat service를 위한 **OpenSpec 전용 진입점**이다. Root [`CHATBOT.md`](../CHATBOT.md)와 [`AGENTS.md`](AGENTS.md)를 대체하지 않으며, OpenSpec 작업에서 필요한 Skill discovery와 routing만 추가한다.

## Routing

- OpenSpec Skill은 현재 task가 OpenSpec change, spec, artifact 또는 workflow를 직접 다룰 때만 사용한다.
- 비슷한 목적의 일반 Skill과 선택이 겹치면 **현재 작업이 OpenSpec 작업인지**로 결정한다. OpenSpec 작업이면 OpenSpec Skill을 우선하고, 아니면 일반 Skill을 사용한다.
- 적용되는 repository guidance와 path instruction은 Skill 선택과 별개로 계속 적용한다.
- 아래 표는 discovery projection이다. 실제 trigger와 동작은 linked `SKILL.md`가 source of truth다.

## Project OpenSpec Skill

| Skill | Trigger |
| --- | --- |
| [`pivot-spec-driven-tdd-rpi`](../.agents/skills/pivot-spec-driven-tdd-rpi/SKILL.md) | Research가 OpenSpec change를 결정·수정하거나 Review finding을 owning work로 되돌려야 할 때. 일반 schema-owned planning이나 Research·Review 입력 없는 Apply에는 사용하지 않음 |

## OpenSpec Skills

OpenSpec upstream이 제공하는 workflow Skill이다. Repository에 같은 Skill이 설치되면 repository의 현재 copy와 적용되는 guidance를 우선한다.

| Skill | Trigger |
| --- | --- |
| [`openspec-propose`](https://github.com/Fission-AI/OpenSpec/blob/main/skills/openspec-propose/SKILL.md) | 새 change를 제안하고 proposal, design, specs와 tasks를 한 번에 생성해 implementation-ready planning을 준비할 때 |
| [`openspec-update-change`](https://github.com/Fission-AI/OpenSpec/blob/main/skills/openspec-update-change/SKILL.md) | 기존 change의 planning artifact를 수정하거나 새 결정을 반영하고 artifact 간 정합성을 맞출 때. 코드는 수정하지 않음 |
| [`openspec-explore`](https://github.com/Fission-AI/OpenSpec/blob/main/skills/openspec-explore/SKILL.md) | change 전이나 진행 중 아이디어를 탐색하고 문제를 조사하거나 요구사항을 명확히 할 때 |
| [`openspec-sync-specs`](https://github.com/Fission-AI/OpenSpec/blob/main/skills/openspec-sync-specs/SKILL.md) | change를 archive하지 않고 delta spec을 main spec에 동기화할 때 |
| [`openspec-archive-change`](https://github.com/Fission-AI/OpenSpec/blob/main/skills/openspec-archive-change/SKILL.md) | implementation이 완료된 change를 최종화하고 archive할 때 |

OpenSpec Skill은 OpenSpec workflow의 authority를 소유하지 않는다. Artifact 목적, dependency, gate와 project-specific 규칙은 현재 적용되는 OpenSpec guidance와 schema/config가 소유한다.
