# HMDA Data Reliability Chatbot Instructions

`CHATBOT.md`는 native repository instruction discovery를 보완하는 최소 compatibility bootstrap이다. Project policy, Skill, Rule 또는 workflow 세부사항을 여기서 소유하지 않는다.

## Bootstrap

1. [`AGENTS.md`](AGENTS.md)를 끝까지 읽고 root guidance를 적용한다.
1. [`.agents/route/ROUTE.md`](.agents/route/ROUTE.md)를 끝까지 읽고 current task intent와 known target path에 맞는 Skill과 Rule을 선택한다.
1. Repository path를 읽거나 변경하기 전에 root부터 target까지 적용되는 `AGENTS.md`를 모두 읽는다.
1. Route가 선택한 source와 그 source가 요구하는 context를 해당 작업 전에 읽는다.
1. Task intent, operation 또는 target path가 달라지면 applicable context를 다시 계산한다. 같은 revision에서 이미 읽었고 여전히 applicable한 context는 재사용한다.

## Routing Priority

Chatbot에서는 repository content를 변경하는 작업을 Git/GitHub context trigger로 취급하고 [`prj-vcs-git-github`](.rulesync/skills/prj-vcs-git-github/SKILL.md)를 로드한다. Git 또는 GitHub의 mutable state가 판단에 영향을 주거나 branch, commit, Pull Request, review, merge 같은 VCS operation을 수행하는 경우에도 이 Skill을 로드한다. 단순한 read-only repository content 조회만으로는 이 Skill을 강제하지 않는다. 세부 VCS 정책과 추가 context 선택은 이 Skill이 소유한다.

## Loading Gate

- Required source의 일부만 로드되거나 output이 truncated되면 읽은 것으로 간주하지 않는다. 필요한 경우 범위를 좁히거나 나눠서 끝까지 읽는다.
- Required context를 확인할 수 없으면 그 context에 의존하는 mutation이나 판단을 추측으로 진행하지 않고 limitation을 명시한다.
- Route와 index metadata는 discovery만 소유한다. 선택된 canonical source가 실제 behavior와 policy를 소유한다.

## Boundary

Repository guidance와 platform/runtime guidance는 각자의 scope에만 적용한다. Compatibility bootstrap은 authority를 재정의하지 않으며, platform-specific behavior를 명시적인 요청 없이 repository policy로 영구 반영하지 않는다.

- Chatbot compatibility는 repository의 local development workflow보다 우선하지 않는다. 오직 Chatbot을 더 쉽게 동작시키기 위해 repository structure, tooling, tracked state 또는 개발 workflow를 변경하지 않는다.
- Local tool이나 runtime이 자연스럽게 소유하는 작업과 derived state는 해당 local workflow에 맡긴다. Chatbot이 직접 처리하기 어렵다는 이유로 lockfile, generated output, install/update 결과 등을 원격에서 수동 재현하거나 우회 구현하지 않으며 local development에 추가 부담을 만들지 않는다.
- 특히 `*.lock` 파일(예: `rulesync.lock`, `uv.lock`)은 local tool이나 runtime이 생성·갱신하는 managed state로 취급한다. Chatbot은 원격에서 직접 편집하지 않고 해당 local workflow가 변경을 생성하도록 맡긴다.
