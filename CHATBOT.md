# Harness Compatibility

Root `CHATBOT.md`는 chatbot harness에서 누락되는 repository context와 Agent Asset loading을 보정한다. Repository state와 GitHub object를 읽거나 변경할 때는 GitHub plugin으로 live state를 확인한다.

항상 [`AGENTS.md`](AGENTS.md)와 [`.agents/route/ROUTE.md`](.agents/route/ROUTE.md)를 읽는다. Git/GitHub 세부 작업에 필요한 guide, template과 live context 선택은 Agent Asset routing에 위임하고 이 문서에서 중복 소유하지 않는다.
