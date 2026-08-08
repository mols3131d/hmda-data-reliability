# OpenSpec Specs

`openspec/specs/`는 현재 canonical capability Spec을 저장한다.

## 이름 규칙

```text
<domain>[-<subdomain>]-<capability>[-<extensions>]
```

- domain을 첫 segment로 두어 관련 Spec이 함께 정렬되게 한다.
- subdomain은 분류에 필요할 때만 사용한다.
- capability만으로 충분하면 거기서 이름을 끝낸다.
- extensions는 추가 구분이 필요할 때만 사용한다.
- lowercase kebab-case를 사용한다.

예시:

```text
hmda-data-ingestion
data-platform-dbt
reliability-incident-detection
reliability-incident-detection-profile
```

Spec은 프로젝트 phase나 구현 작업이 아니라 지속적인 시스템 capability를 나타낸다. 여러 영역에 걸치면 결과 capability를 소유하는 domain에 배정한다.

Domain ownership은 [`docs/domains/OVERVIEW.md`](../../docs/domains/OVERVIEW.md), 공통 작성 규칙은 [`../config.yaml`](../config.yaml)을 따른다.
