# Documentation Rules

`docs/`는 현재 시스템의 durable knowledge, 현재 active goal, 개발 가이드와 인간용 편의 문서를 구분한다. 같은 사실을 여러 위치에서 독립적으로 소유하지 않는다.

## Ownership

| Area | Owns |
| --- | --- |
| `vision.md` | 장기 방향과 제품 원칙 |
| `ARCHITECTURE.md` | 시스템 흐름과 cross-domain boundary |
| `domains/**` | 각 domain의 canonical 책임, 공개 contract와 비책임 |
| `mvp.md` | 현재 active MVP의 목표, scope와 acceptance |
| `development/**` | phase와 무관하게 유지되는 개발 방법과 repository 운영 가이드 |
| `dashboard.md` | 사람이 빠르게 보는 비권위 상태 snapshot |
| `references/**` | 외부 규격과 supporting reference |

## Trust Model

문서 유형마다 답하는 질문이 다르다. 하나의 artifact가 다른 종류의 evidence를 대신하지 않는다.

- **Implementation:** current source, configuration과 generated contract surface를 직접 확인한다.
- **Executable specification:** tests는 기대 behavior와 regression boundary를 설명하지만, test 파일의 존재 자체는 passing evidence가 아니다.
- **Active requirement:** current OpenSpec이 변경 요구사항과 acceptance intent를 소유한다.
- **Durable boundary:** `ARCHITECTURE.md`와 `domains/**`가 시스템·domain ownership을 소유한다.
- **Validation result:** matching repository revision에서 실제 실행된 command, CI result 또는 보존된 runtime evidence만 사용한다.
- **Active goal:** `mvp.md`는 목표와 acceptance를 정의하지만 구현 완료 여부의 evidence가 아니다.
- **Dashboard:** `dashboard.md`는 **사람을 위한 convenience projection**이다. Agent context, repository orientation, current state, validation result, blocker 또는 우선순위의 source로 사용하지 않는다.

서로 충돌하면 dashboard나 오래된 summary로 해소하지 말고 해당 owning source와 current revision evidence를 다시 확인한다.

## Dashboard Policy

- Agent는 사용자가 dashboard 자체를 묻거나 task가 dashboard refresh일 때만 `dashboard.md`를 읽는다.
- Dashboard는 별도의 명시적 dashboard refresh 작업에서만 갱신한다.
- 일반 feature, fix, refactor, test, spec 또는 documentation 작업은 dashboard가 stale해질 수 있다는 이유만으로 함께 수정하지 않는다.
- Dashboard refresh는 owning source를 다시 읽어 snapshot을 재구성하고 기준 revision과 미검증 상태를 명시한다.
- Dashboard를 machine-readable SSOT로 사용하거나 다른 문서가 dashboard 상태에 의존하게 만들지 않는다.

## Phase Lifecycle

Phase 문서는 active phase 동안만 `main`에 둘 수 있다.

1. Active phase는 목표, scope와 acceptance만 소유한다.
2. Domain contract, architecture, 개발 규칙과 runtime behavior를 phase 문서에 복제하지 않는다.
3. Phase가 끝나면 장기 가치가 있는 지식만 canonical owner에 반영한다.
4. 필수 참조가 남지 않았는지 확인한 뒤 완료된 phase bundle을 `main`에서 삭제한다.
5. 완료된 phase를 보존하기 위해 `docs/archive/**` 같은 별도 phase archive를 만들지 않는다. Git history, Pull Request, OpenSpec archive와 필요한 inbox artifact가 history를 보존한다.

현재 active phase가 끝나면 `mvp.md`도 같은 lifecycle을 따른다.

## Writing

- 한 사실에는 한 canonical owner를 둔다.
- 목표, 현재 사실, historical evidence와 인간용 summary를 섞지 않는다.
- 현재성을 자주 잃는 상태 정보는 durable contract 문서에 넣지 않는다.
- KISS, DRY, YAGNI를 우선한다.
