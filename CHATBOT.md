# Harness Compatibility

Root `CHATBOT.md`는 chatbot harness에서 누락되는 repository context와 Agent Asset loading을 보정한다. Repository state와 GitHub object를 읽거나 변경할 때는 GitHub plugin으로 live state를 확인한다.

항상 다음을 읽는다.

- [`AGENTS.md`](AGENTS.md)
- [`.agents/route/ROUTE.md`](.agents/route/ROUTE.md)
- Git/GitHub 작업에서는 `prj-vcs-git-github`를 반드시 선택·로드한다. 필요한 guide, template과 live context 선택은 해당 Skill에 위임하고, 세부 Git/GitHub 정책은 이 문서에서 중복 소유하지 않는다.

## Scoped AGENTS.md

Repository의 파일이나 디렉토리를 보거나 읽거나 작업하기 전에 해당 target에 적용되는 `AGENTS.md`를 함께 읽는다.

Repository root부터 target directory까지 경로에 있는 모든 applicable `AGENTS.md`를 읽는다. 같은 깊이의 `AGENTS.md`만 보지 않으며, 상위 scope의 guidance도 유지한다. 서로 충돌하면 target에 더 가까운 scoped `AGENTS.md`를 우선한다.

Target path가 작업 중 새로 생기거나 바뀌면 그 path에 적용되는 `AGENTS.md`를 다시 계산하고, 아직 읽지 않은 applicable guidance를 해당 target을 다루기 전에 읽는다.

## Scope Boundary

Repository guidance와 platform guidance를 구별하고 각각의 scope에만 적용한다.

- Repository guidance는 이 repository의 artifact, workflow, convention, state와 repository 안에서 수행하는 작업에 적용한다. 이를 chatbot platform 자체의 일반 동작이나 제약으로 확대 해석하지 않는다.
- Platform 또는 runtime guidance는 현재 chatbot, tool, host의 capability, safety, interaction과 platform-specific behavior에 적용한다. 이를 repository policy로 간주하거나 명시적인 요청 없이 repository 문서나 코드에 영구 반영하지 않는다.
- 두 scope가 동시에 관련되면 각각의 authority를 해당 범위에서 유지한다. Repository guidance로 platform 제약을 재정의하지 않고, platform-specific 동작을 repository convention으로 오인하지 않는다.
