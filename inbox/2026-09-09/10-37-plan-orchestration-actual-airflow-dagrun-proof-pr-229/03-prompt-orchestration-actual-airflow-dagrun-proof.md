---
type: prompt
title: "Actual Airflow DAGRun Proof Agent Handoff Prompt"
description: "[SUPERSEDED] 후속 구현 에이전트가 실제 Airflow DAGRun 검증 및 스크립트 구축 작업을 즉시 착수할 수 있도록 정찰 결과, 실행 제약, 시나리오 및 검증 절차를 전달하는 프롬프트."
tags:
  - orchestration
  - airflow
  - runtime-proof
  - agent-prompt
  - handoff
  - pr-229
---

# Actual Airflow DAGRun Proof Agent Handoff Prompt

> [!WARNING]
> 이 handoff prompt는 후속 실행 전 작성된 역사적 기록이며 현재 실행 지침으로 사용하지 않는다. `dags test`는 scheduler service 실행 증거가 아니고 결함 샘플의 실제 적재량은 19행이다. 자동·주기 실행과 scheduler-service proof는 현재 MVP 및 canonical spec의 완료 조건이 아니다. 현재 상태와 근거는 [실측 결과](04-report-orchestration-actual-airflow-dagrun-proof-result.md)와 [이슈·블로커 보고서](07-report-orchestration-pr-229-issues-blockers.md)를 따른다.

> [!NOTE]
> 본 문서는 GitHub Pull Request [#229](https://github.com/mols3131d/hmda-data-reliability/pull/229) (`test/actual-airflow-dagrun-proof`)의 후속 작업을 수행할 에이전트에게 전달하기 위한 실행 프롬프트입니다. 앞서 검증된 정찰 보고서([02-report-orchestration-actual-airflow-dagrun-reconnaissance.md](02-report-orchestration-actual-airflow-dagrun-reconnaissance.md))의 실측 결과와 핵심 제약사항을 바탕으로 작성되었습니다.

---

## Agent Prompt

다음 프롬프트 텍스트를 복사하여 후속 작업을 진행할 에이전트에게 입력으로 전달하십시오:

```markdown
당신은 GitHub Pull Request [#229](https://github.com/mols3131d/hmda-data-reliability/pull/229) (`test/actual-airflow-dagrun-proof` 브랜치)의 실제 Airflow DAGRun 동작 증명(Proof)을 구현하고 검증하는 시니어 데이터 엔지니어링 에이전트입니다.

### 1. 작업 목적과 범위
- **목적:** 실제 Apache Airflow 3.3.0 런타임 환경에서 `hmda_data_plane` DAG의 스케줄러 생성 DAGRun 라이프사이클, TaskInstance 상태 전이, Asset 이벤트 기록, 그리고 dbt 산출물 프로젝션이 [openspec/specs/orchestration-pipeline/spec.md](../../../openspec/specs/orchestration-pipeline/spec.md) 규격과 정확히 일치함을 실측 증거로 최종 입증합니다.
- **핵심 원칙:** 메인 저장소의 실데이터 DB(`data/hmda_reliability.duckdb`, 1,354만 건)와 dbt 빌드 산출물(`dbt/target/manifest.json`)을 1바이트도 오염시키지 않는 완전 격리 환경을 유지해야 합니다.
- **프로덕션 코드 수정 여부:** 프로덕션 DAG([src/hmda_reliability/orchestration/dags/hmda_data_plane.py](../../../src/hmda_reliability/orchestration/dags/hmda_data_plane.py))나 canonical spec은 수정하지 않습니다(정찰 결과 현행 스펙과 100% 일치 확인됨).

### 2. 선행 정찰에서 입증된 핵심 사실 (반드시 숙지)
1. **실행 명령:** 별도 상시 데몬(스케줄러/웹서버) 구동 없이 `airflow dags test hmda_data_plane -c '<JSON_CONF>'` 명령 하나로 스케줄러 기반 실제 DAGRun 및 TaskInstance를 즉시 동기식(Sync)으로 실행하고 완료할 수 있습니다.
2. **TaskInstance 상태 확인:** `airflow tasks states-for-dag-run hmda_data_plane "<RUN_ID>" -o json`으로 태스크 전이 상태를 JSON으로 추출할 수 있습니다.
3. **Asset Event 증거 회수:** CLI `airflow assets details`는 `last_asset_event: null`을 반환하므로, 아울렛 에셋 메타데이터(적재 건수, projection ID 등)는 격리된 `airflow.db`의 `asset_event` 테이블을 SQLite로 직접 쿼리하여 회수해야 합니다.
4. **격리 메커니즘:** 저장소 내부의 `.local/worktrees/<name>`에 disposable `git worktree`를 생성하여 실행하면 메인 작업 트리의 DB와 `dbt/target`이 완벽하게 보호됩니다(실측 mtime 불변 검증 완료).

### 3. 절대 위반하면 안 되는 3가지 제약사항 (Critical Guardrails)
1. **[저장소 내부 경로 사용]** 시스템 `/tmp`는 WSL tmpfs 용량 한계(약 235MB 잔여)로 인해 패키지 추출이나 DuckDB 정렬 시 디스크 풀/메모리 초과 오류가 발생합니다. 워크트리는 반드시 저장소 내 `.local/worktrees/<worktree-name>` 경로를 사용하십시오.
2. **[실데이터 사용 금지]** 메인 1,354만 건 실데이터를 전체 적재하면 메모리 한계로 실패합니다. 클린 통과 시나리오에는 정상 결측률(약 16%)을 준수한 **1,000행 픽스처**를 사용하고, 결함 차단 시나리오에는 20행 샘플(`data/samples/hmda/year_2025.csv`) 또는 synthetic 결함 생성기를 사용하십시오.
3. **[사후 정리 보장]** 테스트 실행 후 생성된 worktree는 `git worktree remove <path> --force`로 반드시 정리하여 메인 브랜치의 `git status`가 `clean` 상태를 유지하도록 하십시오.

### 4. 구현 및 검증 태스크
1. **실행 증명 스크립트 작성 (선택 또는 권장):**
   - 워크트리 생성 → Airflow 메타데이터 DB 초기화(`db migrate`, `dags reserialize`) → 픽스처 준비 → DAGRun 실행(`airflow dags test`) → 상태 및 Asset DB 증거 회수 → 워크트리 정리를 일괄 수행하는 자동화 스크립트([scripts/run_actual_source.py](../../../scripts/run_actual_source.py) 또는 전용 스크립트)를 구성하거나 순차 실행합니다.
2. **두 가지 필수 시나리오 증명:**
   - **시나리오 A (품질 게이트 실패 차단):** 이상 데이터 주입 → `load_raw_hmda_loans` (success) → `evaluate_quality_gate` (failed, `QualityGateError`) → `build_dbt_loan_analytics` (upstream_failed).
   - **시나리오 B (클린 파이프라인 전체 성공):** 1,000행 정상 픽스처 → `load_raw_hmda_loans` (success) → `evaluate_quality_gate` (success) → `build_dbt_loan_analytics` (success, dbt build 완료 및 manifest 프로젝션 생성).
3. **증거 수집 및 인박스 보고서 작성:**
   - 실행된 두 시나리오의 DAGRun ID, TaskInstance 상태 JSON, SQLite `asset_event` 쿼리 결과, 그리고 메인 트리의 무오염 증거(mtime 불변 로그)를 수집하여 `04-report-orchestration-actual-airflow-dagrun-proof-result.md`에 기록하십시오.
4. **인박스 태스크 및 PR #229 갱신:**
   - [tasks.md](tasks.md)의 Workstream 2/3 완료 체크 및 PR #229 설명 본문을 최종 결과로 업데이트하십시오.

### 5. 참고 아티팩트
- 계획서: [inbox/2026-09-09/10-37-plan-orchestration-actual-airflow-dagrun-proof-pr-229/README.md](README.md)
- 사전 기획 조사서: [inbox/2026-09-09/10-37-plan-orchestration-actual-airflow-dagrun-proof-pr-229/01-research-orchestration-actual-airflow-dagrun-planning.md](01-research-orchestration-actual-airflow-dagrun-planning.md)
- 정찰 보고서: [inbox/2026-09-09/10-37-plan-orchestration-actual-airflow-dagrun-proof-pr-229/02-report-orchestration-actual-airflow-dagrun-reconnaissance.md](02-report-orchestration-actual-airflow-dagrun-reconnaissance.md)
- 태스크 목록: [inbox/2026-09-09/10-37-plan-orchestration-actual-airflow-dagrun-proof-pr-229/tasks.md](tasks.md)
```
