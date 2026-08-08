# OpenSpec Agent Rules

`openspec/`의 Spec과 Change를 생성, 수정, 리팩토링할 때 적용한다.

## 먼저 확인

- [`README.md`](README.md): 구조와 이름 규칙
- [`config.yaml`](config.yaml): artifact 작성 규칙
- [`../docs/domains/OVERVIEW.md`](../docs/domains/OVERVIEW.md): domain ownership
- 작업 대상과 관련된 current Spec과 active Change

## 공통 규칙

- 결과를 소유하는 하나의 domain을 기준으로 분류한다.
- 새 artifact를 만들기 전에 기존 artifact와 목적이나 책임이 겹치는지 확인한다.
- 요청 범위와 직접 관련된 artifact만 수정한다.
- rename, merge, split 시 의미와 영향받는 OpenSpec 참조를 함께 확인한다.
- 변경 후 이름, domain ownership, 중복 책임, 참조 일관성을 검토한다.

Spec과 Change의 추가 규칙은 각 디렉토리의 `AGENTS.md`를 따른다.
