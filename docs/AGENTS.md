# Documentation Rules

`docs/`는 현재 시스템의 durable knowledge, 현재 active goal, 개발 가이드와 인간용 편의 문서를 구분한다. 같은 사실을 여러 위치에서 독립적으로 소유하지 않는다.

## Ownership

| Area | Owns |
| --- | --- |
| `vision.md` | 장기 방향과 제품 원칙 |
| `ARCHITECTURE.md` | 시스템 흐름과 cross-domain boundary |
| `domains/**` | 각 domain의 책임, 공개 surface와 비책임 |
| `mvp.md` | 현재 active MVP의 목표, scope와 acceptance |
| `development/**` | phase와 무관하게 유지되는 개발 방법과 repository 운영 가이드 |
| `dashboard.md` | 사람이 빠르게 보는 비권위 상태 snapshot |
| `references/**` | 외부 규격과 supporting reference |

OpenSpec의 capability contract ownership은 `docs/`가 아니라 `openspec/specs/**`에 있다.

## Trust Model

문서 유형마다 답하는 질문이 다르다. 하나의 artifact가 다른 종류의 evidence를 대신하지 않는다.

- **Implementation:** current source, configuration과 generated contract surface를 직접 확인한다.
- **Canonical capability contract:** `openspec/specs/**`가 현재 capability의 canonical OpenSpec contract를 소유한다.
- **Change plan:** `openspec/changes/**`는 제안, 설계, task, review와 intended delta를 담는 작업 공간이다. Change는 current system의 canonical source가 아니며 대응 Spec을 직접 override하지 않는다.
- **Executable specification:** tests는 expected behavior와 regression boundary를 표현하지만 test 파일의 존재 자체는 passing evidence가 아니다.
- **Durable architecture / ownership:** `ARCHITECTURE.md`와 `domains/**`가 시스템 흐름과 domain ownership boundary를 설명한다.
- **Validation result:** matching repository revision에서 실제 실행된 command, CI result 또는 보존된 runtime evidence만 사용한다.
- **Active goal:** `mvp.md`는 목표와 acceptance를 정의하지만 구현 완료 여부의 evidence가 아니다.
- **Dashboard:** `dashboard.md`는 **사람을 위한 convenience projection**이다. Agent context, repository orientation, current state, validation result, blocker 또는 우선순위의 source로 사용하지 않는다.

Source와 canonical Spec이 다르면 implementation drift로, tests나 실행 결과가 canonical Spec과 다르면 contract/validation drift로 보고한다. Change나 dashboard를 사용해 그 충돌을 해소하지 않는다.

## OpenSpec Lifecycle

1. `openspec/changes/**`에서 변경 목적, delta, 설계, task와 review를 계획하고 추적한다.
2. Change가 진행 중인 동안에도 current capability의 canonical contract는 `openspec/specs/**`다.
3. 구현·검증된 durable contract는 OpenSpec workflow에 따라 `openspec/specs/**`에 반영한다.
4. 반영이 끝난 Change는 archive할 수 있지만, archive된 Change 역시 historical work artifact이지 current contract가 아니다.

## Dashboard Policy

- Agent는 사용자가 dashboard 자체를 묻거나 task가 dashboard refresh일 때만 `dashboard.md`를 읽는다.
- Dashboard는 별도의 명시적 dashboard refresh 작업에서만 갱신한다.
- 일반 feature, fix, refactor, test, spec 또는 documentation 작업은 dashboard가 stale해질 수 있다는 이유만으로 함께 수정하지 않는다.
- Dashboard refresh는 owning source를 다시 읽어 사람용 snapshot을 재구성하고 기준 revision과 미검증 상태를 명시한다.
- Dashboard에는 canonical contract, acceptance definition 또는 machine-readable SSOT를 새로 만들지 않는다. 필요한 정의는 owning document에 링크한다.

## Phase Lifecycle

Phase 문서는 active phase 동안만 `main`에 둘 수 있다.

1. Active phase는 목표, scope와 acceptance만 소유한다.
2. Canonical capability contract, architecture guidance, 개발 규칙과 runtime behavior를 phase 문서에 복제하지 않는다.
3. Phase가 끝나면 장기 가치가 있는 지식을 해당 owning location에 반영한다. Capability contract는 `openspec/specs/**`, architecture/domain guidance는 `docs/**`에 반영한다.
4. 필수 참조가 남지 않았는지 확인한 뒤 완료된 phase bundle을 `main`에서 삭제한다.
5. 완료된 phase를 보존하기 위해 `docs/archive/**` 같은 별도 phase archive를 만들지 않는다. Git history, Pull Request, OpenSpec archive와 필요한 inbox artifact가 history를 보존한다.

현재 active phase가 끝나면 `mvp.md`도 같은 lifecycle을 따른다.

## Writing

- 한 사실에는 한 owning source를 둔다.
- 목표, canonical contract, historical work evidence와 인간용 summary를 섞지 않는다.
- 현재성을 자주 잃는 상태 정보는 canonical Spec이나 durable guide에 넣지 않는다.
- KISS, DRY, YAGNI를 우선한다.
