---
type: openspec-spec-driven-tdd-proposal
category: proposal
title: Investigate HMDA Ingestion
description: HMDA 적재 준비와 실행 결과를 읽기 전용으로 조사하고 운영자에게 근거 있는 다음 조치를 인계합니다.
---

## Why

HMDA 적재 담당자는 원천의 상태와 Airflow 실행 결과를 함께 확인해 다음 조치를 정해야 한다. 현재 적재기는 원천 검증·쓰기 결과를 제공한다. 신규 LangGraph 실행부와 Codex OAuth 우선 제공자 경계를 먼저 교체한 뒤, 그 기반에서 조사 범위를 고정하고 서로 다른 근거에 따라 필요한 조회와 후속 조치를 제안할 실행 흐름을 제공한다. [PR #291 런타임 선택](../../../inbox/github-291-build-ingestion-agent-harness/01-report-llmops-runtime-selection.md), [적재 조사 설계](../../../inbox/github-291-build-ingestion-agent-harness/02-proposal-ingestion-llmops/README.md)

## What Changes

- 운영자는 적재 전 준비 조사에서 입력 버전에 묶인 준비 상태, 확인 근거, 미확인 항목과 다음 조치를 받는다.
- 조사 중 해석이나 추가 근거가 필요하면 에이전트가 허용된 읽기 전용 조회 또는 근거 있는 권고를 선택한다.
- 운영자는 선택한 Airflow 실행의 단계 상태를 조회하고, 실제 입력의 범위와 버전이 확인되는 경우에 준비 조사와 대조한다.
- 조사 결과와 실패를 로컬에 기록하고, 저장된 입력과 조회·모델 응답을 이용해 판단을 오프라인에서 재현한다.
- 적재 조사는 기존 사고 조사 실행 루프와 별개로 구현하지 않고, 선행 Reliability AI 교체 Change에서 제공하는 LangGraph·제공자 계약을 사용한다.

## Boundaries

- **In Scope:** 로컬 HMDA CSV·Parquet 준비 조사, 운영자 인계, 지정된 `hmda_data_plane` 실행의 결과 조회, 로컬 기록·재현과 허용된 추적.
- **Out of Scope:** 사고 조사 실행부와 제공자 adapter 교체, 에이전트가 시작하는 적재·복구, 실제 적재 시점의 원천 버전 기록 확대, 프로세스 재시작 뒤 동일 조사 ID 재개, 사람 평가나 벤치마크 플랫폼 구축.

## Capabilities

### New Capabilities

#### `reliability-ai-ingestion-investigation`

- Reliability AI의 적재 전후 근거 조사와 운영자 인계를 정의한다. 기존 사고 리뷰는 [Reliability Agentic Review](../../specs/reliability-agentic-review/spec.md)의 입력·결과 계약을 따른다.

## Impact

- Reliability AI에 적재 조사 진입점과 로컬 근거 계약이 추가된다. 원천 확인은 [HMDA Data](../../specs/hmda-data-ingestion/spec.md), 실행 권한과 결과는 [Data Operations](../../specs/data-operations-stage-execution/spec.md) 및 [Airflow](../../specs/orchestration-pipeline/spec.md)의 기존 경계를 따른다.
- 이 Change는 같은 PR에서 선행 구현할 Reliability AI 실행부 교체 Change의 LangGraph·제공자 계약을 사용한다. 해당 계약과 Codex OAuth 로컬 검증이 준비되기 전에 적재 모델 호출을 구현하지 않는다.
- 이 흐름은 별도 호출로 제공하는 적재 조사 기능이다. [MVP](../../../docs/mvp.md)의 Agentic review 증명은 그 문서의 사고 검토 기준으로 판단한다.
