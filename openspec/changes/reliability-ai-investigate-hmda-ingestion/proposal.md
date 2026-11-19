---
type: openspec-spec-driven-tdd-proposal
category: proposal
title: Investigate HMDA Ingestion
description: HMDA 적재 준비와 실행 결과를 읽기 전용으로 조사하고 운영자에게 근거 있는 다음 조치를 인계합니다.
---

## Why

HMDA 적재 담당자는 원천의 상태와 Airflow 실행 결과를 함께 확인해 다음 조치를 정해야 한다. 입력 버전으로 조사 범위를 고정하고, 근거에 따라 필요한 조회나 다음 조치를 인계하는 기능을 제공한다. [적재 조사 설계](../../../inbox/github-291-build-ingestion-agent-harness/02-proposal-ingestion-llmops/README.md)

## What Changes

- 운영자는 적재 전 준비 조사에서 입력 버전에 묶인 준비 상태, 확인 근거, 미확인 항목과 다음 조치를 받는다.
- 조사 중 해석이나 추가 근거가 필요하면 에이전트가 허용된 읽기 전용 조회 또는 근거 있는 권고를 선택한다.
- 운영자는 선택한 Airflow 실행의 단계 상태를 조회하고, 실제 입력의 범위와 버전이 확인되는 경우에 준비 조사와 대조한다.
- 조사 결과와 실패를 로컬에 기록하고, 저장된 입력과 조회·모델 응답을 이용해 판단을 오프라인에서 재현한다.

## Boundaries

- **In Scope:** 로컬 HMDA CSV·Parquet 준비 조사, 운영자 인계, 지정된 `hmda_data_plane` 실행의 결과 조회, 로컬 기록·재현과 허용된 추적.
- **Out of Scope:** 사고 조사 실행부와 제공자 adapter 교체, 에이전트가 시작하는 적재·복구, 실제 적재 시점의 원천 버전 기록 확대, 프로세스 재시작 뒤 동일 조사 ID 재개, 사람 평가나 벤치마크 플랫폼 구축.

## Capabilities

### New Capabilities

#### `reliability-ai-ingestion-investigation`

- Reliability AI의 적재 전후 근거 조사와 운영자 인계를 정의한다. 기존 사고 리뷰는 [Reliability Agentic Review](../../specs/reliability-agentic-review/spec.md)의 입력·결과 계약을 따른다.

## Impact

- Reliability AI에 적재 조사 진입점과 로컬 근거 계약이 추가된다. 원천 확인은 [HMDA Data](../../specs/hmda-data-ingestion/spec.md), 실행 권한과 결과는 [Data Operations](../../specs/data-operations-stage-execution/spec.md) 및 [Airflow](../../specs/orchestration-pipeline/spec.md)의 기존 경계를 따른다.
- 적재 조사는 사고 조사 실행부 교체에서 제공하는 조사·모델 연결·기록 계약을 사용한다. Codex의 ChatGPT 구독 OAuth 연동과 최초 실실행 검증은 선행 Change가 소유한다. [사고 조사 실행부 교체](../reliability-ai-replace-investigation-runtime/proposal.md)
- 이 흐름은 별도 호출로 제공하는 적재 조사 기능이다. [MVP](../../../docs/mvp.md)의 Agentic review 증명은 그 문서의 사고 검토 기준으로 판단한다.
