# OpenSpec Specs

`openspec/specs/`는 현재 시스템의 canonical capability Spec을 저장한다.

## 이름 규칙

Spec ID는 다음 형식을 사용한다.

```text
<domain>[-<subdomain>]-<capability>[-<extensions>]
```

- 첫 segment는 capability를 소유하는 domain으로 한다.
- subdomain과 extensions는 분류나 구분에 필요할 때만 사용한다.
- 가능한 한 `domain-capability` 수준에서 이름을 끝낸다.
- lowercase kebab-case를 사용한다.

예시:

```text
hmda-data-ingestion
data-platform-dbt
reliability-incident-detection
reliability-incident-detection-profile
orchestration-pipeline
```

## 범위

Spec은 프로젝트 phase, 구현 작업, 임시 change가 아니라 지속적인 시스템 capability를 나타낸다.

Requirement에는 관찰하고 검증할 수 있는 시스템 동작과 data contract를 작성한다. 구현 세부사항은 design artifact, source code, test 또는 해당 project documentation에서 다룬다.

## 소유권

Domain boundary는 [`docs/domains/OVERVIEW.md`](../../docs/domains/OVERVIEW.md)를 따른다. 여러 영역에 걸친 Spec은 결과 capability를 소유하는 하나의 domain에 배정한다.
