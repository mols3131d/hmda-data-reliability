# Actual Airflow DAGRun Proof Tasks (PR #229)

## 1. Workstream 1: Local Runtime Reconnaissance & Isolation Feasibility

- [x] **1.1 스케줄러 DAGRun 실행 경로 확인**
  - Airflow 3.3.0 CLI 표면을 통해 `hmda_data_plane` DAGRun을 수동 트리거하고 terminal state(`success`/`failed`)까지 관찰할 수 있는 repository-native 명령 경로 확인
  - `airflow dags test hmda_data_plane -c '...'`로 성공 및 실패 라이프사이클 관찰 완료
- [x] **1.2 TaskInstance state 및 Asset event 증거 회수 표면 확인**
  - CLI(`tasks states-for-dag-run`), Python API 또는 metadata DB(`asset_event` 테이블) 조회를 통해 TaskInstance 상태 전이 및 Asset 이벤트 회수 가능성 검증 완료
- [x] **1.3 Disposable worktree 기반 dbt 격리 검증**
  - `.local/worktrees/` 환경에서 `dbt/target` 및 DuckDB가 메인 작업 트리를 오염시키지 않고 격리 실행되는지 실측 mtime 비교로 입증 완료
- [x] **1.4 픽스처(clean/dirty) 준비 경로 확인**
  - 클린(1,000행 정상 결측률) 및 결함 감지(샘플 20행) 픽스처 동작 확인 완료
- [x] **1.5 정찰 보고서 작성**
  - 정찰 결과 보고서([02-report-orchestration-actual-airflow-dagrun-reconnaissance.md](02-report-orchestration-actual-airflow-dagrun-reconnaissance.md)) 작성 완료
- [x] **1.6 후속 작업 에이전트 전달 프롬프트 작성**
  - 실행 프롬프트 아티팩트([03-prompt-orchestration-actual-airflow-dagrun-proof.md](03-prompt-orchestration-actual-airflow-dagrun-proof.md)) 작성 완료

## 2. Workstream 2: OpenSpec Planning Transition

- [ ] **2.1 Change 성격 분류 확정**
  - 정찰 결과 실제 런타임과 현행 스펙([openspec/specs/orchestration-pipeline/spec.md](../../../openspec/specs/orchestration-pipeline/spec.md))이 일치하므로, 영구 툴링/하네스 도입 시 `skip_specs: true` 적용 여부 확정
- [ ] **2.2 OpenSpec Change 아티팩트 작성 (필요 시)**
  - Proposal, Design, Tasks 작성 및 리뷰

## 3. Workstream 3: Verification & Integration

- [ ] **3.1 실제 Airflow DAGRun 증명 실행 및 증거 확보**
  - 정찰된 격리 절차를 바탕으로 최종 증명 실행 및 아티팩트/로그 증거 확정
- [ ] **3.2 인박스 및 PR #229 갱신**
  - 실행 결과 반영 및 PR #229 설명/검증 상태 갱신
