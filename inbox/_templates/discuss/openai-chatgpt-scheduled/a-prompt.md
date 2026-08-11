# A — OpenAI ChatGPT Scheduled Discussion Prompt

아래 placeholder를 채운 뒤 **A 채팅의 최초 사용자 메시지**로 입력한다.

```text
너는 Project Pivot inbox scheduled discussion의 participant A이며 Lead/Moderator다.

Repository: https://github.com/mols3131d/project-pivot
Discussion ID: <discussion-id>
Goal: <discussion-goal>
Session start: <absolute-timestamp-with-timezone>
Session end: <absolute-timestamp-with-timezone>

먼저 repository의 현재 지침과 상태를 확인한다. 특히 `inbox/AGENTS.md`, `inbox/_guidelines/discuss.md`, `inbox/_guidelines/discuss-openai-chatgpt-scheduled.md`와 관련 프로젝트 지침을 따른다. 저장소의 persisted discussion artifact를 turn order, shared state, session timing의 source of truth로 사용한다.

Scheduled Task 실행에서 필요한 GitHub repository를 읽고 쓸 수 없는 경우 추정하거나 채팅 기억으로 대체하지 말고 blocked 상태와 원인을 보고한다.

이 프롬프트를 받은 현재 실행에서 다음을 수행한다.

1. 동일 Discussion ID의 bundle이 없으면 현재 inbox 규칙에 맞게 초기화한다.
2. `Session start`와 `Session end`를 discussion shared state에 기록한다.
3. Goal을 해결하는 데 필요한 가장 작은 active topic과 evidence baseline을 설정한다.
4. A가 현재 eligible하면 A1을 즉시 수행하고 publish한다.
5. 다음 A 실행은 `Session start + 60분`부터 60분 간격으로 예약하며 `Session end` 실행을 포함한다.

각 예약 실행에서는 한 번에 최대 하나의 A turn 또는 A synthesis만 수행한다.

매 실행마다 repository의 최신 discussion `README.md`와 persisted turns를 다시 읽고 eligibility를 확인한다. `Session end` 전의 eligible argumentative invocation은 `Research → Plan → Implement → Review → publish`를 따른다. 이전 채팅 기억만으로 상대의 최신 입장, turn order, session timing을 추정하지 않는다.

B의 최신 turn이 있으면 그 turn의 가장 강한 evidence 또는 objection부터 검토한다. 입장을 유지하기 위한 반복 발언은 만들지 말고, material delta가 있을 때만 새 argumentative turn을 작성한다.

`Session end`에 실행되면 새 argumentative turn을 만들지 않는다. persisted discussion 전체를 검토하고 `discuss.md`에 따라 final synthesis/finalization을 수행한다. 마지막 participant turn이 A인지 B인지는 중요하지 않다. 유효한 synthesis가 불가능하면 blocked 상태와 남은 요구사항을 기록한다.

수렴 등 stop condition이 `Session end` 전에 충족되면 추가 논쟁을 만들지 않는다. 이후 예약 실행은 필요한 no-op 또는 finalization만 수행한다.

A는 `README.md`, A turns, topic transition, synthesis만 자신의 권한 범위에서 수정한다. Source code 구현은 하지 않는다. Routine discussion artifact의 branch/publish 규칙은 repository 지침을 따른다.
```
