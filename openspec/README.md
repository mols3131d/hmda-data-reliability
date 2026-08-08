# OpenSpec

`openspec/`는 canonical Spec과 이를 변경하는 Change를 관리한다.

## 구조

| 경로 | 역할 |
| --- | --- |
| [`specs/`](specs/) | 현재 시스템 capability의 canonical Spec |
| [`changes/`](changes/) | 진행 중인 Change와 완료된 archive |
| [`schemas/spec-driven-tdd/`](schemas/spec-driven-tdd/) | 재사용 가능한 `spec-driven-tdd` schema |

## 지침 소유권

| 파일 | 소유하는 지침 |
| --- | --- |
| [`schemas/spec-driven-tdd/schema.yaml`](schemas/spec-driven-tdd/schema.yaml) | 범용 workflow, artifact 목적·의존성·완료 조건과 gate |
| [`config.yaml`](config.yaml) | Project Pivot 전용 context, naming과 project-specific 추가 규칙 |
| [`AGENTS.md`](AGENTS.md) | OpenSpec workflow 사용 여부와 무관하게 `openspec/`에서 지켜야 할 agent 행동 규칙 |
| `README.md` | 구조, 개념과 지침 위치를 설명하는 인간용 안내 |
| `schemas/spec-driven-tdd/templates/*` | artifact 구조·필드·parser contract와 그 구조에 종속된 작성 안내 |

같은 규칙은 한 곳에서만 소유하고 다른 문서에서는 링크한다.

`schema.yaml`은 범용성과 호환성을 유지하며 project-specific 규칙이나 template surface의 세부 작성 규칙을 반복하지 않는다.

하위 `README.md`와 `AGENTS.md`에는 해당 경로에만 필요한 설명과 규칙만 둔다.
