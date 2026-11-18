---
type: brief
title: "Ingestion Agent Harness Implementation Handoff"
description: "PR #291의 LangGraph 또는 Deep Agents 기반 ingestion harness를 로컬 작업자가 구현하기 위한 현재 상태와 첫 결정 지점을 전달한다."
---

# Ingestion Agent Harness Implementation Handoff

> [!IMPORTANT]
> **PR #291은 Draft이며 설계·구현·검증 전이다.** 개발자의 명시적 목적은 **LangChain 생태계 기반 LangGraph 또는 Deep Agents로 LLMOps harness를 구축하고, MVP에서 데이터 흡수 단계의 에이전트 작업을 실제로 설계·구현하는 것**이다. LLM 품질 점수화, 단순한 도구 추가, deterministic 검사 결과의 요약으로 목표를 대체하지 않는다.

## Continuation

- Owning PR: [#291](https://github.com/mols3131d/hmda-data-reliability/pull/291)
- Owning branch: `agent/feat/build-ingestion-agent-harness`
- Initial base: `main@35d099c748cbe08ae6a12ce60acd7574fe086719`. 재개 시 main/head와 변경 소유권을 재확인한다.
- Starting context: [Research](00-research-ingestion-agent-harness-boundary.md), [Plan](01-plan-ingestion-agent-harness-mvp.md).
- Known constraint: `pyproject.toml`에 `langgraph`가 이미 있고 `deepagents`는 아직 없다. `orchestration-pipeline` Spec은 Airflow의 data-plane ownership을 고정한다.

## First Decisions

1. 현재 OpenSpec active Change와 [MVP](../../docs/mvp.md)를 확인한다. 기존 review 중심 MVP에 ingestion agent를 추가하는 사용자 요구를 **명시적으로 정본화**하되 기존 data-plane/recovery의 권한 경계는 유지한다.
2. **에이전트가 실제로 수행할 ingest 업무**와 비결정론적 선택이 필요한 지점을 확인한다. Source investigation / task planning / delegated tool execution 중 최소 유용한 범위를 정한 다음 **LangGraph 단독 vs Deep Agents SDK**의 장단점과 기존 provider·observability 연동을 평가해 선택한다.
3. AI output이 authorization이 되지 않도록 기존 Data Operations·Airflow의 실행 경계를 확인한다. 새 human approval 단계를 기본으로 만들지 않는다. 실제 agent-mediated write가 필요한 경우에만 trusted caller의 permission과 atomic guard를 증명하고, 안전하지 않으면 read-only planning/handoff로 제한한다.

## Next Action

- Re-read current branch/main and applicable local/repository harness. 같은 목표의 existing implementation/active OpenSpec을 먼저 재사용한다.
- 기존 구현으로 해결되지 않는 **에이전트 고유의 판단·위임 작업**을 먼저 확인하고, 필요한 수준의 state / allowed tools / execution permission / tracing을 설계한 뒤 구현한다. 체크포인트, 서브에이전트, 복잡한 replay는 필요성을 입증하지 못하면 추가하지 않는다.
- Source preflight뿐 아니라 증거별 tool choice·task branch, 실패/한도, 권한 거부와 기존 ingestion boundary 통합을 offline tests로 검증한다. 실제 mutation을 포함한 경우에만 isolated DuckDB의 stale/idempotency proof를 요구한다.
- 실제 실행 증거와 구현 검증 상태를 PR description에 갱신한다. 강한 리뷰/반례는 직접 확인하고 타당한 것만 수용한다.
- Review readiness는 증거 기반으로 판단하며, **Ready 전환·merge·권한 확대는 인간의 별도 결정**이다.

## Boundaries

- 다른 PR [#290](https://github.com/mols3131d/hmda-data-reliability/pull/290)은 pytest marker 정확성만 소유한다. 구현 우선순위는 #290 이후를 권장하나 **기술적 선행조건은 아니며** 변경을 혼합하지 않는다.
- `mols3131d` / `mols3131d@gmail.com` 외 계정·명의를 사용하지 않는다.
- Live model/remote service 호출과 credentials 사용은 명시적으로 준비된 환경과 권한을 확인한다. 테스트를 통과했다고 외부 Langfuse trace 성공을 주장하지 않는다.
- 현재 PR의 첫 커밋은 문서만 포함하며 실제 harness 실행/테스트 근거는 없다.
