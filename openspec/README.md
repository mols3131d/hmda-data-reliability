# OpenSpec

`openspec/`는 **current capability의 canonical Spec**과 시스템 변경을 계획·추적하는 **work Change**를 관리한다.

## 구조

| 경로 | 역할 | 권위 |
| --- | --- | --- |
| [`specs/`](specs/) | 현재 시스템 capability의 contract | **Canonical** |
| [`changes/`](changes/) | proposal, applicable specs, design, tasks와 intended change를 담는 작업 공간 및 archive | **Non-canonical** |
| [`schemas/spec-driven-tdd/`](schemas/spec-driven-tdd/) | 재사용 가능한 `spec-driven-tdd` schema | Workflow/schema contract |

Change는 시스템 변경의 계획과 실행 기록이다. Spec-level behavior가 바뀌면 delta Spec을 통해 canonical contract 변경을 제안하고, 그렇지 않은 Change는 `skip_specs: true`로 Spec을 변경하지 않는다. Change가 존재하거나 task가 완료됐다는 사실만으로 current capability contract가 바뀌지 않으며, 구현·검증된 durable contract가 OpenSpec workflow를 통해 `specs/**`에 반영된 뒤에야 canonical current Spec이 갱신된다.

Review feedback은 별도 canonical artifact가 아니라 원인을 소유하는 planning artifact 또는 implementation work로 route한다. Archive된 Change도 historical work artifact이며 current capability의 source of truth가 아니다.

## 지침 소유권

| 파일 | 소유하는 지침 |
| --- | --- |
| [`schemas/spec-driven-tdd/schema.yaml`](schemas/spec-driven-tdd/schema.yaml) | 범용 workflow, artifact 목적·의존성·완료 조건과 gate |
| [`config.yaml`](config.yaml) | 사용할 schema와 repository-specific context, naming, canonical boundary와 artifact별 추가 규칙 |
| `README.md` | 구조, canonical boundary와 지침 소유권을 설명하는 인간용 안내 |
| `schemas/spec-driven-tdd/templates/*` | artifact 구조·필드·parser contract와 그 구조에 종속된 작성 안내 |

같은 활성 지침은 한 곳에서만 소유하고 다른 문서에서는 그 소유 파일을 참조한다.

Change의 proposal/applicable specs/design/tasks는 작업 근거와 intended change를 설명할 수 있지만 `specs/**`의 current contract를 대체하지 않는다.

`schema.yaml`은 범용성과 호환성을 유지하며 project-specific 규칙이나 template surface의 세부 작성 규칙을 반복하지 않는다.

하위 `README.md`에는 해당 경로에만 필요한 설명을 둔다. OpenSpec update 이후에도 유지해야 하는 repository-specific agent guidance는 `config.yaml`의 `context` 또는 `rules`가 소유한다.
