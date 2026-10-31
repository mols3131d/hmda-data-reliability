---
type: plan
title: "Review AI Output Quality Follow-up"
description: "PR #278에서 확인된 Review AI 수치 설명 오류, 예시 복사와 검토 가치 부족을 재현·평가하고 최소 변경으로 개선하기 위한 실행 계획입니다."
tags:
  - review-ai
  - evaluation
  - output-quality
status: in-progress
---

# Review AI Output Quality Follow-up

## Goal

Review AI의 **schema 통과와 실제 출력 품질을 구분**하고, 수치 정확성·입력 충실성·추가 검토 가치를 대표 사례에서 검증한다. 확인된 결함만 최소한으로 수정하며 개선이 입증되지 않으면 후보를 채택하지 않는다.

이 문서는 착수 계획이다. 선택 가능한 v3 후보와 독립 품질 corpus의 로컬 구현은 [OpenSpec Change](../../openspec/changes/review-ai-ground-output-explanations/tasks.md)에서 추적한다. 모델 비교 실행과 사람의 utility 평가는 아직 수행되지 않았다.

## Starting Point

- Base: PR [#278](https://github.com/mols3131d/hmda-data-reliability/pull/278)이 병합된 `main`; 작업 시작 시 head를 다시 확인한다.
- 근거와 재현 입력: [PR #278 후속 계획](../github-278-resolve-review-ai-live-schema/04-plan-review-ai-output-quality-follow-up.md). 기존 출력의 숫자·예시 복사 오류는 관찰됐으나 반복 성공률이나 일반화된 모델 품질 결론은 아니다.
- Current baseline: `v2` prompt. 기존 [human rubric과 comparison](https://github.com/mols3131d/hmda-data-reliability/blob/1d03c5397bd75422cfd94b6d2ce7d67d682e7565/src/hmda_reliability/review_ai/evaluation/value.py), [평가 가이드](../../docs/development/review-ai-evaluation.md), [canonical Spec](../../openspec/specs/reliability-agentic-review/spec.md)을 재사용한다.
- Active OpenSpec Change `review-ai-evaluation-subdomain-refactor` 및 `review-ai-langfuse-projection`과 ownership·진행 상태를 먼저 대조한다. Inbox는 요구사항 정본이 아니다.

## Accepted Context Configuration

2026-10-28 사용자 수용 결정: **RTX 3070 8GB에서 Qwen3.5 4B의 Ollama active context를 16K(`num_ctx=16384`)로 우선 운영·검증하고, 이후 32K(`num_ctx=32768`)를 추가 검증**한다. 32K 운영 확정이나 모든 환경에서의 성능·안정성 보장은 아니다.

- **Evidence:** PR #278의 `qwen3.5:4b-8k-local`은 active context 8192 및 출력 제한 4096에서 schema·guard 검증을 통과했다. 기존 4K 실행에서는 `length` 종료와 빈 본문이 관찰됐다. RTX 3070의 16K/32K 실제 VRAM 사용량과 응답 품질은 아직 측정하지 않았다.
- **Execution:** 기존 모델을 보존하고 동일 양자화의 16K 변형으로 시작한다. 16K에서 메모리·완료 여부·품질을 확인한 뒤 32K를 시험한다. `ollama ps`로 실제 `CONTEXT`와 GPU/CPU 적재 상태를, `nvidia-smi`로 GPU 메모리를 확인한다. 실패와 CPU offload도 숨기지 않는다.
- **Controls:** 초기 출력 상한은 PR #278에서 검증한 4096토큰을 유지하고, `num_ctx`(전체 문맥)와 `max_output_tokens`(생성 상한)을 구별한다. Thinking 설정, prompt, 모델, 입력을 한꺼번에 바꾸지 않는다. Context별 비교와 prompt baseline/candidate 비교는 분리하며 후자의 active context는 동일하게 유지한다.
- **Thinking:** Qwen3.5/Ollama가 제공하는 기존 Thinking 기능의 실제 활성 상태부터 확인한다. 비활성화되어 있거나 충분히 활용되지 않는다면 **새 추론 기능을 구현하기보다 기존 Thinking을 명시적으로 켜는 것이 필요할 수 있다.** 동일 입력·모델·prompt·context에서 ON/OFF를 비교하고, 출력 완성도·정확성·토큰 사용량·지연시간을 근거로 채택 여부를 판단한다. 현재 활성 상태와 개선 효과는 미검증이다.
- **Decision gate:** 16K의 실제 실행 결과로 초기 운용 가능 여부를 판단하고, 32K는 GPU 메모리 여유·GPU 적재·지연시간·schema 통과 및 의미적 품질을 확인한 경우에만 채택을 검토한다. 문서 기록만으로 Ollama·앱 설정을 변경하거나 검증 완료를 주장하지 않는다.

## Work Plan

1. **Baseline 및 oracle 고정.** Representative input, deterministic facts, 기존 `RemediationDraft`, 기대할 수 있는 정확한 해석, 제공되지 않은 evidence를 사례별로 고정한다. 기존 provider output을 정답으로 사용하지 않는다.
1. **최소 대표 사례와 negative control.** 다음 구별력을 가진 작은 fixture 집합을 만든다. 중복 fixture를 늘리기보다 서로 다른 실패를 식별하도록 설계한다.
   - `null_spike`: baseline `0.01`, current `0.21`, delta 약 `0.20`, threshold `0.1` → **1%에서 21%, 20 percentage points 증가, threshold 10 percentage points**. 상대 증가율을 사용한다면 2000%다.
   - Baseline `0` 및 다른 threshold: 상대 변화율이 정의되지 않는 상황과 threshold 단위를 구별한다.
   - Context sufficient / missing: 확인되지 않은 원인·검증 결과를 지어내지 않는지 판별한다.
   - Draft with / without backfill: 존재하지 않는 조치를 비판하는 오류를 탐지한다.
   - Known wrong-number, copied-example, restatement, unsupported-cause output을 negative control로 두어 평가·검증의 판별력을 먼저 확인한다.
1. **최소 후보 설계.** Task-specific 문구가 없는 shape-only 예시, 명시적인 비율·단위·근거 사용 지침을 우선 비교한다. 숫자 표현을 결정적 코드로 제공하는 방안은 prompt-only 대안이 부족할 때에만 projection, byte bound와 Spec 영향까지 검토한다. 변경한 prompt는 새 version으로 식별하고 기존 `v1`/`v2` replay·digest를 보존한다.
1. **반복 가능한 검증.** 관련 기존 fixture 및 테스트에 회귀를 연결하고, 단위 계산과 계약 검사를 수행한다. 예시 문구 exact match는 품질 신호로 기록할 수 있으나 정당한 공통 표현을 runtime에서 일괄 거부하지 않는다.
1. **동일 조건의 live 비교.** 하나의 clean candidate revision에서 `v2` baseline과 candidate를 동일 case/version/facts, model, active context, runtime cap으로 실행한다. 호출 전 반복 횟수·비용 한도를 정하고 전 시도, 실패, exclusion, prompt/output digest, latency와 usage를 남긴다. 과거 #278의 호출은 동일 revision 비교의 baseline을 대체하지 않는다.
1. **Human 평가와 채택 판단.** 사람이 `rubric_v1`의 `added_value`, `actionability`, `evidence_awareness`, `uncertainty_handling`, `prioritization`에 각각 0–2점과 근거를 기록한다. 기존 `compare_review_value()`에 연결해 accept/reject/no_change를 결정하고 관련 focused checks·최종 CI·독립 검토를 수행한다.

## Acceptance

- **Numeric fidelity:** 독립 oracle의 수치·단위·threshold와 일치하며 baseline 0에서 정의되지 않은 상대 증가율을 생성하지 않는다.
- **Context fidelity:** 제공되지 않은 root cause·validation result를 확정하지 않으며 실제 draft에 없는 조치를 비판하지 않는다.
- **Added utility:** 단순 재서술·예시 복사를 넘어, 다음 확인 우선순위와 결과에 따라 달라지는 사람의 판단을 구체적으로 제시한다.
- **Comparable evidence:** 동일 revision/조건과 output identity의 비교를 검증할 수 있다. 불일치 시 `blocked` 또는 `inconclusive`이며 임의 채택하지 않는다.
- **Human authority:** 다섯 항목을 사람이 근거와 함께 평가하지 않았다면 utility 완료를 주장하지 않는다.
- **Compatibility:** closed schema, structured-fact guard, read-only/advisory boundary, sanitized provenance, typed failure, `v1`/`v2` replay를 보존한다.

## Boundaries and Decisions

- 범위는 **output quality, 이를 평가하는 최소 사례·절차, 확인된 결함의 회귀 방지**에 한정한다.
- Provider/router 추가, JSON repair/자동 재시도, raw response 저장·전송, 자동 LLM judge, 새 평가 플랫폼, approval/recovery 권한 변경, Langfuse 기본 활성화는 제외한다.
- 채택 기준·관찰값이 불분명한 prompt 반복 변경을 시작하지 않는다. Contract 변경이 필요해지면 해당 OpenSpec workflow에 반영한 뒤 구현한다.
- 착수 시 결정할 사항: **live 반복 예산**과 **실제 human rubric 평가 담당자·시점**. 두 항목이 정해지지 않으면 live comparison과 human utility 완료 여부는 미검증으로 남긴다.

## Next Action

대표 사례/독립 oracle과 negative control, 선택 가능한 v3 prompt 후보를 준비했다. 로컬 검증과 남은 일은 [결과 보고](01-report-output-quality-preparation.md)를 따른다. [평가 가이드](../../docs/development/review-ai-evaluation.md#baseline-and-candidate-comparison)에 따라 live 반복 예산과 실제 human 평가 담당자를 정하고, 깨끗한 같은 revision에서 v2/v3를 비교한다. 실제 출력 품질과 human utility가 확인되기 전에는 후보를 채택하지 않는다.
