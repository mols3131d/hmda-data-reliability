---
type: proposal
title: LLMOps for HMDA Ingestion
description: PR 291에서 구현할 읽기 전용 적재 조사, 기존 실행 경로와의 인계, 검증 순서를 정의합니다.
tags:
  - llmops
  - ingestion
  - hmda-data
---

# LLMOps for HMDA Ingestion

**PR #291은 기존 Reliability AI의 Python 조사 루프와 단일 모델 연결을 LangGraph 중심 실행부로 교체한 뒤, 같은 기반에 HMDA 적재 조사를 연결한다.** 첫 제공자 검증은 ChatGPT 구독 OAuth를 사용하는 Codex를 우선하며 Ollama도 선택 가능하게 설계한다. 적재 조사는 준비 근거를 고정하고 운영자에게 기존 Airflow 실행을 인계한 뒤 지정 실행 결과를 조회한다. [런타임 선택](../01-report-llmops-runtime-selection.md), [Codex 제공자 설계](../04-design-runtime-ai-codex-oauth-provider.md)

## Design Documents

| 문서 | 구현 전에 확정한 내용 |
| --- | --- |
| [아키텍처와 적용 계획](architecture-plan.md) | 로컬 조사 진입점, LangGraph 분기, Airflow 연결, 중단과 재현 |
| [판단·도구 계약](decision-contract.md) | 모델 호출 조건, 허용되는 다음 행동, 준비 판정과 인계 형식 |
| [근거 스키마와 검증](evidence-tool-schemas.md) | 원천 버전 고정, 필수 검사, 실제 실행 결과의 출처, 계약 테스트 |

설계 기준은 [직전 검토의 F1–F4](../03-review-ingestion-llmops-design.md#findings)다. LangGraph가 조사 상태·분기·도구 집행·종료를 관리하고 LangChain Core가 모델 제안의 공통 입력·출력 계약을 연결한다. Codex App Server와 Ollama는 같은 제공자 계약에 맞춰 별도 adapter로 접속한다. [런타임 선택 근거](../01-report-llmops-runtime-selection.md)

## Delivery Order

1. **공통 실행부를 먼저 교체한다.** 기존 사고 조사 진입점이 새 LangGraph와 provider contract를 사용하게 한다. Codex 구독 OAuth와 Ollama를 같은 조사 입출력 계약에서 확인한다.
1. **적재 준비 근거를 고정한다.** 동일한 적재 요청과 원천 스냅샷으로 검사를 실행하고, 어느 범위까지 확인했는지 결과에 남긴다.
1. **모델이 고르는 조회를 검증한다.** 서로 다른 근거를 받았을 때 조회 대상이나 다음 조치가 달라지는지 확인한다. 규칙으로 판정과 다음 조치가 확정되면 즉시 반환한다.
1. **운영자에게 인계하고 결과를 읽는다.** 준비 판정과 근거를 반환하고, 별도로 실행한 DAG 단계 상태를 조회한다. 입력 일치를 증명할 수 있는 경우에만 사전 관찰과 결과를 대조한다.
1. **실패를 재현한다.** 보존된 근거로 규칙과 판정을 오프라인에서 다시 실행한다. 구현 범위와 결과 계약은 관련 OpenSpec과 사용 가이드에 반영한다.

첫 구현의 확인 기준은 fake provider와 실제 로컬 조회로 위 흐름을 재현하고 기존 적재·Airflow의 회귀를 검증하는 것이다. Codex OAuth를 사용하는 로컬 실행과 Langfuse 원격 조회는 각 결과를 확인한 뒤 별도 근거로 기록한다. [검증 항목](evidence-tool-schemas.md#contract-tests)

## How to Decide

운영에서 활용 범위를 넓힐 때는 같은 입력에서 규칙만 사용한 결과, 한 번 설명한 결과, 읽기 전용 조사 결과를 비교한다. 사전에 정한 기준으로 담당자의 다음 조치 정확도·소요 시간·수동 재조회와 모델 지연·비용을 확인한다. 검증된 효용과 복구 근거가 축적된 업무부터 위임 범위를 넓힌다. [프로젝트의 위임 원칙](../../../docs/VISION.md#delegation-boundary)
