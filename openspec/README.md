# OpenSpec

`openspec/`는 프로젝트의 canonical Spec과 이를 변경하는 Change를 관리한다.

## 구조

| 경로 | 역할 |
| --- | --- |
| [`specs/`](specs/) | 지속적인 시스템 capability의 current Spec |
| [`changes/`](changes/) | 검토 가능한 변경과 완료된 archive |
| [`config.yaml`](config.yaml) | OpenSpec schema와 artifact 작성 규칙 |

## 이름 규칙

모든 ID는 owning domain부터 시작하고 lowercase kebab-case를 사용한다.

| Artifact | 형식 |
| --- | --- |
| Spec | `<domain>[-<subdomain>]-<capability>[-<extensions>]` |
| Change | `<domain>[-<subdomain>][-<capability>]-<short-title>[-<extensions>]` |

- subdomain과 extensions는 분류나 구분에 필요할 때만 사용한다.
- 동급인 여러 domain을 하나의 이름에 나열하지 않는다.
- domain ownership은 [`docs/domains/OVERVIEW.md`](../docs/domains/OVERVIEW.md)를 따른다.

Spec과 Change의 세부 의미는 각 디렉토리의 `README.md`를 따른다.
