---
type: plan
title: "Review AI Langfuse Integration Plan"
description: "Review AI의 repository-native evaluation contract 위에 optional Langfuse tracing과 human annotation을 도입하기 위한 PR #248 실행 계획입니다."
tags:
  - "domain:review-ai"
  - "capability:reliability-agentic-review"
  - evaluation
  - langfuse
  - llmops
---

# Review AI Langfuse Integration Plan

이 work unit은 Review AI의 repository-native evaluation contract를 유지하면서 Langfuse를 optional live observability와 human evaluation surface로 도입한다. Langfuse 도입 자체가 목적은 아니며, repository가 evaluation semantics, deterministic safety, prompt identity와 acceptance boundary를 계속 소유한다.

## Current State

- PR #245는 `main`에 merge되었고 이 setup은 merge commit `dda8f24510ca83f9cefd9d4039f117a02eb2fa31`을 기준으로 다시 검토했다.
- #248 branch는 위 `main` revision을 병합해 #245의 Review AI implementation, tests와 working context를 포함한다.
- `openspec/changes/review-ai-utility-evaluation/`은 아직 active Change로 남아 있고, bounded context, structured utility contribution, versioned human utility evaluation과 baseline/candidate comparison의 durable requirements는 아직 모두 canonical `openspec/specs/reliability-agentic-review/spec.md`에 반영되지 않았다.
- 따라서 #248은 계속 Draft/setup-only 상태로 유지하며, OpenSpec transition이 완료되기 전에는 Langfuse dependency나 production integration code를 추가하지 않는다.

## Goal

실제 live Review AI invocation을 repository identity와 연결해 추적하고, 사람이 현재 `rubric_v1`으로 output을 평가할 수 있는 가장 작은 optional Langfuse integration을 증명한다.

## Activation Gate

Implementation은 다음 조건이 모두 충족된 뒤 시작한다.

1. `review-ai-utility-evaluation`의 구현·검증된 durable requirements가 current OpenSpec workflow를 통해 canonical `openspec/specs/**`에 반영된다.
1. 완료된 Change가 current workflow에 맞게 archive 또는 정리되어 active delta와 canonical contract의 역할이 다시 분리된다.
1. 그 transition은 #248에 섞지 않고 별도 owning work unit에서 완료한다.
1. transition이 반영된 최신 `main`을 #248 branch에 다시 동기화한다.
1. current `docs/mvp.md`, `docs/domains/review-ai.md`, canonical OpenSpec, `review_ai`/`runtime_ai` source와 tests를 다시 확인한다.
1. Langfuse의 최신 공식 Python/OpenTelemetry tracing, human annotation/score와 public score retrieval surface를 다시 확인한다.

`main` 또는 canonical contract가 달라지면 이 gate와 아래 projection을 다시 검토한다.

## Decision Gate

다음 세 질문에 모두 `yes`일 때만 integration을 진행한다.

1. 사람이 live invocation, output, provenance와 rubric score를 연결하는 현재 workflow에 material한 마찰이 남아 있는가?
1. Langfuse가 custom tooling보다 작은 비용으로 그 마찰을 줄이는가?
1. Langfuse가 unavailable이어도 Review AI core, deterministic validation과 recovery boundary가 그대로 유지되는가?

하나라도 `no`이면 dependency를 추가하지 않고 범위를 줄이거나 도입을 중단한다.

## First Slice

### Optional Trace Projection

새 canonical provenance schema를 만들지 않고 existing repository identity를 Langfuse trace/observation metadata로 투영한다. 우선 검토할 field는 다음이다.

- `invocation_id`
- `project_revision`
- prompt template/version과 digest
- model과 sanitized configuration
- review result와 validation status
- output digest 또는 stable output identity
- latency와 available usage

Langfuse trace/observation ID는 integration-local identity로 취급하고 core Review AI model이나 evaluation contract에 영구 field로 추가하지 않는다. Provider `trace_id`와 Langfuse identity도 같은 의미로 재사용하지 않는다.

### Human Annotation Mapping

Repository-owned `rubric_v1`의 `added_value`, `actionability`, `evidence_awareness`, `uncertainty_handling`, `prioritization`을 Langfuse human score/comment surface에 손실 없이 표현할 수 있는지 검증한다.

Langfuse의 score config, queue description과 display metadata는 integration projection이다. Repository rubric semantics, same-case invariant 또는 human decision authority를 vendor schema에 맞춰 바꾸지 않는다. Annotation 결과만으로 candidate 승인, recovery 또는 delegation authority를 변경하지 않는다.

### Data Minimization and Failure Isolation

- credential, raw provider error, raw large evidence, 전체 log와 불필요한 payload를 export하지 않는다.
- Human review에 실제로 필요한 input/output visibility는 공식 tracing surface를 확인한 뒤 최소 allowlist로 정한다. Evidence는 가능한 경우 raw payload보다 identity, digest와 bounded projection을 우선한다.
- Langfuse disabled 상태에서는 기존 Review AI behavior가 변하지 않아야 한다.
- Langfuse client, network 또는 ingestion failure는 Review AI result, deterministic validation, invocation provenance의 repository contract 또는 recovery authority를 변경해서는 안 된다.

## Deferred by Default

Completed human annotation의 repository one-way import는 첫 implementation slice의 기본 범위에서 제외한다. 공식 public API로 score/rationale와 repository identity를 읽을 수 있고, polling worker, 별도 synchronization framework, generic evaluation store 또는 vendor-specific core field 없이 작은 adapter 하나로 끝나는 것이 확인될 때만 Review에서 scope 추가를 검토한다.

현재 공식 surface에는 human annotation을 위한 Annotation Queue/Score와 score 조회용 public API가 존재하므로 기술적 가능성은 있다. 그러나 가능하다는 이유만으로 첫 PR에 import를 포함하지 않는다.

## Boundaries

- Langfuse는 canonical evaluation source가 아니다.
- Prompt Management로 repository prompt authority를 이전하지 않는다.
- automatic LLM judge, Promptfoo, generic evaluator/plugin framework, dataset/experiment platform과 production-grade self-host infrastructure는 이 PR 범위 밖이다.
- future convenience를 위해 `output_fixture_id`, rubric schema, evidence store 또는 evaluation type을 선제적으로 일반화하지 않는다.
- private/unstable API, scraping 또는 generic two-way synchronization을 요구하면 scope를 확장하지 않고 중단한다.
- OpenSpec canonicalization/archive는 #248의 구현 scope가 아니다.

## Validation

Setup 단계에서는 다음을 검증한다.

- #245 merge가 포함된 current `main`과 branch history가 동기화되어 있다.
- PR description과 이 plan이 current prerequisite와 scope를 같은 의미로 설명한다.
- setup-only head에서 repository CI가 통과한다.

Implementation 단계에서는 다음을 추가한다.

- Langfuse disabled 상태에서 기존 Review AI behavior와 tests가 유지된다.
- trace projection이 stable repository identity를 보존한다.
- credential, raw large payload와 불필요한 evidence가 export되지 않는다.
- Langfuse client/network failure가 Review AI result 또는 recovery authority를 변경하지 않는다.
- human annotation mapping이 score와 rationale 의미를 손실하지 않는다.
- opt-in live smoke에서 실제 invocation 하나를 추적하고 human annotation workflow를 확인한다. 실행하지 못하면 `⚪ Not Verified`로 명시한다.

## Done When

Activation Gate를 통과한 current `main` 위에서 선택한 최소 Langfuse integration이 optional boundary를 유지하며 검증되고, repository-native evaluation contract와 deterministic safety가 Langfuse availability와 독립적으로 유지되면 완료한다.
