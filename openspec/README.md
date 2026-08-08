# OpenSpec

`openspec/`는 canonical Spec과 이를 변경하는 Change를 관리한다.

| 경로 | 역할 |
| --- | --- |
| [`specs/`](specs/) | 현재 시스템 capability의 canonical Spec |
| [`changes/`](changes/) | 진행 중인 Change와 완료된 archive |
| [`schemas/spec-driven-tdd/schema.yaml`](schemas/spec-driven-tdd/schema.yaml) | artifact 순서, 의존성, gate와 Apply 진입 계약 |
| [`config.yaml`](config.yaml) | 프로젝트 context, naming과 OpenSpec 작성 규칙 |
| [`AGENTS.md`](AGENTS.md) | `openspec/`에서 작업하는 agent의 행동 규칙 |

세부 규칙은 해당 소유 파일을 직접 따른다. 하위 `README.md`와 `AGENTS.md`에는 해당 artifact에만 필요한 설명과 규칙만 둔다.
