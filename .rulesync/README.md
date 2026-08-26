# Rulesync

Repository Agent asset policy는 [`docs/development/ai-agent/README.md`](../docs/development/ai-agent/README.md)를 따른다.

## Projection Ownership

| Surface | Git | Role |
| --- | --- | --- |
| `.rulesync/rules`, `.rulesync/skills/prj-*`, config와 lock | Track | canonical source와 재현 가능한 dependency state |
| `.agents/rules`, `.agents/skills`, `.claude/**`, generated `CLAUDE.md` | Ignore | local runtime용이며 bootstrap에서 재생성 |
| `.agents/route` | Track | chatbot discovery용 derived index |
| `.github/instructions`, `.github/skills/prj-review-code` | Track | GitHub.com이 repository에서 직접 소비하는 projection |

External Rulesync와 Skills CLI 설치물은 추적하지 않는다. Chatbot routing은 설치 경로 대신 lock의 exact ref에 고정된 upstream Skill을 사용한다.

## Chatbot Route

[`scripts/generate_agent_routes.py`](../scripts/generate_agent_routes.py)는 repository-owned Rule/Skill과 locked external Skill에서 `.agents/route` index를 생성한다.
