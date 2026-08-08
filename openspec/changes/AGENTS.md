# OpenSpec Changes Agent Rules

`openspec/changes/`의 Change 작업에 추가로 적용한다.

- 하나의 Change는 하나의 검토 가능한 변경 목적을 가진다.
- 같은 목적의 active Change가 있으면 새 Change보다 기존 Change 갱신을 우선한다.
- 영향받는 Spec과 실제 변경 범위를 일치시킨다.
- archive 전 구현과 검증 근거, current Spec과의 일관성을 확인한다.
- 기존 archive는 이름 규칙 준수만을 위해 수정하지 않는다.
