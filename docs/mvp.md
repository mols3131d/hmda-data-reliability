---
title: "MVP"
description: "로컬 HMDA Data Lake와 evidence-first Reliability, 제한된 Agentic review를 하나의 완결된 proof로 검증하기 위한 현재 MVP 목표, scope와 acceptance를 정의합니다."
categories:
  - data-engineering
  - reliability
  - ai-engineering
tags:
  - airflow
  - ai-delegation
  - dbt
  - duckdb
  - evaluation
  - evidence-first
  - llm
  - recovery
---

# MVP

> **Active goal:** 로컬 HMDA 데이터로 최소 Data Lake를 end-to-end로 실행하고, 그 위에서 evidence-first Reliability와 제한된 Agentic review가 안전하면서도 사람의 reliability 판단을 실질적으로 보조할 만큼 유용하게 동작함을 증명한다.

이 문서는 **현재 MVP의 목표, scope와 acceptance만 소유한다.** 현재 구현 상태, validation 결과와 blocker는 여기서 관리하지 않는다.

MVP는 단순한 ETL 데모도, LLM을 붙인 anomaly demo도 아니다. **신뢰할 수 있는 데이터 상태를 만들고 → 문제를 결정론적으로 증명하고 → AI가 필요한 근거를 제한된 맥락에서 검토해 사람의 조사·판단에 추가 가치를 제공하며 → 사람의 승인 뒤에만 복구하는 작은 완결 시스템**을 증명한다.

## MVP Value

MVP는 두 capability가 함께 존재해야 한다.

### Minimal Data Lake

HMDA Data가 local source를 검증해 DuckDB Bronze까지 적재하고, Data Platform이 그 Bronze를 dbt staging/mart로 변환한다. 결과는 downstream Reliability가 다시 추적할 수 있는 data와 dbt evidence를 남긴다.

### Agentic Reliability

Deterministic reliability layer를 먼저 만들고, 제한된 Agentic reviewer가 incident를 이해하는 데 필요한 bounded context와 기존 `RemediationDraft`를 검토한다. AI는 deterministic 결과를 단순 재서술하는 데 그치지 않고 조사 우선순위, evidence gap, remediation의 약점 또는 근거에 제한된 대안 가설처럼 사람이 다음 판단을 내리는 데 필요한 추가 가치를 제공해야 한다. AI 판단은 관찰·평가·재실행 가능해야 하며 실제 state change 권한은 갖지 않는다.

**Data Lake만 있거나, 안전하지만 실질적인 review value가 없는 Agentic demo만 있어서는 이 MVP가 아니다.**

## Minimum Useful Agentic Review

MVP에서 Agentic review의 목표는 범용 자율 RCA가 아니라 **사람이 incident를 더 잘 조사하고 remediation을 검토하도록 돕는 최소한의 유용한 advisory review**다.

최소한의 유용성은 다음 조건으로 판단한다.

1. **Bounded context sufficiency** — review input은 target incident와 deterministic `RemediationDraft`뿐 아니라 해당 판단에 직접 필요한 surrounding profile, sibling signal, lineage·downstream impact, dbt/source execution evidence와 domain semantics 중 관련 있는 evidence를 제한적으로 선택한다. 제공되지 않은 정보와 unknown은 숨기지 않는다.
1. **Added review value** — output은 제공된 deterministic fact의 자연어 재서술만으로 끝나지 않고 investigation priority, evidence gap, remediation critique 또는 근거에 제한된 alternative hypothesis 중 하나 이상의 실질적인 review contribution을 제공한다.
1. **Evaluable utility** — 사전에 고정된 대표 case와 rubric으로 같은 review를 다시 평가할 수 있어야 한다. 단순히 schema가 유효하거나 deterministic validator를 통과했다는 사실은 usefulness의 증거가 아니다.
1. **Bounded authority** — 유용성 평가를 통과하더라도 review는 advisory다. deterministic truth, approval과 recovery authority는 기존 경계를 유지한다.

Exact context projection, case set, rubric과 threshold는 해당 capability의 owning Spec 또는 active Change가 정의한다. 이 문서는 MVP가 요구하는 제품 수준의 acceptance boundary만 소유한다.

## System Proof

```mermaid
flowchart TB
    source["HMDA source"] --> bronze["Bronze"]
    bronze --> analytical["dbt staging / marts"]
    analytical --> evidence["Data + dbt evidence"]
    evidence --> reliability["Deterministic Reliability"]
    reliability --> incident["Incident + RemediationDraft"]

    incident --> context["Bounded Review Context"]
    context --> agent["Useful Agentic Review"]
    agent --> guard["Deterministic Review Validation"]

    incident --> proposal["Validated Recovery Proposal"]
    proposal --> human["Human Approval"]
    guard -. advisory .-> human
    human --> recovery["Approved Recovery"]
    recovery --> verify["Deterministic Re-validation"]

    airflow["Apache Airflow"] -. data plane .-> bronze
    airflow -. data plane .-> analytical
```

Airflow는 최소 Data Lake의 data plane을 실행한다. Reliability control-plane, Agentic review와 approval을 data plane에 암묵적으로 자동 결합하지 않는다. Agentic review는 MVP proof에는 필요하지만 기존 deterministic recovery proposal / approval / recovery contract의 authority를 대체하거나 새로운 authorization prerequisite를 만들지 않는다.

## System Invariants

1. **Deterministic truth first** — detection과 핵심 safety 판단을 LLM에 맡기지 않는다.
1. **Evidence-bound AI** — Agentic 판단은 저장소가 제공하고 provenance를 유지하는 bounded context와 deterministic `RemediationDraft`를 근거로 한다.
1. **Utility beyond restatement** — Agentic review는 deterministic fact의 재서술만으로 MVP acceptance를 충족하지 않는다.
1. **Proposal-bound approval** — human approval은 검증된 recovery proposal에 결합된다.
1. **Advisory, not authoritative** — Agentic review는 human decision을 보조하지만 approval/recovery authority를 획득하거나 변경하지 않는다.
1. **Human-controlled mutation** — AI output만으로 데이터 state를 변경할 수 없다.
1. **Locally reproducible core** — Data Lake, Reliability와 safety contract는 외부 model 호출 없이 반복 검증할 수 있다.
1. **Observable live judgment** — 실제 Agentic invocation은 입력 근거, model/prompt 조건, 결과와 실행 비용·성능을 검토할 evidence를 남긴다.
1. **Replayable utility** — 대표 review case와 평가 기준은 변경 전후 Agentic utility를 같은 조건에서 다시 비교할 수 있어야 한다.
1. **Acceptance over feature count** — 기능 수보다 하나의 완결된 proof로 MVP를 판단한다.

## Domain Completion Gates

[`domains/OVERVIEW.md`](domains/OVERVIEW.md)와 각 domain 문서는 domain 구조와 ownership을 설명하는 human-readable guide다. Current capability의 normative contract는 [`../openspec/specs/`](../openspec/specs/)가 소유한다. 여기서는 MVP에서 필요한 proof만 정의한다.

| Domain | MVP proof |
| --- | --- |
| [HMDA Data](domains/hmda-data.md) | 같은 source와 case에서 재현 가능한 Source → Bronze state와 synthetic incident input을 만든다. |
| [Data Platform](domains/data-platform.md) | Bronze → staging → mart와 채택된 dbt artifact/lineage evidence를 추적할 수 있다. |
| [Data Operations](domains/data-operations.md) | ingestion/dbt/reliability execution과 candidate/current adoption boundary, failure evidence가 명확하다. |
| [Reliability](domains/reliability.md) | deterministic incident → validated proposal/approval → recovery → re-validation을 닫는다. |
| [Review AI](domains/review-ai.md) | Reliability lifecycle에서 필요한 evidence를 bounded review context로 투영하고, deterministic validation과 provenance를 유지하면서 사람의 조사·remediation 판단에 추가 가치를 주는 advisory review를 생성·평가할 수 있다. |
| [Runtime AI](domains/runtime-ai.md) | Review semantics와 분리된 provider-neutral settings와 bounded invocation contract를 재현 가능하게 검증한다. |
| [Orchestration](domains/orchestration.md) | Bronze와 dbt analytical layer의 local data plane을 Airflow dependency로 반복 실행한다. |

## MVP Acceptance

하나의 current revision에서 다음 proof가 모두 성립하면 완료한다.

- **Data Lake proof** — HMDA source가 Bronze와 dbt analytical layer까지 재현 가능하게 흐른다.
- **Reliability proof** — 대표 synthetic incident를 deterministic evidence로 탐지·설명하고 recovery 뒤 같은 기준으로 다시 검증한다.
- **Agentic context proof** — 대표 review case에 대해 target incident와 `RemediationDraft`를 넘어 판단에 직접 필요한 surrounding reliability evidence를 deterministically 선택한 bounded context를 만들고 provenance와 explicit unknown을 보존한다. Raw dataset, 전체 manifest 또는 무관한 로그를 무제한으로 prompt에 전달하는 방식은 proof로 인정하지 않는다.
- **Agentic contract proof** — structured review contract, context/evidence binding, structured-fact validation과 provenance를 deterministic하게 반복 검증할 수 있다.
- **Live Agentic utility proof** — 같은 revision에서 실제 model invocation을 사전에 고정된 대표 case와 rubric으로 평가한다. Review가 deterministic fact를 단순 재서술하는 데 그치지 않고 investigation priority, evidence gap, remediation critique 또는 근거에 제한된 alternative hypothesis 중 하나 이상의 유용한 contribution을 제공한다는 human evaluation evidence를 남겨야 한다. Model/config, prompt identity, project revision, context/evidence refs, output, latency와 제공 가능한 usage(token/cost)도 invocation evidence로 보존한다. Structured validation을 통과했다는 사실만으로 이 proof를 충족하지 않는다.
- **Safety proof** — Agentic output은 deterministic guardrail과 proposal-bound human approval을 우회해 mutation을 일으킬 수 없고, LLM availability 또는 utility 평가 결과 자체가 recovery authority를 부여하거나 변경하지 않는다.
- **Reproducibility proof** — 정상, incident, recovery와 주요 failure/retry의 deterministic 결과를 같은 revision에서 다시 설명할 수 있다. Agentic review는 동일 case/context/rubric으로 replay하여 변경 전후 utility를 비교할 수 있고 live invocation 결과와 human evaluation evidence를 보존한다.

## Scope

### In Scope

- local HMDA CSV/Parquet와 Source → DuckDB Bronze 적재
- dbt staging/marts와 artifact evidence
- Airflow local data plane
- deterministic profiling, incident, impact, `RemediationDraft`, recovery와 evaluation
- 대표 reliability case에 필요한 bounded review context selection
- 사람의 조사·remediation 판단에 추가 가치를 제공하는 최소 Agentic review
- Agentic contract evaluation, replay 가능한 utility evaluation과 observable live model proof
- validated recovery proposal, human approval, recovery와 re-validation

### Out of Scope

- cloud deployment와 distributed lakehouse
- 범용 multi-dataset ingestion platform
- 모든 incident type의 완전한 기능 parity
- LLM 기반 anomaly detection 또는 승인 없는 automatic recovery
- autonomous RCA, multi-agent workflow와 approval UI
- production SLO, security-grade authorization와 multi-host coordination
- 특정 LLM provider 또는 LLMOps vendor를 canonical source로 고정하는 것

## Lifecycle

이 문서는 MVP가 active인 동안만 유지한다. MVP 종료 시 durable architecture/domain guidance와 구현·검증된 capability contract를 각각 `docs/**`와 `openspec/specs/**`의 owning location에 반영한 뒤 이 phase 문서를 `main`에서 삭제한다. Historical 보존을 위한 별도 docs archive는 만들지 않는다.
