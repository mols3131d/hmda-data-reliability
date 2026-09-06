---
type: openspec-spec-driven-tdd-proposal
category: proposal
title: Orchestration Quality Gate
description: Airflow data-plane DAG에 신뢰성 품질 게이트 태스크를 추가해, 이상 데이터 적재 후 즉시 파이프라인 실패를 유발한다.
tags:
  - "domain:orchestration"
  - "capability:orchestration-pipeline"
---

## Why

현재 Airflow `hmda_data_plane` DAG은 Bronze 적재와 dbt 빌드만 수행한다. 이상이 있는 데이터(예: `income` Null 급증)가 적재되어도 파이프라인이 정상 완료되며, 이상 탐지는 별도 스크립트를 수동으로 실행해야만 확인할 수 있다.

데이터 신뢰성 이상을 운영 관점에서 가시화하려면, 적재 직후 신뢰성 게이트를 Airflow 태스크로 연결해 이상 발견 시 파이프라인 자체를 실패 상태로 전환해야 한다.

## What Changes

- `hmda_data_plane` DAG에 `evaluate_quality_gate` 태스크를 추가한다.
- `load_raw_hmda_loans` 성공 후, `build_dbt_loan_analytics` 실행 전에 실행된다.
- Data Operations는 dbt source가 소비할 전체 Bronze 파티션의 프로파일 스냅샷을 구성하고 Reliability public boundary에 평가를 위임한다.
- Reliability는 baseline, threshold, 활성 detector와 blocking 판정을 소유한다.
- 이상이 탐지되면 태스크를 명시적으로 실패시켜 다운스트림 analytics 빌드를 차단한다.
- 이상이 없으면 태스크가 정상 완료되어 analytics 빌드로 진행한다.
- Analytics build는 database mutation lock 안에서 전체 Bronze gate를 다시 평가한 뒤 같은 lock을 유지한 채 dbt subprocess를 시작한다.
- durable architecture와 domain guide를 raw load → quality gate → analytics build 실행 계약으로 동기화한다.

## Boundaries

- **In Scope:** DAG thin-adapter 태스크 추가, Reliability-owned quality policy, 전체 Bronze partition 평가, build 직전 lock-bound revalidation, Data Operations application composition, 이상 탐지 시 `AirflowException` 발생, 3-stage architecture 문서 동기화
- **Out of Scope:** baseline 저장소 구현, 외부 알림(Slack, Email), Airflow Alert, 복구 자동화, baseline 동적 관리

## Capabilities

### Modified Capabilities

#### `orchestration-pipeline`

- Data-plane workflow는 raw load → **quality gate** → analytics build 순서로 실행되어야 한다.
- quality gate 태스크는 탐지된 인시던트가 있을 때 실패해야 한다.
- quality gate 태스크는 탐지된 인시던트가 없을 때 정상 완료해야 한다.

## Impact

- `src/hmda_reliability/orchestration/dags/hmda_data_plane.py`: `evaluate_quality_gate` 태스크 추가
- `src/hmda_reliability/reliability/`: baseline, threshold, detector와 blocking policy 소유
- `src/hmda_reliability/data_operations/`: 전체 Bronze partition profile과 Reliability gate 호출을 조합하고 lock-bound quality-gated dbt build 제공
- `openspec/specs/orchestration-pipeline/spec.md`: quality gate requirement 추가
- `docs/ARCHITECTURE.md`, `docs/domains/orchestration.md`: 3-stage data-plane contract 반영
- `tests/orchestration/`: 품질 게이트 통합 테스트 추가
