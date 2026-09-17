---
title: "MVP"
description: "로컬 HMDA Data Lake와 evidence-first Reliability 위에서 최소한으로 유용한 Agentic review를 증명하기 위한 현재 MVP의 목표, scope와 acceptance를 정의합니다."
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

> **Active goal:** 로컬 HMDA 데이터로 최소 Data Lake를 end-to-end로 실행하고, 그 위에서 evidence-first Reliability와 제한된 Agentic review가 안전하게 동작하며 사람의 reliability 판단에도 최소한의 실질적 도움을 준다는 것을 증명한다.

이 문서는 **현재 MVP의 목표, scope와 acceptance만 소유한다.** 현재 구현 상태, validation 결과와 blocker는 여기서 관리하지 않는다.

MVP는 단순한 ETL 데모도, LLM을 붙인 anomaly demo도 아니다. **신뢰할 수 있는 데이터 상태를 만들고 → 문제를 결정론적으로 증명하고 → AI가 관련 근거를 바탕으로 사람의 조사·판단에 실제로 도움이 되는 review를 만들며 → 사람의 승인 뒤에만 복구하는 작은 완결 시스템**을 증명한다.

AI가 안전하게 호출되고 deterministic facts를 다시 말하는 것만으로는 충분하지 않다. MVP의 Agentic review는 제한된 범위 안에서 **추가로 확인할 evidence, 조사 우선순위, remediation의 누락이나 위험, 판단에 중요한 불확실성** 가운데 적어도 하나를 드러내 사람의 다음 판단을 개선할 수 있어야 한다.

## MVP Value

MVP는 다음 두 capability를 함께 증명해야 한다.

### Minimal Data Lake

HMDA Data는 local source를 검증해 DuckDB Bronze까지 적재되고, Data Platform은 그 Bronze를 dbt staging/mart로 변환한다. 이 결과는 downstream Reliability가 다시 추적할 수 있는 data와 dbt evidence를 남긴다.

### Agentic Reliability

Deterministic reliability layer를 먼저 만들고, 제한된 Agentic reviewer가 incident에 직접 관련된 bounded evidence와 기존 `RemediationDraft`를 설명·검토한다. AI review는 deterministic 결과의 단순 재진술을 넘어 사람이 다음 조사 또는 remediation 판단에 사용할 수 있는 추가 가치를 보여야 한다.

AI 판단은 관찰·평가·재현 가능해야 하며 실제 state change 권한은 갖지 않는다. 더 많은 context나 더 큰 자율성 자체가 목표가 아니며, **필요한 evidence를 제한적으로 제공해 최소한의 유용성을 증명하는 것**이 목표다.

**Data Lake만 있거나, Agentic review가 안전해도 실질적인 판단 가치를 증명하지 못하면 이 MVP가 아니다.**

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
    guard -. evaluation evidence .-> evaluation["Replayable Quality Evaluation"]

    incident --> proposal["Validated Recovery Proposal"]
    proposal --> human["Human Approval"]
    guard -. advisory .-> human
    human --> recovery["Approved Recovery"]
    recovery --> verify["Deterministic Re-validation"]

    airflow["Apache Airflow"] -. data plane .-> bronze
    airflow -. data plane .-> analytical
```

Airflow는 최소 Data Lake의 data plane을 실행한다. Reliability control-plane, Agentic review와 approval을 data plane에 암묵적으로 자동 결합하지 않는다. Agentic review는 MVP proof에는 필요하지만 기존 deterministic recovery proposal / approval / recovery contract의 authority를 대체하거나 새로운 authorization prerequisite를 만들지 않는다.

`Bounded Review Context`는 raw data, 전체 manifest 또는 로그를 무제한으로 전달하는 방식이 아니다. Review에 필요한 incident 주변 evidence를 결정론적으로 선택하고 provenance를 유지해 AI가 근거를 추적하면서도 불필요한 context에 의존하지 않게 한다.

## System Invariants

1. **Deterministic truth first** — detection과 핵심 safety 판단을 LLM에 맡기지 않는다.
1. **Evidence-bound AI** — Agentic 판단은 저장소가 선택해 제공한 bounded evidence와 deterministic `RemediationDraft`를 근거로 한다.
1. **Useful, not merely valid** — structured validation을 통과했다는 사실만으로 review를 성공으로 보지 않는다. 사람의 조사 또는 remediation 판단에 추가 가치를 제공해야 한다.
1. **Proposal-bound approval** — human approval은 검증된 recovery proposal에 결합된다.
1. **Advisory, not authoritative** — Agentic review는 human decision을 보조하지만 approval/recovery authority를 획득하거나 변경하지 않는다.
1. **Human-controlled mutation** — AI output만으로 데이터 state를 변경할 수 없다.
1. **Locally reproducible core** — Data Lake, Reliability와 safety contract는 외부 model 호출 없이 반복 검증할 수 있다.
1. **Observable live judgment** — 실제 Agentic invocation은 입력 근거, model/prompt 조건, 결과와 실행 비용·성능을 검토할 evidence를 남긴다.
1. **Replayable utility evaluation** — 같은 review case와 versioned evaluation 기준으로 Agentic output의 최소 유용성을 다시 평가하고 변경 전후를 비교할 수 있다.
1. **Acceptance over feature count** — 기능 수보다 하나의 완결된 proof로 MVP를 판단한다.

## Domain Completion Gates

[`domains/OVERVIEW.md`](domains/OVERVIEW.md)와 각 domain 문서는 domain 구조와 ownership을 설명하는 guide다. 현재 capability의 normative contract는 [`../openspec/specs/`](../openspec/specs/)가 소유한다. 여기서는 MVP에 필요한 proof만 정의한다.

| Domain | MVP proof |
| --- | --- |
| [HMDA Data](domains/hmda-data.md) | 같은 source와 case에서 재현 가능한 Source → Bronze state와 synthetic incident input을 만든다. |
| [Data Platform](domains/data-platform.md) | Bronze → staging → mart와 채택된 dbt artifact/lineage evidence를 추적할 수 있다. |
| [Data Operations](domains/data-operations.md) | ingestion/dbt/reliability execution과 candidate/current adoption boundary, failure evidence가 명확하다. |
| [Reliability](domains/reliability.md) | deterministic incident → validated proposal/approval → recovery → re-validation을 닫는다. |
| [Review AI](domains/review-ai.md) | Incident 주변의 bounded evidence와 `RemediationDraft`를 advisory review로 변환하고, deterministic validation과 invocation provenance를 유지하면서 최소한의 review utility를 평가할 수 있다. |
| [Runtime AI](domains/runtime-ai.md) | Review semantics와 분리된 provider-neutral settings와 bounded invocation contract를 재현 가능하게 검증한다. |
| [Orchestration](domains/orchestration.md) | Bronze와 dbt analytical layer의 local data plane을 Airflow dependency로 반복 실행한다. |

## MVP Acceptance

하나의 current revision에서 Foundation Proofs와 Utility Proofs가 모두 성립하면 완료한다.

### Foundation Proofs

- **Data Lake proof** — HMDA source가 Bronze와 dbt analytical layer까지 재현 가능하게 흐른다.
- **Reliability proof** — 대표 synthetic incident를 deterministic evidence로 탐지·설명하고 recovery 뒤 같은 기준으로 다시 검증한다.
- **Agentic contract proof** — structured review contract, evidence binding, structured-fact validation과 evaluation을 deterministic하게 반복 검증할 수 있다.
- **Live Agentic proof** — 같은 revision에서 실제 model invocation이 evidence와 `RemediationDraft`를 기반으로 structured review를 최소 한 번 만들고, model/config, prompt identity, project revision, evidence refs, output, latency와 제공 가능한 usage(token/cost)를 invocation evidence로 남긴다. 이 proof는 deterministic regression과 동일하게 취급하지 않는다.
- **Safety proof** — Agentic output은 deterministic guardrail과 proposal-bound human approval을 우회해 mutation을 일으킬 수 없고, LLM availability 자체가 recovery authority를 부여하거나 변경하지 않는다.
- **Reproducibility proof** — 정상, incident, recovery와 주요 failure/retry의 deterministic 결과를 같은 revision에서 다시 설명할 수 있고 live invocation 결과는 evidence로 보존된다.

### Utility Proofs

- **Review context proof** — 대표 review case에서 단일 incident의 최소 structured facts뿐 아니라 판단에 직접 필요한 주변 evidence를 bounded context로 선택하고, 각 evidence의 provenance와 누락·미확인 context를 구분할 수 있다.
- **Agentic utility proof** — 대표 review case에서 AI가 deterministic facts 또는 `RemediationDraft`를 단순 재진술하는 데 그치지 않고, 사람의 다음 판단에 사용할 수 있는 decision-relevant contribution을 최소 하나 만든다. 예시는 evidence gap, 조사 우선순위, remediation critique 또는 중요한 uncertainty 식별이다.
- **Quality evaluation proof** — review utility를 versioned human rubric으로 평가하고 같은 case와 기준으로 다시 실행할 수 있다. 최소 기준은 added value, actionability, evidence awareness, uncertainty handling과 prioritization을 포함하되, 자동 LLM judge나 특정 평가 플랫폼에 의존하지 않는다.
- **Change comparison proof** — prompt, model 또는 review context의 의미 있는 변경은 같은 representative case와 rubric에서 현재 baseline과 비교할 수 있고, 채택 여부와 근거를 사람이 검토 가능한 evidence로 남길 수 있다.

## Scope

### In Scope

- local HMDA CSV/Parquet와 Source → DuckDB Bronze 적재
- dbt staging/marts와 artifact evidence
- Airflow local data plane
- deterministic profiling, incident, impact, `RemediationDraft`, recovery와 evaluation
- 대표 synthetic incident를 사용하는 최소 Agentic review
- Agentic contract evaluation과 최소 한 번의 observable live model proof
- incident 판단에 직접 관련된 profile, sibling signal, lineage/impact, dbt execution 또는 domain semantics 중 필요한 evidence만 제한적으로 선택하는 review context
- Agentic structured-fact validation, invocation provenance와 최소한의 human utility evaluation
- 같은 representative case와 versioned rubric을 사용하는 작은 baseline/candidate comparison
- validated recovery proposal, human approval, recovery와 re-validation

### Out of Scope

- cloud deployment와 distributed lakehouse
- 범용 multi-dataset ingestion platform
- 모든 incident type의 완전한 기능 parity
- 모든 raw row, 전체 manifest 또는 전체 execution log를 AI context로 제공하는 것
- 모든 domain semantics를 완전한 knowledge layer로 모델링하는 것
- LLM 기반 anomaly detection 또는 승인 없는 automatic recovery
- autonomous RCA, multi-agent workflow와 approval UI
- automatic LLM-as-a-judge를 MVP acceptance의 authority로 사용하는 것
- production-grade evaluation platform, production SLO, security-grade authorization와 multi-host coordination
- 특정 LLM provider 또는 LLMOps vendor를 canonical source로 고정하는 것

## Lifecycle

이 문서는 MVP가 active인 동안만 유지한다. MVP 종료 시 durable architecture/domain guidance와 구현·검증된 capability contract를 각각 `docs/**`와 `openspec/specs/**`의 owning location에 반영한 뒤 이 phase 문서를 `main`에서 삭제한다. Historical 보존을 위한 별도 docs archive는 만들지 않는다.
