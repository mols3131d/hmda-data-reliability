---
type: review
title: "Ingestion Agent Harness PR Preparation Self-Review"
description: "PR #291의 개발 의도·현재 MVP 계약·프레임워크 선택권·인계 실효성을 검토한다."
---

# Ingestion Agent Harness PR Preparation Self-Review

> [!NOTE]
> **Preparation: fit after clarification. Implementation readiness: not ready.** 사용자 의도인 ingestion 작업용 LangChain 생태계 기반 LLMOps harness를 보존하면서, 기존 계획의 조기 설계 확정과 불필요한 승인 의무를 교정했다. Framework 도입, 구현 및 런타임 검증은 아직 수행하지 않았다.

- **Target:** [PR #291](https://github.com/mols3131d/hmda-data-reliability/pull/291), `agent/feat/build-ingestion-agent-harness`
- **Revision:** 최초 리뷰 기준 `main@35d099c748cbe08ae6a12ce60acd7574fe086719` → head `f6a638a0a79a7a732c93b0e4a19b9efd67e2ea37`; 이후 문서 보완은 같은 PR에서 수행
- **Scope:** PR 준비 문서 3개, MVP·Ingestion·Orchestration 계약, LangGraph/Deep Agents 공식 개요의 정적 검토

## Findings

| ID | Severity | Finding | Action |
| --- | --- | --- | --- |
| F1 | 🟠 Major | 첫 preflight→plan→write 흐름을 확정 설계처럼 서술해 실제 에이전트 작업의 목표를 좁힐 위험 | vertical slice를 후보로 두고 agent의 선택·도구 사용·작업 위임을 완료 조건에 포함 |
| F2 | 🟠 Major | 모든 ingest 경로에 새로운 human approval을 요구하는 듯한 인계 | AI가 권한을 생성하지 못하게 하되 기존 authorized caller와 human approval을 구별 |
| F3 | 🟡 Minor | LangGraph 우선 채택, PR #290 선행을 강한 전제로 오해할 가능성 | LangGraph·Deep Agents 비교 중립화 및 독립 PR 관계 명시 |
| F4 | 🟡 Minor | replay·checkpoint·외부 trace 요건이 검증 범위를 과도하게 넓힐 위험 | 증거 보존은 필수, 추가 기능은 첫 slice에 실제 필요할 때만 선택 |

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | 사용자의 목표와 준비 문서의 정적 비교 | [Research](00-research-ingestion-agent-harness-boundary.md), [Plan](01-plan-ingestion-agent-harness-mvp.md), [Handoff](02-brief-ingestion-agent-harness-implementation-handoff.md) |
| ✅ Pass | 기존 ownership과 안전 경계 확인 | [MVP](../../docs/mvp.md), [Architecture](../../docs/ARCHITECTURE.md), [Ingestion Spec](../../openspec/specs/hmda-data-ingestion/spec.md), [Orchestration Spec](../../openspec/specs/orchestration-pipeline/spec.md) |
| ✅ Pass | Framework capabilities 문서 확인 | [LangGraph](https://docs.langchain.com/oss/python/langgraph/overview), [Deep Agents](https://docs.langchain.com/oss/python/deepagents/overview) |
| ⚪ Not Verified | SDK/model adapter 실제 통합, 변경된 MVP/OpenSpec, tool execution 및 CI | 구현 전이며 실행하지 않음 |

## Risks and Limits

현재 canonical MVP는 reliability review를 중심으로 한다. 사용자 요청인 ingestion agent MVP는 향후 해당 owner를 통한 명시적 scope/contract 정합화가 필요하며, 이 Inbox 문서로 정본을 덮어쓰지 않는다. 로컬 에이전트는 설계 제안과 실제 규범을 구분하고 현재 소스·의존성·실행 경계를 확인한 뒤 필요한 것만 채택해야 한다. 셀프 리뷰는 독립 승인이나 merge readiness를 의미하지 않는다.
