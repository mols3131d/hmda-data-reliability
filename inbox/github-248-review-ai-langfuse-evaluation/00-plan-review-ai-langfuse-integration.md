---
type: plan
title: "Review AI Langfuse Integration Plan"
description: "PR #245 이후 Review AI에 optional Langfuse tracing과 human evaluation workflow를 도입하기 위한 준비 계획입니다."
tags:
  - "domain:review-ai"
  - "capability:reliability-agentic-review"
  - evaluation
  - langfuse
  - llmops
---

# Review AI Langfuse Integration Plan

이 work unit은 Review AI의 repository-native evaluation contract를 유지하면서 Langfuse를 optional live observability와 human evaluation surface로 도입하기 위한 별도 작업이다.

현재 PR #245가 아직 merge되지 않았으므로 이 branch/PR은 **준비용 Draft**로 시작한다. Langfuse implementation은 #245 merge와 필요한 OpenSpec canonical transition을 확인한 뒤 최신 `main`을 동기화하고 시작한다.

## Goal

실제 live Review AI invocation을 추적하고, 사람이 현재 human rubric으로 output을 평가할 수 있는 가장 작은 Langfuse integration을 증명한다.

Langfuse 도입 자체가 목적은 아니다. Repository가 evaluation semantics, deterministic safety, prompt identity와 durable acceptance boundary를 계속 소유한다.

## Preconditions

Implementation 전에 다음을 모두 다시 확인한다.

1. PR #245가 `main`에 merge되었다.
1. `review-ai-utility-evaluation` OpenSpec change의 canonical transition이 필요한 경우 완료되었다.
1. 최신 `main`에서 current `docs/mvp.md`, canonical OpenSpec, `review_ai`/`runtime_ai` implementation과 tests를 다시 읽었다.
1. Langfuse 최신 공식 Python/OpenTelemetry와 human annotation/score surface를 조사했다.

Precondition이 충족되기 전에는 dependency 추가나 production code 변경을 시작하지 않는다.

## Decision First

다음 세 질문에 모두 `yes`일 때만 integration을 진행한다.

1. 사람이 live invocation, output, provenance와 rubric score를 연결하는 현재 workflow에 material한 마찰이 남아 있는가?
1. Langfuse가 custom tooling보다 작은 비용으로 그 마찰을 줄이는가?
1. Langfuse가 unavailable이어도 repository core와 deterministic validation을 그대로 유지할 수 있는가?

## Minimum Scope

첫 implementation slice는 다음을 우선한다.

- existing invocation identity를 사용한 optional Langfuse trace/observation projection
- current human rubric score와 rationale을 Langfuse annotation surface에 표현
- secret/raw evidence leakage 방지와 Langfuse failure isolation
- external Langfuse 없이 검증 가능한 fake/stub tests
- opt-in live smoke

Completed annotation의 repository one-way import는 public supported API, existing repository contract와 낮은 구현 복잡도가 확인될 때만 같은 PR에 포함한다.

## Boundaries

- Langfuse는 canonical evaluation source가 아니다.
- Prompt Management로 repository prompt authority를 이전하지 않는다.
- provider `trace_id`와 Langfuse trace/observation identity를 같은 의미로 재사용하지 않는다.
- automatic LLM judge, Promptfoo, generic evaluator/plugin framework, dataset/experiment platform과 production-grade self-host infrastructure는 이 PR 범위 밖이다.
- future convenience를 위해 `output_fixture_id`, rubric schema, evidence store 또는 evaluation type을 선제적으로 일반화하지 않는다.
- private/unstable API, scraping 또는 generic two-way synchronization을 요구하면 scope를 확장하지 않고 중단한다.

## Validation

- Langfuse disabled 상태에서 기존 Review AI behavior와 tests가 유지된다.
- trace projection이 stable repository identity를 보존한다.
- credential, raw large payload와 불필요한 evidence가 export되지 않는다.
- Langfuse client/network failure가 Review AI result 또는 recovery authority를 변경하지 않는다.
- human annotation mapping을 구현하면 score와 rationale의 의미가 손실되지 않는다.
- import를 구현하면 invocation/output/revision/rubric mismatch를 fail-closed 한다.
- live smoke를 실행하지 못하면 `⚪ Not Verified`로 명시한다.

## Done When

현재 필요성을 근거로 선택한 최소 Langfuse integration이 optional boundary를 유지하며 검증되고, repository-native evaluation contract와 deterministic safety가 Langfuse availability와 독립적으로 유지되면 완료한다.
