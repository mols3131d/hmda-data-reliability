# OpenSpec Changes Agent Rules

`openspec/changes/`의 Change를 생성, 수정, archive할 때 적용한다.

## 먼저 확인

- [`README.md`](README.md): Change의 역할과 이름 규칙
- [`../config.yaml`](../config.yaml): OpenSpec 작성 규칙
- 영향받는 current Spec과 관련 기존 Change

## 작업 규칙

- 하나의 Change는 하나의 검토 가능한 변경 목적을 가진다.
- 이름은 `README.md`의 규칙을 따른다.
- 기존 active Change와 목적이 겹치면 새 Change보다 기존 Change 갱신을 우선 검토한다.
- 영향받는 Spec과 실제 변경 범위를 일치시킨다.
- 관련 없는 Change나 Spec은 수정하지 않는다.

## Archive

archive 전 구현과 검증 근거를 확인하고, current Spec과의 일관성을 검토한다.
