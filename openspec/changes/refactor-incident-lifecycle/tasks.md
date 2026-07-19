## 1. 변경 준비

- [ ] 1.1 완료된 `remove-pipeline-cli` change를 archive하고 main specs가 동기화됐는지 확인한다.
- [ ] 1.2 실제 current, 다중 detection, 무사고, baseline 불일치, 무부작용 lifecycle 테스트를 추가한다.

## 2. Lifecycle 단계 축소

- [ ] 2.1 `run_incident_lifecycle(request, baseline)`이 DB current profile을 측정하고 호환성을 검증하도록 변경한다.
- [ ] 2.2 모든 detection의 impact와 remediation을 처리하고 순서 보존·중복 제거된 요약을 반환한다.
- [ ] 2.3 합성 current, 자체 approval, backfill, evaluation report 실행과 관련 import/helper를 제거한다.
- [ ] 2.4 `LifecycleResult`에서 evaluation·recovery 필드를 제거하고 호출부·테스트를 새 계약에 맞춘다.
- [ ] 2.5 `DataOperationRequest`에서 `simulate_row_count_ratio`, `run_backfill`, `report_path`를 제거한다.

## 3. Dagster graph 축소

- [ ] 3.1 `DataOperationsResource`에서 삭제된 lifecycle 설정을 제거한다.
- [ ] 3.2 `incident_lifecycle` asset을 제거하고 `pipeline_job`을 raw와 dbt asset만 포함하도록 변경한다.
- [ ] 3.3 Dagster definitions, asset 순서, metadata materialization 테스트를 두 asset 계약에 맞춘다.

## 4. 문서와 검증

- [ ] 4.1 README, architecture, private lifecycle guide를 caller-supplied baseline과 분리된 recovery/evaluation 경계에 맞춘다.
- [ ] 4.2 lifecycle·orchestration·reliability 테스트와 전체 pytest를 실행한다.
- [ ] 4.3 Ruff, mypy, OpenSpec 검증을 실행하고 제거된 설정·asset·결과 필드 참조가 없는지 확인한다.
