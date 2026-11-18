---
type: brief
title: "Ingestion Agent Harness Implementation Handoff"
description: "PR #291의 LangGraph 또는 Deep Agents 기반 ingestion harness를 로컬 작업자가 구현하기 위한 현재 상태와 첫 결정 지점을 전달한다."
---

# Ingestion Agent Harness Implementation Handoff

> [!IMPORTANT]
> **PR #291은 Draft이며 설계·구현·검증 전이다.** 목표는 실제 **ingestion agent harness MVP 구현**이다. LLM 품질 점수화로 범위를 전환하거나 도구 도입만으로 완료 처리하지 않는다.

## Continuation

- Owning PR: [#291](https://github.com/mols3131d/hmda-data-reliability/pull/291)
- Owning branch: `agent/feat/build-ingestion-agent-harness`
- Initial base: `main@35d099c748cbe08ae6a12ce60acd7574fe086719`. 재개 시 main/head와 변경 소유권을 재확인한다.
- Starting context: [Research](00-research-ingestion-agent-harness-boundary.md), [Plan](01-plan-ingestion-agent-harness-mvp.md).
- Known constraint: `pyproject.toml`에 `langgraph`가 이미 있고 `deepagents`는 아직 없다. `orchestration-pipeline` Spec은 Airflow의 data-plane ownership을 고정한다.

## First Decisions

1. 현재 OpenSpec active Change와 [MVP](../../docs/mvp.md)를 확인한다. 기존 review 중심 MVP에 ingestion agent를 추가하는 사용자 요구를 **명시적으로 정본화**하되 기존 data-plane/recovery의 권한 경계는 유지한다.
2. 첫 vertical slice의 tool contract와 안전한 실행 진입점을 결정한다. **LangGraph 단독 vs Deep Agents SDK**를 필요한 planning/delegation 수준, dependency, provider adapter, failure recovery 기준으로 실제 평가하여 선택한다.
3. Agent의 output은 typed plan과 evidence에 한정하고, trusted caller의 approval 및 target expected-state 검증이 충분히 강한지 확인한다. 안전한 atomic guard가 없다면 승인 없는 실행을 도입하지 않는다.

## Next Action

- Re-read current branch/main and applicable local/repository harness. 같은 목표의 existing implementation/active OpenSpec을 먼저 재사용한다.
- Contract / bounded state / tools / approval / trace design을 먼저 닫은 뒤 구현한다.
- Source preflight, denied/stale/invalid cases, accepted execution 및 repeatability를 offline tests + isolated DuckDB에서 검증한다.
- 실제 실행 증거와 구현 검증 상태를 PR description에 갱신한다. 강한 리뷰/반례는 직접 확인하고 타당한 것만 수용한다.
- Review readiness는 증거 기반으로 판단하며, **Ready 전환·merge·권한 확대는 인간의 별도 결정**이다.

## Boundaries

- 다른 PR [#290](https://github.com/mols3131d/hmda-data-reliability/pull/290)은 pytest marker 정확성만 소유한다. 변경을 혼합하지 않는다.
- `mols3131d` / `mols3131d@gmail.com` 외 계정·명의를 사용하지 않는다.
- Live model/remote service 호출과 credentials 사용은 명시적으로 준비된 환경과 권한을 확인한다. 테스트를 통과했다고 외부 Langfuse trace 성공을 주장하지 않는다.
- 현재 PR의 첫 커밋은 문서만 포함하며 실제 harness 실행/테스트 근거는 없다.
