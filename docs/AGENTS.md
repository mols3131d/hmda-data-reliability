# Documentation Rules

`docs/`는 durable guidance, active goal, development guide와 human-only projection을 구분한다. 이 파일은 **`docs/**`의 공통 작성·trust·lifecycle 규칙**을 소유하며, Git/GitHub 같은 subject-specific workflow는 해당 owning guide가 소유한다.

## Ownership

| Area | Owns |
| --- | --- |
| `vision.md` | 장기 방향과 제품 원칙 |
| `ARCHITECTURE.md` | 시스템 흐름과 cross-domain boundary guidance |
| `domains/**` | 각 domain의 책임, 공개 surface와 비책임을 설명하는 guide |
| `mvp.md` | 현재 active MVP의 목표, scope와 acceptance |
| `development/**` | phase-independent 개발 가이드와 human-only development dashboard |
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
- **Human projection:** `development/dashboard.md`는 편의용 snapshot이며 current state나 validation evidence를 소유하지 않는다.

Owning source가 서로 다르면 문서에서 임의로 하나를 정답으로 만들지 않고 drift를 명시한다.

## Dashboard Policy

- Agent는 사용자가 dashboard 자체를 묻거나 task가 명시적인 dashboard refresh일 때만 `development/dashboard.md`를 상태 판단에 사용한다.
- Dashboard는 별도의 dashboard refresh 작업에서만 갱신한다. 일반 feature, fix, refactor, test, spec 또는 documentation 작업의 side effect로 수정하지 않는다.
- Refresh는 installed `mols-markdown-dashboard` skill을 사용해 current canonical Spec, source, tests와 matching-revision execution evidence를 다시 조사한다.
- Project dashboard 계약의 `Development Progress`, `Implementation Gaps`, `Verification Gaps`를 유지하고 Requirement와 Verification Target을 의미 단위로 집계한다.
- 근거 없는 status나 denominator를 추측하지 않는다.
- Dashboard에 canonical contract, acceptance definition 또는 project-wide machine-readable SSOT를 새로 만들지 않는다.
- Repository artifact는 Markdown을 기본으로 유지한다. Skill이 작업용 YAML을 사용하더라도 별도 요청 없이 dashboard SSOT로 저장하지 않는다.

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
