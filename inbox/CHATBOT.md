# Inbox Chatbot Entry

이 entry는 GitHub 같은 연결 도구로 `inbox/**`를 다루는 AI chat service에만 적용한다.

Inbox의 의미, artifact contract와 lifecycle은 [`AGENTS.md`](AGENTS.md)를 따른다. 이 파일은 **chatbot의 artifact delivery 방식만** 추가한다.

## Delivery

- 사용자가 standalone working artifact를 repository `inbox/`에 저장하라고 요청했고 기존 작업 branch나 Pull Request가 그 artifact를 소유하지 않으면 dedicated `inbox` branch에 저장한다.
- 이미 진행 중인 repository 변경, branch 또는 Pull Request와 직접 연결된 artifact는 명시적 요청이 없는 한 그 작업 branch에 함께 둔다.
- Inbox artifact를 저장하기 위해 다른 agent의 branch로 전환하거나 그 branch를 갱신하지 않는다.
- Dedicated `inbox` branch 사용은 chatbot의 standalone artifact delivery에만 허용되는 예외다. Local agent의 일반 작업이나 repository 변경 workflow로 확장하지 않는다.

## Isolation

Dedicated `inbox` branch에 direct push할 때는 해당 standalone artifact만 변경한다.

- `inbox/YYYY-MM-DD/**`의 요청된 artifact 외 repository content를 수정하지 않는다.
- `AGENTS.md`, `CHATBOT.md`, `README.md`, `_guidelines/`, `_templates/` 같은 운영 자산은 direct-push 예외에 포함하지 않는다.
- `inbox` branch를 `main`이나 다른 작업 branch로 merge, rebase, cherry-pick 또는 promotion하지 않는다.
- Artifact delivery를 위해 `main`이나 다른 작업 branch를 수정·reset·force-push하지 않는다.
- `main`을 `inbox`에 자동 sync하지 않는다. 현재 repository state가 필요하면 source branch를 읽어 evidence로 사용한다.
- Dedicated branch가 없을 때만 current remote `main`에서 생성할 수 있으며, 생성 자체가 `main`을 변경하지 않아야 한다.

## Authority

`inbox` branch의 artifact는 repository implementation status나 canonical truth의 근거가 아니다. 현재 상태 판단은 해당 작업의 owning source와 current branch를 직접 확인한다.
