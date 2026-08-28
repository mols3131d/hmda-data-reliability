# Harness Compatibility

`CHATBOT.md`는 chatbot harness를 repository guidance와 Agent Assets에 연결하는 최소 bootstrap이다. 정책, Skill 또는 Rule 본문은 여기서 소유하지 않는다.

## Load

- 항상 [`AGENTS.md`](AGENTS.md)와 [`.agents/route/ROUTE.md`](.agents/route/ROUTE.md)를 읽는다.
- Git/GitHub 작업에서는 [`.rulesync/skills/prj-vcs-git-github/SKILL.md`](.rulesync/skills/prj-vcs-git-github/SKILL.md)를 반드시 읽고, 필요한 guide, template과 live context 선택은 해당 Skill에 위임한다.
- Repository path를 읽거나 변경하기 전에 root부터 target까지 적용되는 모든 `AGENTS.md`를 읽는다. 충돌하면 target에 가까운 지침을 우선하며, target이 바뀌면 다시 계산한다.
- Repository 또는 GitHub object의 현재 상태가 판단에 영향을 주면 GitHub plugin으로 live state를 확인한다.

## Boundary

- Repository guidance와 platform/runtime guidance는 각자의 scope에만 적용한다. 서로의 authority를 재정의하거나 platform-specific behavior를 명시적인 요청 없이 repository policy로 영구 반영하지 않는다.
