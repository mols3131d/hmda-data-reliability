---
type: report
title: "Actual Airflow DAGRun Reconnaissance and Isolation Report"
description: "[SUPERSEDED] Airflow 3.3.0 실제 DAGRun CLI 실행, TaskInstance 및 Asset Event 조회 표면, git worktree 기반 런타임/dbt 격리 타당성 정찰 결과."
tags:
  - orchestration
  - airflow
  - runtime-proof
  - reconnaissance
  - isolation
  - pr-229
---

# Actual Airflow DAGRun Reconnaissance and Isolation Report

> [!WARNING]
> 이 문서는 실행 전 정찰 기록이다. `dags test`를 scheduler service가 생성·관리한 실행으로 표현한 부분과 결함 샘플을 20행으로 표현한 부분은 후속 실측에서 정정됐다. 실제 두 실행은 `triggered_by=TEST`, `creating_job_id=null`, `scheduled_by_job_id=null`이었고 적재량은 19행이다. 현재 결론은 [실측 결과](04-report-orchestration-actual-airflow-dagrun-proof-result.md)와 [이슈·블로커 보고서](07-report-orchestration-pr-229-issues-blockers.md)를 따른다.

> [!NOTE]
> 본 보고서는 GitHub Pull Request [#229](https://github.com/mols3131d/hmda-data-reliability/pull/229)의 사전 기획에 따라, OpenSpec 계획 수립 전 실제 Airflow 3.3.0 CLI 실행 경로, TaskInstance 및 Asset 이벤트 증거 회수 방식, 그리고 `git worktree` 기반의 런타임/dbt 완전 격리 가능성을 로컬에서 직접 검증하고 기록한 정찰 결과입니다.

## Executive Summary

- **DAGRun 실행 경로:** 별도 데몬(스케줄러/웹서버) 상시 구동 없이 `airflow dags test <DAG_ID> -c '<JSON_CONF>'` 명령만으로 스케줄러 기반 실제 DAGRun 및 TaskInstance 라이프사이클을 온전히 실행하고 최종 상태(`success`/`failed`)를 관찰할 수 있음을 확인했습니다.
- **TaskInstance 상태 증거 회수:** `airflow tasks states-for-dag-run <DAG_ID> <RUN_ID> -o json`으로 개별 태스크의 상태 전이(`success`, `failed`, `upstream_failed`)를 CLI 표준 출력(JSON)으로 명확히 회수할 수 있습니다.
- **Asset Event 증거 회수:** CLI `airflow assets details`의 `last_asset_event`는 null로 반환되지만, 메타데이터 DB(`airflow.db`)의 `asset_event` 테이블에 `extra` 메타데이터(적재 건수, dbt projection ID 등)가 온전히 기록됨을 확인했습니다. 따라서 증거 회수 시 메타데이터 DB 쿼리가 가장 신뢰할 수 있는 경로입니다.
- **런타임 및 dbt 격리 타당성:** `.local/worktrees/<name>` 위치에 disposable `git worktree`를 생성하여 실행할 경우, 메인 저장소의 실데이터 DB(`data/hmda_reliability.duckdb`)와 dbt 타깃(`dbt/target/manifest.json`)이 전혀 오염되지 않고 완벽하게 독립 실행됨을 실측 타임스탬프로 입증했습니다. (주의: `/tmp`는 WSL tmpfs 용량 한계가 있으므로 워크스페이스 내부의 `.local` 경로 사용 필수)
- **픽스처 요구사항:** 전체 파이프라인(dbt 빌드 포함) 성공 시나리오 검증 시에는 2025년 기준 정상 결측률(약 16%) 및 필수 식별 컬럼을 갖춘 최소 1,000행 픽스처가 필요하며, 결함 차단 시나리오 검증 시에는 `data/samples/hmda/year_2025.csv` 또는 synthetic 결함 생성기로 충분합니다.

---

## 1. Local Runtime Reconnaissance Findings

### 1.1 Airflow 3.3.0 DAGRun Execution Surface

Airflow 3.3.0 환경에서 실제 DAGRun을 실행하기 위해 백그라운드 스케줄러나 웹서버를 띄울 필요 없이, 독립된 `AIRFLOW_HOME`에서 다음 표준 CLI 시퀀스로 재현 가능한 실행이 가능합니다:

```bash
export AIRFLOW_HOME="<ISOLATED_PATH>/.local/airflow"
export AIRFLOW__CORE__DAGS_FOLDER="<ISOLATED_PATH>/src/hmda_reliability/orchestration/dags"
export AIRFLOW__CORE__LOAD_EXAMPLES=false

# 메타데이터 DB 초기화 및 DAG 번들 직렬화
uv run airflow db migrate
uv run airflow dags reserialize

# 스케줄러 생성 DAGRun 격리 테스트 실행
uv run airflow dags test hmda_data_plane -c '{"database_path": "...", "source_root": "...", "source_year": 2025, "run_dbt_build": true}'
```

이 과정에서 Airflow SDK의 태스크 러너가 실제 컨텍스트를 주입하고, 태스크 간 의존성을 스케줄링하며, `run_type=manual`의 DAGRun과 TaskInstance를 생성함을 확인했습니다.

### 1.2 TaskInstance State Verification

실행 완료 후 생성된 `run_id`를 대상으로 다음 명령을 실행하여 모든 태스크의 최종 상태를 JSON으로 추출할 수 있습니다:

```bash
uv run airflow tasks states-for-dag-run hmda_data_plane "<RUN_ID>" -o json
```

실제 관찰된 전이 결과:

- **품질 게이트 실패 시:** `load_raw_hmda_loans` (success) → `evaluate_quality_gate` (failed) → `build_dbt_loan_analytics` (upstream_failed).
- **정상 파이프라인 통과 시:** `load_raw_hmda_loans` (success) → `evaluate_quality_gate` (success) → `build_dbt_loan_analytics` (success).

### 1.3 Asset Event Evidence Retrieval

`hmda_data_plane.py`는 아울렛 에셋(`RAW_HMDA_LOANS_ASSET`, `ANALYTICS_LOAN_ASSET`)에 실행 독립적 메타데이터를 `extra` 필드로 부착합니다.

- **CLI 표면 한계:** `airflow assets details --name "..." -o json` 명령은 `last_asset_event: null`을 반환하여 상세 이벤트 내용을 제공하지 못합니다.
- **메타데이터 DB 직접 조회:** 격리된 `airflow.db`의 `asset_event` 테이블에 다음과 같은 정밀 증거가 정상 적재됨을 검증했습니다:
  - `load_raw_hmda_loans`: `execution_stage: "raw_load"`, `database_path`, `hmda_loans_row_count` 등.
  - `build_dbt_loan_analytics`: `execution_stage: "analytics_build"`, `manifest_path`, `projection_id` 등.

---

## 2. Runtime and Artifact Isolation Feasibility

### 2.1 Isolation Risk Evaluation

기존 메인 작업 트리에서 `database_path` 파라미터만 분리하여 실행할 경우, `dbt build` 과정에서 생성되는 컴파일 산출물 및 매니페스트(`dbt/target/manifest.json`, `dbt/target/runs/current/*`)가 메인 저장소의 작업 상태를 덮어쓰게 됩니다.

### 2.2 Disposable Git Worktree Verification

저장소 내부의 `.local/worktrees/<name>`에 독립된 worktree를 생성하고 실행한 결과:

1. **dbt Artifact 격리:**
   - 메인 저장소 `dbt/target/manifest.json` 수정 시간(mtime): `1788848463` (실행 전후 동일, 0 bytes 변경).
   - Worktree 내부 `dbt/target/manifest.json` 수정 시간(mtime): `1788929696` (worktree 내부에만 최신 빌드 산출물 생성).
1. **DuckDB 파일 격리:**
   - worktree 전용 샌드박스 DB(`clean_sandbox.duckdb`)에만 데이터가 기록되었으며, 메인 `data/hmda_reliability.duckdb`는 무결하게 보존되었습니다.
1. **작업 트리 청결성:**
   - worktree 삭제(`git worktree remove --force`) 후 메인 브랜치의 git status는 완전히 `clean` 상태를 유지했습니다.

> [!WARNING]
> **WSL `/tmp` 용량 제약:**  
> 시스템 `/tmp`는 5.8GB 메모리 기반 tmpfs로 마운트되어 있으며 잔여 용량이 부족(약 235MB)하여 패키지 캐시 추출 및 DuckDB 정렬 시 `OutOfMemoryException` 또는 디스크 풀 오류가 발생할 수 있습니다. 따라서 disposable worktree는 반드시 루트 파일시스템에 위치한 저장소 내 `.local/worktrees/` 경로를 사용해야 합니다.

---

## 3. Data Fixture Requirements for Proof

1. **클린(Clean) 통과 시나리오:**
   - 2025년 기준 정상 결측률 허용 범위(약 16%)를 만족하고, dbt 모델(`stg_hmda_loans`, `int_loans`, `fct_loans`)이 요구하는 스키마 컬럼을 구비한 1,000행 규모의 CSV 픽스처가 필요합니다.
1. **결함 감지 및 게이트 차단 시나리오:**
   - 소규모 샘플(`data/samples/hmda/year_2025.csv`, 20행)은 `income` 결측률이 기준치와 달라 자연스럽게 `null_spike(income)` 이상으로 감지되어 다운스트림 차단을 즉시 입증할 수 있습니다.

---

## 4. Decision Gate Conclusion

사전 계획서([README.md](README.md))의 결정 기준(Decision Gates)에 따른 결론:

- **Existing runtime surface is sufficient:** Airflow CLI(`airflow dags test`, `tasks states-for-dag-run`)와 메타데이터 DB 쿼리만으로 스케줄러 기반 실행 및 증거 회수가 충분히 가능합니다.
- **No production behavior violation:** 현행 `openspec/specs/orchestration-pipeline/spec.md`에 정의된 스테이지 순서, 퀄리티 게이트 실패 시 차단, 성공 시 dbt 승격 동작이 실제 Airflow 런타임에서도 100% 일치하게 동작함을 확인했습니다.
- **OpenSpec Change 권고:** 프로덕션 오케스트레이션 계약의 변경이 없으므로, 향후 반복 가능한 증명 스크립트/테스트 하네스를 영구 구축할 경우에만 `skip_specs: true` 형태의 Tooling Change로 진행하거나, 일회성 검증 보고서 아티팩트로 완료할 수 있습니다.
