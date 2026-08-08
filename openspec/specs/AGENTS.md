# OpenSpec Specs Agent Rules

`openspec/specs/`의 Spec을 생성, 수정, 리팩토링할 때 적용한다.

## 먼저 확인

- [`README.md`](README.md): 역할과 이름 규칙
- [`../config.yaml`](../config.yaml): Spec 작성 규칙
- [`../../docs/domains/OVERVIEW.md`](../../docs/domains/OVERVIEW.md): domain 소유권
- 작업 대상과 관련된 기존 Spec

## 작업 규칙

- 하나의 Spec은 하나의 지속적인 capability와 하나의 owning domain을 가진다.
- 같은 capability가 이미 있으면 새 Spec보다 기존 Spec 갱신을 우선한다.
- 이름은 `README.md`, 내용은 `../config.yaml`을 따른다.
- 요청 범위 밖의 Spec은 수정하지 않는다.

## 리팩토링

rename, merge, split 시 기존 계약의 의미와 영향받는 OpenSpec 참조를 확인한다.
변경 후 이름, domain 소유권, 중복 책임, 참조 일관성을 검토한다.
