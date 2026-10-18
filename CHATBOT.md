# HMDA Data Reliability Chatbot Instructions

## Bootstrap

1. [`AGENTS.md`](AGENTS.md)와 대상 경로에 적용되는 하위 `AGENTS.md`를 읽는다.
1. [`.agents/route/ROUTE.md`](.agents/route/ROUTE.md)에 따라 작업과 대상 경로에 필요한 Skill·Rule을 선택해 읽는다.
1. 적용되는 지침이 요구하는 가이드라인·템플릿 등 후속 context를 작업 전에 읽고 적용한다.

## Checks

- 일부만 로드되거나 잘린 필수 context는 미확인으로 취급한다. 확인할 수 없는 지침에 의존한 판단·변경은 진행하지 않고 한계를 알린다.
- 작성·수정한 산출물은 적용되는 필수 계약과 대조하고, 검증하지 못한 사항을 명시한다.

## Boundary

- Repository content 변경이나 Git/GitHub mutable state가 관련되는 작업에서는 [`prj-vcs-git-github`](.rulesync/skills/prj-vcs-git-github/SKILL.md)를 로드한다.
- Chatbot 편의를 위해 repository workflow를 변경하거나 local tooling이 소유하는 managed state(예: `*.lock`, generated output)를 원격에서 수동 편집하지 않는다.
