# OpenSpec Agent Rules

`openspec/` 아래 artifact를 생성, 수정, 리팩토링할 때 적용한다.

## 먼저 확인

- [`README.md`](README.md): 지침 소유권과 구조
- [`config.yaml`](config.yaml): Project Pivot 전용 OpenSpec 규칙
- 사용 중인 schema와 작업 대상의 `README.md`, `AGENTS.md`
- 관련 current Spec과 active Change

## 작업 규칙

- 지침은 `README.md`의 소유권에 맞는 파일 한 곳에 두고 다른 문서에서는 링크한다.
- 새 artifact를 만들기 전에 기존 artifact와 목적이나 책임이 겹치는지 확인한다.
- 요청 범위와 직접 관련된 artifact만 수정한다.
- rename, merge, split 시 의미와 영향받는 OpenSpec 참조를 함께 확인한다.
- 변경 후 중복 책임과 참조 일관성을 검토한다.

이 규칙은 OpenSpec workflow를 통하지 않는 `openspec/` 작업에도 적용한다.
