# Documentation Rules

`docs/`는 durable guidance, active goal, development guide와 human-only projection을 구분한다. 이 파일은 **`docs/**`의 공통 작성·trust·lifecycle 규칙**을 소유하며, subject-specific workflow는 해당 owning guide가 소유한다.

## Ownership

| Area | Owns |
| --- | --- |
| `vision.md` | 장기 방향과 제품 원칙 |
| `ARCHITECTURE.md` | 시스템 흐름과 cross-domain boundary guidance |
| `domains/**` | 각 domain의 책임, 공개 surface와 비책임을 설명하는 guide |
| `mvp.md` | 현재 active MVP의 목표, scope와 acceptance |
| `development/**` | phase-independent 개발 가이드와 human-only development dashboard |
| `references/**` | 외부 규격과 supporting reference |

Current capability의 normative contract는 `docs/`가 아니라 [`../openspec/specs/`](../openspec/specs/)가 소유한다. OpenSpec-specific agent와 workflow 규칙은 [`../openspec/AGENTS.md`](../openspec/AGENTS.md)를 진입점으로 해당 owning file을 따른다.

## Trust Boundary

문서 유형마다 답하는 질문이 다르다. 하나의 artifact가 다른 종류의 evidence를 대신하지 않는다.

- **Implementation:** current source와 configuration을 직접 확인한다.
- **Normative capability contract:** `openspec/specs/**`를 사용한다.
- **Architecture / domain ownership:** `ARCHITECTURE.md`와 `domains/**`는 구조와 책임 경계를 설명하는 durable guide다.
- **Executable specification / validation:** tests는 expected behavior를 표현하지만 passing evidence는 matching repository revision의 command, CI result 또는 보존된 runtime evidence에서 확인한다.
- **Active goal:** `mvp.md`는 목표와 acceptance를 소유하지만 implementation status나 validation result를 소유하지 않는다.
- **Human projection:** `development/dashboard.md`는 편의용 snapshot이며 current state나 validation evidence를 소유하지 않는다.

Owning source가 서로 다르면 문서에서 임의로 하나를 정답으로 만들지 않고 drift를 명시한다.

## Dashboard Policy

- 사용자가 dashboard 자체를 묻거나 task가 명시적인 dashboard refresh인 경우에만 `development/dashboard.md`를 읽는다. 그 외 orientation, planning, implementation, review 또는 validation에 사용하지 않는다.
- Dashboard는 별도의 dashboard refresh 작업에서만 갱신한다. 일반 feature, fix, refactor, test, spec 또는 documentation 작업의 side effect로 수정하지 않는다.
- Refresh는 installed `mols-markdown-dashboard` skill을 사용하고 current owning sources와 matching-revision evidence에서 사실을 다시 도출한다. Skill contract를 이 파일에 복제하지 않는다.
- `development/dashboard.md`는 human-only non-canonical projection으로 유지한다. 별도 요청 없이 추가 dashboard SSOT를 만들지 않는다.

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
