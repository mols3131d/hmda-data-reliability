# OpenSpec Changes

`openspec/changes/`는 진행 중인 OpenSpec Change와 완료된 archive를 저장한다.

Change는 proposal, specs, design, tasks와 intended delta를 다루는 **비권위 작업 artifact**다. Current capability의 canonical contract는 [`../specs/`](../specs/)가 소유하며, Change가 존재하거나 완료됐다는 사실만으로 Spec이 바뀌지 않는다.

Review feedback은 별도 canonical artifact가 아니라 원인을 소유하는 planning artifact 또는 implementation work로 route한다.

구현·검증된 durable contract는 OpenSpec workflow에 따라 `specs/**`에 반영하고, 완료된 Change는 필요에 따라 archive한다. Archive된 Change도 historical work evidence이지 current contract가 아니다.

이름과 repository-specific 작성 규칙은 [`../config.yaml`](../config.yaml)을 따른다.
