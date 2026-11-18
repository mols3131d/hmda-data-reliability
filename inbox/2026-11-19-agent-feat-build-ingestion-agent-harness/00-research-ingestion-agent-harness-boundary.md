---
type: research
title: "Ingestion Agent Harness Boundary"
description: "LangGraph 또는 Deep Agents 기반 HMDA 데이터 흡수 에이전트 MVP의 기존 실행 경계와 기술 선택 조건을 조사한다."
---

# Ingestion Agent Harness Boundary

> [!NOTE]
> 새 에이전트는 기존 Bronze loader나 Airflow를 대체하는 별도의 full-pipeline orchestrator가 아니라, 데이터 흡수 작업의 **source preflight → bounded investigation → actionable plan → controlled execution request → deterministic outcome evidence**를 다루는 별도 control-plane capability로 설계하는 것이 현재 계약과 가장 잘 맞는다. 구현 전 OpenSpec 및 MVP scope 정합성 결정이 필요하다.

## Question

LangGraph 또는 Deep Agents로 HMDA source ingestion 작업에 유용한 LLMOps harness를 구축할 때 어떤 기존 경계와 실행 증거를 재사용할 수 있는가?

## Scope

기준: `main` commit `35d099c748cbe08ae6a12ce60acd7574fe086719`. 실제 모델 품질 평가, 범용 multi-dataset ingestion, 클라우드 배포는 이 PR의 목표가 아니다.

## Findings

### Existing data-plane ownership

- [Ingestion Spec](../../openspec/specs/hmda-data-ingestion/spec.md): 원천 발견, 구조 검증, provenance, idempotent partition replacement 및 stale-state guard가 결정론적 계약이다.
- [Stage Execution Spec](../../openspec/specs/data-operations-stage-execution/spec.md): `DataOperationRequest`, `load_raw_data` 등 공개 stage API는 전체 파이프라인 순서를 소유하지 않는다.
- [Orchestration Spec](../../openspec/specs/orchestration-pipeline/spec.md): Airflow는 raw → quality gate → dbt의 유일한 data-plane workflow owner이고 LLMOps control-plane을 자동으로 실행하지 않는다.
- [Architecture](../../docs/ARCHITECTURE.md): agent 결과가 승인이나 원천 데이터 상태 변경 권한이 되지 않는다.
- [`pyproject.toml`](../../pyproject.toml): `langgraph>=1.2.10`은 이미 direct dependency다. `deepagents`는 현재 direct dependency가 아니다.

### Framework capabilities and fit

- [LangGraph Python overview](https://docs.langchain.com/oss/python/langgraph/overview): 명시적 state / node / transition, persistence, human-in-the-loop를 제공하여 bounded deterministic workflow와 접합하기 쉽다.
- [Deep Agents Python overview](https://docs.langchain.com/oss/python/deepagents/overview): LangChain·LangGraph 기반의 planning, task decomposition, context files, subagent delegation을 갖춘 상위 harness SDK다.
- 두 프레임워크의 결합은 가능하지만 필수가 아니다. MVP에 계획·하위 에이전트·파일 기반 컨텍스트가 실제 필요한지 검증하기 전 중복 orchestration을 만들지 않는다. LangSmith managed service는 요구사항이 아니다.

### Proposed first vertical slice

HMDA 입력 한 범위를 대상으로 source discovery와 제한적 구조·provenance 점검을 수행하고, 에이전트가 발견 사실과 불확실성을 구분한 실행 계획을 제안한다. 사람 또는 trusted caller가 실행 범위를 명시적으로 확정하면 기존 deterministic ingestion entrypoint를 별도로 호출하며, 결과를 실제 row count / source identity / 오류와 연계한다.

이 흐름에서 모호하거나 유효하지 않은 source는 실행을 차단·보류하고, 모델에 범용 shell·임의 SQL 쓰기·원격 network·직접 Bronze mutation 권한을 부여하지 않는다.

## Implications

- **Default candidate:** bounded state flow가 주된 요구라면 기존 LangGraph를 우선 검토한다. Multi-step planning과 subagent delegation의 고유 가치가 입증되면 self-hosted Deep Agents SDK를 선택한다.
- **Harness goals:** bounded tools, explicit state and step budgets, tool-call trace/provenance, checkpoint/replay, human escalation, fail-closed policy. 기존 `runtime_ai`와 Langfuse 경계는 실익에 따라 재사용한다.
- **Contract change:** 현재 [MVP](../../docs/mvp.md)는 incident advisory AI를 중점으로 한다. ingestion agent를 MVP acceptance에 포함하려면 canonical MVP 및 영향받는 OpenSpec contract의 명시적 정합화가 필요하다.

## Open Questions

- Deep Agents의 built-in planning/subagents가 첫 HMDA ingestion slice에 필요한가, 아니면 명시적 LangGraph state machine으로 충분한가?
- 모델이 생성한 계획을 어떤 immutable scope / expected-state와 바인딩하고, 승인·실행·결과를 어떻게 구별할 것인가?
- 재실행과 관측 artifact의 최소 저장 경계는 기존 run artifact 및 Langfuse와 어떻게 연결할 것인가?

이 보고서는 기술 선택의 근거이지 framework 최종 채택 결정이나 구현 완료 근거가 아니다.
