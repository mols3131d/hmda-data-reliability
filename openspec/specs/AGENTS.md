# OpenSpec Specs Agent Rules

`openspec/specs/` 아래의 Spec을 생성, 수정, 리팩토링할 때 적용한다.

## 먼저 확인

- [`README.md`](README.md): Spec의 역할과 이름 규칙
- [`../config.yaml`](../config.yaml): OpenSpec 작성 규칙
- [`../../docs/domains/OVERVIEW.md`](../../docs/domains/OVERVIEW.md): domain 소유권
- 작업 대상과 관련된 기존 Spec

## 작업 규칙

- 하나의 Spec은 하나의 지속적인 capability와 하나의 owning domain을 가진다.
- 새 Spec을 만들기 전에 기존 Spec과 책임이 겹치는지 확인한다. 같은 capability라면 새로 만들기보다 기존 Spec을 우선 갱신한다.
- Requirement에는 관찰하고 검증할 수 있는 시스템 동작과 data contract만 둔다.
- 구현 세부사항은 Spec에 넣지 않는다.
- 이름은 `README.md`의 규칙을 따른다. subdomain과 extensions는 필요할 때만 사용한다.
- 기존의 비표준 이름은 요청 범위에 포함될 때만 정리한다.
- 관련 없는 Spec은 수정하지 않는다.

## 리팩토링

rename, merge, split 시 기존 계약의 의미를 보존하고 영향받는 OpenSpec 참조를 함께 확인한다.

변경 후에는 이름, domain 소유권, 중복 책임, 참조 일관성을 검토한다.
