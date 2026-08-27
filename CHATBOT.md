# Harness Compatibility

Root `CHATBOT.md`는 chatbot harness에서 누락되는 repository context와 Agent Asset loading을 보정한다. Repository state와 GitHub object를 읽거나 변경할 때는 GitHub plugin으로 live state를 확인한다.

항상 [`AGENTS.md`](AGENTS.md)와 [`.agents/route/ROUTE.md`](.agents/route/ROUTE.md)를 읽는다. Git/GitHub 세부 작업에 필요한 guide, template과 live context 선택은 Agent Asset routing에 위임하고 이 문서에서 중복 소유하지 않는다.

## Scope Boundary

Repository guidance와 platform guidance를 구별하고 각각의 scope에만 적용한다.

- Repository guidance는 이 repository의 artifact, workflow, convention, state와 repository 안에서 수행하는 작업에 적용한다. 이를 chatbot platform 자체의 일반 동작이나 제약으로 확대 해석하지 않는다.
- Platform 또는 runtime guidance는 현재 chatbot, tool, host의 capability, safety, interaction과 platform-specific behavior에 적용한다. 이를 repository policy로 간주하거나 명시적인 요청 없이 repository 문서나 코드에 영구 반영하지 않는다.
- 두 scope가 동시에 관련되면 각각의 authority를 해당 범위에서 유지한다. Repository guidance로 platform 제약을 재정의하지 않고, platform-specific 동작을 repository convention으로 오인하지 않는다.
