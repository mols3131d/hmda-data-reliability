# OpenSpec

`openspec/`는 프로젝트의 canonical Spec과 이를 변경하는 Change를 관리한다.

## 구조

| 경로 | 역할 |
| --- | --- |
| [`specs/`](specs/) | 지속적인 시스템 capability의 current Spec |
| [`changes/`](changes/) | 검토 가능한 변경과 완료된 archive |
| [`config.yaml`](config.yaml) | OpenSpec schema, 이름, artifact 작성 계약 |
| [`AGENTS.md`](AGENTS.md) | `openspec/`에서 작업하는 agent 규칙 |

OpenSpec artifact의 이름과 작성 규칙은 [`config.yaml`](config.yaml)을 따른다.
Spec과 Change의 역할은 각 디렉토리의 `README.md`를 참고한다.
