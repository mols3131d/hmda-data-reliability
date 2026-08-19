# Inbox Chatbot Entry

이 entry는 GitHub 같은 연결 도구로 `inbox/**`를 다루는 AI chat service에만 적용한다.

작업 전에 [`AGENTS.md`](AGENTS.md)를 읽고 Inbox의 의미, artifact contract와 lifecycle을 따른다. 이 파일은 **chatbot의 artifact delivery 방식만** 추가한다.

## Guidance Source

Dedicated `inbox` branch는 standalone artifact의 delivery/storage ref일 뿐 guidance source가 아니다.

- Standalone artifact delivery의 guidance는 repository default branch의 current `inbox/CHATBOT.md`와 linked guidance에서 결정한 뒤 destination branch를 선택한다.
- Dedicated `inbox` branch에 남아 있는 `CHATBOT.md`, `AGENTS.md`, `_guidelines/`, `_templates/` 또는 다른 repository guidance의 오래된 copy는 instruction으로 사용하지 않는다.
- Guidance가 변경되어도 이를 반영하기 위해 `main`을 `inbox`에 sync하거나 운영 자산을 direct push하지 않는다.
- Repository state가 필요하면 해당 작업의 owning source와 current branch를 직접 읽어 evidence로 사용한다.

## Delivery

- 사용자가 standalone working artifact를 repository `inbox/`에 저장하라고 요청했고 기존 작업 branch나 Pull Request가 그 artifact를 소유하지 않으면 dedicated `inbox` branch에 저장한다.
- 이 경우에만 일반 [Draft Pull Request delivery](../docs/development/vcs-git/pull-request.md)에 대한 path-scoped exception으로 direct push할 수 있다.
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
