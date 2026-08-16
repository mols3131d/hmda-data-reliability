# Chatbot Entry

`CHATBOT.md`는 표준 agent instruction 파일이 아니다. GitHub 연동을 통해 이 저장소를 다루는 AI chat service가 사용할 **저장소 전용 진입점**이다. Repository 규칙을 새로 소유하거나 [`AGENTS.md`](AGENTS.md)를 대체하지 않으며, chat 환경에서 현재 repository-owned guidance로 진입하는 방법과 chat-specific boundary만 정의한다.

## Start

1. [`AGENTS.md`](AGENTS.md)를 repository guidance의 기본 entry point로 사용한다.
2. 작업 경로에 더 가까운 `AGENTS.md`가 있으면 해당 범위에서 우선한다.
3. Root 또는 local guidance가 연결하는 owner 중 현재 task에 직접 필요한 것만 추가로 읽는다.

관련 없는 guidance를 예방적으로 모두 읽지 않는다.

## Repository State

- 현재 branch, Pull Request, file과 validation 상태가 판단에 필요하면 GitHub에서 다시 확인한다.
- 과거 대화, 기억 또는 이전 artifact만으로 current repository state를 단정하지 않는다.
- Human-only projection을 canonical state나 validation evidence로 사용하지 않는다.

## Chat Boundary

- 사용자의 요청 범위와 repository-owned guidance를 우선한다.
- 조사와 리뷰는 repository 변경 요청이 없는 한 read-only로 수행한다.
- Repository 변경과 Git/GitHub lifecycle은 적용되는 owning guidance를 따른다.
- Guidance 충돌을 해소할 수 없으면 임의로 우회하지 않고 충돌과 근거를 보고한다.
