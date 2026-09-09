# Actual Airflow DAGRun Proof Tasks (PR #229)

## 1. Workstream 1: Local Runtime Reconnaissance & Isolation Feasibility

- [ ] **1.1 스케줄러 DAGRun 실행 경로 확인**
  - Airflow 3.3.0 CLI 표면을 통해 `hmda_data_plane` DAGRun을 수동 트리거하고 terminal state(`success`/`failed`)까지 관찰할 수 있는 repository-native 명령 경로 확인
- [ ] **1.2 TaskInstance state 및 Asset event 증거 회수 표면 확인**
  - CLI, Python API 또는 metadata DB 조회를 통해 TaskInstance 상태 전이 및 Asset 이벤트 회수 가능성 검증
- [ ] **1.3 Disposable worktree 기반 dbt 격리 검증**
  - 임시 worktree 환경에서 `dbt/target` 및 DuckDB가 메인 작업 트리를 오염시키지 않고 격리 실행되는지 확인
- [ ] **1.4 픽스처(clean/dirty) 준비 경로 확인**
  - 실제 실행에 필요한 최소 데이터 픽스처가 기존 contract를 그대로 활용할 수 있는지 확인

## 2. Workstream 2: OpenSpec Planning Transition

- [ ] **2.1 Change 성격 분류 확정**
  - 정찰 결과 실제 런타임과 현행 스펙([openspec/specs/orchestration-pipeline/spec.md](../../../openspec/specs/orchestration-pipeline/spec.md))이 일치하면 proof/tooling change(`skip_specs`)로, 불일치 확인 시 behavior delta change로 범위 확정
- [ ] **2.2 OpenSpec Change 아티팩트 작성**
  - Proposal, Design, Tasks 작성 및 리뷰

## 3. Workstream 3: Verification & Integration

- [ ] **3.1 실제 Airflow DAGRun 증명 실행**
  - 정찰된 격리 절차를 바탕으로 DAGRun 증명 실행 및 아티팩트/로그 증거 확보
- [ ] **3.2 인박스 및 PR #229 갱신**
  - 실행 결과 보고서 작성 및 PR #229 설명/검증 상태 갱신
