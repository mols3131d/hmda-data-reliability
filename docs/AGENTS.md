# Documentation Rules

`docs/`는 durable guidance, active goal, development guide와 human-only projection을 구분한다. 이 파일은 **`docs/**` 전체에 공통인 문서 규칙만** 소유하며, 더 좁은 subtree 규칙은 가까운 `AGENTS.md`가 소유한다.

## Ownership

| Area | Owns |
| --- | --- |
| `vision.md` | 장기 방향과 제품 원칙 |
| `ARCHITECTURE.md` | 시스템 흐름과 cross-domain boundary guidance |
| `domains/**` | 각 domain의 책임, 공개 surface와 비책임을 설명하는 guide |
| `mvp.md` | 현재 active MVP의 목표, scope와 acceptance |
| `development/**` | phase-independent 개발 가이드와 human-only development dashboard; 세부 규칙은 [`development/AGENTS.md`](development/AGENTS.md) |
| `references/**` | 외부 규격과 supporting reference |

Current capability의 normative contract는 `docs/`가 아니라 [`../openspec/specs/`](../openspec/specs/)가 소유한다. OpenSpec workflow 규칙은 [`../openspec/AGENTS.md`](../openspec/AGENTS.md)가 소유한다.

## Trust Boundary

문서 유형마다 답하는 질문이 다르다. 하나의 artifact가 다른 종류의 evidence를 대신하지 않는다.

- **Implementation:** current source와 configuration을 직접 확인한다.
- **Normative capability contract:** `openspec/specs/**`를 사용한다. `openspec/changes/**`는 current Spec을 대신하지 않는다.
- **Architecture / domain ownership:** `ARCHITECTURE.md`와 `domains/**`는 구조와 책임 경계를 설명하는 durable guide다. Capability contract를 소유하지 않는다.
- **Executable specification:** tests는 expected behavior와 regression boundary를 표현하지만 test 존재 자체는 passing evidence가 아니다.
- **Validation result:** matching repository revision의 command, CI result 또는 보존된 runtime evidence만 사용한다.
- **Active goal:** `mvp.md`는 목표와 acceptance를 소유하지만 implementation status나 validation result를 소유하지 않는다.
- **Human projection:** `development/dashboard.md`는 편의용 snapshot이며 current state나 validation evidence를 소유하지 않는다. 세부 dashboard 규칙은 `development/AGENTS.md`가 소유한다.

Owning source가 서로 다르면 문서에서 임의로 하나를 정답으로 만들지 않고 drift를 명시한다.

## Phase Lifecycle

Phase 문서는 active phase 동안만 `main`에 둘 수 있다.

1. Active phase는 목표, scope와 acceptance만 소유한다.
2. Normative capability contract, architecture guidance, 개발 규칙과 runtime behavior를 phase 문서에 복제하지 않는다.
3. Phase가 끝나면 장기 가치가 있는 지식을 해당 owning location에 반영한다.
4. 필수 참조가 남지 않았는지 확인한 뒤 완료된 phase bundle을 `main`에서 삭제한다.
5. 완료된 phase만을 보존하기 위한 `docs/archive/**`는 만들지 않는다. Git history, Pull Request, OpenSpec archive와 필요한 inbox artifact가 history를 보존한다.

현재 active phase가 끝나면 `mvp.md`도 같은 lifecycle을 따른다.

## Writing

- 한 사실에는 한 owning source를 둔다.
- 목표, normative contract, historical work evidence와 human summary를 섞지 않는다.
- 현재성을 자주 잃는 상태 정보는 durable guide나 normative contract에 복제하지 않는다.
- 링크 대상의 역할을 과장하지 않는다. Guide는 guide로, contract는 contract로 표현한다.
