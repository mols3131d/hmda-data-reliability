# Rulesync

Repository Agent asset policy는 [`docs/development/ai-agent/README.md`](../docs/development/ai-agent/README.md)를 따른다.

## Projection Ownership

| Surface | Git | Role |
| --- | --- | --- |
| `.rulesync/rules`, `.rulesync/skills/prj-*`, `.rulesync/subagents`, config와 lock | Track | canonical source와 재현 가능한 dependency state |
| `.github/instructions` | Track | GitHub.com이 repository에서 직접 소비하는 projection |
| `.agents/rules`, `.agents/skills`, `.agents/agents`, `.claude/**`, `.codex/**`, `.github/agents`, `.github/skills/**`, generated `CLAUDE.md` | Ignore | runtime projection이며 필요할 때 Rulesync로 재생성 |
| `.agents/route` | Track | chatbot discovery용 derived index |

External Rulesync와 Skills CLI 설치물은 추적하지 않는다. Chatbot routing은 설치 경로 대신 upstream Skill을 사용한다. Rulesync는 lock의 resolved revision을 사용하고, Skills CLI version 1 lock은 실제 source revision의 Skill 폴더가 `computedHash`와 일치할 때만 해당 commit URL을 채택한다.

## Agent Execution

외부 Skill을 지원하는 coding agent로 직접 실행하려면 다음 command를 사용한다.

```bash
uv run python scripts/agent_assets.py run <source> --skill <name> --agent <id>
```

이 command는 `npm exec`를 통해 Skills CLI의 `use` command를 실행한다. `source`, `skill`과 `agent`를 모두 명시해야 하며, 지원되는 agent identifier와 실제 실행·권한 semantics는 Skills CLI와 target runtime이 소유한다.

## Chatbot Route

[`scripts/agent_routes/`](../scripts/agent_routes/)는 repository-owned Rule/Skill과 locked external Skill에서 `.agents/route` index를 생성한다. 저장소 루트에서 `uv run python -m scripts.agent_routes`로 생성하고 `uv run python -m scripts.agent_routes --check`로 검증한다.

Skills CLI lock의 `ref`와 `skillPath`는 optional이다. 누락 시 실제 default revision과 Skill 이름으로 경로를 해석하지만 내용이 lock과 다르면 실패한다. `computedHash`는 Git revision이 아니며, 과거 snapshot을 복원하는 주소도 아니다. Hash 검증은 vendor와 동일한 Node.js 경로 정렬을 사용한다. `--check`는 파일을 쓰지 않으며 일치·drift·입력/조회 오류의 종료 코드는 각각 0·1·2다.
