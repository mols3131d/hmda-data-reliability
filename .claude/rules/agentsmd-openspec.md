---
paths:
  - openspec/**/*
---

# OpenSpec Agent Rules

`openspec/` 아래 artifact를 생성, 수정, 리팩토링할 때 적용한다. 이 파일은 **`openspec/**` 공통 agent 행동 규칙**을 소유하며, 하위 `AGENTS.md`는 해당 subtree에만 필요한 추가 규칙을 소유한다. Workflow/schema/project-specific rule ownership은 [`README.md`](README.md)의 지침 소유권 map을 따른다.

## 먼저 확인

- [`README.md`](README.md)의 canonical boundary와 지침 소유권
- 작업 대상의 `README.md`와 `AGENTS.md`
- Spec 또는 Change 작업: [`config.yaml`](config.yaml), 선택된 schema, 관련 current Spec과 필요한 Change artifact
- schema 작업: 해당 schema의 `README.md`와 필요한 `docs/`; project config를 schema 요구사항으로 사용하지 않는다.

## Canonical Boundary

- `specs/**`만 current capability의 canonical OpenSpec contract다.
- `changes/**`는 작업 계획과 변경 기록이다. Proposal, design, tasks와 review는 intended delta를 설명하지만 current Spec을 직접 override하지 않는다.
- Change 내용을 current system fact로 재사용해야 할 때는 먼저 대응 `specs/**`, source/tests와 현재 revision evidence를 확인한다.
- 구현·검증된 durable contract는 OpenSpec workflow에 따라 `specs/**`에 반영한다. 그 전까지 Change의 내용은 planned or in-flight delta로 취급한다.
- Archive된 Change는 historical evidence이며 canonical current contract가 아니다.

## 작업 규칙

- 활성 지침은 `README.md`의 소유권에 맞는 파일 한 곳에서만 관리한다.
- 새 artifact를 만들기 전에 기존 artifact와 목적이나 책임이 겹치는지 확인한다.
- 요청 범위와 직접 관련된 artifact만 수정한다.
- rename, merge, split 시 의미와 영향받는 OpenSpec 참조를 함께 확인한다.
- 변경 후 중복 책임, Spec/Change 경계와 참조 일관성을 검토한다.

이 규칙은 OpenSpec workflow를 통하지 않는 `openspec/` 작업에도 적용한다.
