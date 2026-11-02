---
type: plan
title: "Review AI Output Quality Follow-up"
description: "PR 278의 실제 실행에서 남은 수치 설명 오류, 예시 복사와 낮은 추가 가치를 다음 PR에서 재현·평가·개선하기 위한 인계 계획입니다."
tags:
  - review-ai
  - evaluation
  - output-quality
status: proposed
---

# Review AI Output Quality Follow-up

## Goal and Starting Point

다음 PR의 목표는 **Review AI가 입력에 맞는 정확하고 유용한 설명을 제공하는지 검증하고, 확인된 품질 결함을 개선하는 것**이다. 제안 제목은 `Review AI 출력의 수치 정확성과 검토 가치 개선`이다. PR 번호와 구현안은 아직 정하지 않았다.

PR [#278](https://github.com/mols3131d/hmda-data-reliability/pull/278)은 schema 실패 진단, v2 instruction과 회귀 방지를 완료했다. 최종 코드·live 근거는 `babea53600c48d63049c2fa83c85ccfeb0a1c976`이며 이후 변경은 Inbox 문서다. `accepted`는 출력 계약·structured-fact guard·provenance 통과를 뜻한다. 자유 서술의 정확성이나 human utility까지 입증하지 않는다. 전체 검증과 호출 이력은 [결과 보고](03-report-review-ai-schema-resolution.md)를 따른다.

이 문서는 사용자가 요청한 다음 PR 준비 자료이며 새 canonical requirement가 아니다. 후속 구현은 #278이 머지된 최신 `main`에서 시작하고 실제 base SHA와 active OpenSpec Change의 소유 범위를 다시 확인한다. 사람의 다섯 항목 utility 평가는 아직 수행되지 않았다.

## Retained Reproduction Evidence

### Case and Execution Basis

기존 [live harness](../../scripts/run_agentic_review_live.py)의 synthetic `null_spike` 사례를 사용했다. 재현의 정답은 입력의 deterministic facts·Evidence·RemediationDraft이며 이전 모델 출력이 아니다.

| Input | Retained value |
| --- | --- |
| Target | `raw.hmda_loans`, partition `2025`, column `income` |
| Identity | `inc_null_spike_raw_hmda_loans_2025_income`; `ev_null_spike_raw_hmda_loans_2025_income` |
| Facts | baseline `0.01`, current `0.21`, delta `0.19999999999999998`, threshold `0.1` |
| Missing context | `table_metadata`, `catalog`, `dbt_artifact`; root cause unconfirmed |
| Existing draft | `inspect_source_columns`, `add_dbt_not_null_test`, `validate_source_partition` |
| Existing validation | `rerun_profile_snapshot`, `rerun_dbt_build`, `validate_null_rate`; `backfill_actions=[]` |

최종 두 호출은 v2, temperature `0`, output cap `4096`, timeout `180s`, retry `0`, prompt/output byte cap `65536/32767`, Langfuse off였다. Prompt digest는 `sha256:3636e263750d9e264df2142cea4b4bb6bc16af70d84f60402dcd0a6893b37322`다.

| Model | Invocation | Result | Latency / tokens |
| --- | --- | --- | --- |
| `qwen2.5-coder:7b` | `ar-20261028-a613ff9cd836` | `accepted` | `17.90s`; prompt/completion `1390/503` |
| `qwen3.5:4b-8k-local` | `ar-20261028-ce7a6c327159` | `accepted` | `74.67s`; prompt/completion `5088/616` |

Qwen3.5는 실제 provider의 `num_ctx=8192`를 확인한 변형이다. 기본 active context `4096`에서는 빈 본문과 `finish_reason=length`를 관찰했다. Output cap만 높인 실행을 같은 조건으로 취급하지 않는다. 위 결과는 모델별 최종 1회이며 반복 성공률이나 성능 benchmark가 아니다.

아래는 synthetic invocation의 저장된 `parsed_output`에서 문제를 설명하는 짧은 발췌다. Raw provider response는 보존하지 않았다. Local record는 ignored artifact이므로 새 checkout에서 사용할 수 있다고 가정하지 않는다. 이 입력·버전·호출 identity와 [보고서](03-report-review-ai-schema-resolution.md)의 조건을 재현 출발점으로 사용한다.

### Confirmed Numeric Error

Qwen2.5의 finding에는 `increased by 199.99999999999998%`와 `threshold of 100%`라는 잘못된 설명이 있었다. 같은 출력의 structured facts는 입력과 일치해 guard를 통과했다.

정확한 해석은 **1% → 21%, 증가 폭 20 percentage points, threshold 10 percentage points**다. 상대 증가율을 표현한다면 `(0.21 - 0.01) / 0.01 × 100 = 2000%`다. 비율, percentage points와 상대 변화율을 구분하고 부동소수점 표현을 그대로 설명에 노출하지 않아야 한다.

### Example Copying and Utility Gap

Qwen2.5의 네 utility description은 v2 [instruction](../../src/hmda_reliability/review_ai/prompt/guidance/utility_examples.md)의 예시와 모두 같았다. 예를 들어 `Check source completeness first.`와 `Confirm the cause before backfill.`을 그대로 사용했다. 이 사례의 draft에는 backfill action이 없었다. 복사 금지 문구만으로 예시의 내용 유입을 막지 못했다는 관찰이다.

Qwen3.5는 제공된 context gap을 반영했지만 source completeness 확인과 원인 확인 등 일반적인 제안이 중심이었다. Existing draft보다 어떤 판단을 더 돕는지는 입증하지 못했다. Backfill/schema change에 대한 비판도 실제 draft의 어느 제안과 연결되는지 검토해야 한다. 이는 후속 평가 대상이며 formal human rubric 점수나 전체 모델의 품질 결론은 아니다.

## Proposed Work

1. **Evaluation baseline부터 고정한다.** [기존 utility API](../../src/hmda_reliability/review_ai/evaluation/value.py), [control fixtures](../../tests/review_ai/evaluation/test_utility_evaluation.py)와 [Evaluation Guide](../../docs/development/review-ai-evaluation.md)를 재사용한다. 현재 v2를 baseline으로 두고 사례별 입력·draft·정답 근거·평가 질문을 먼저 남긴다. 기존 positive/restatement/hedging control을 실제 provider 품질 근거로 오인하지 않는다.
1. **작은 대표 사례 집합을 만든다.** 위 수치 오류 사례에 더해 다른 rate/threshold, baseline `0`의 상대 변화율, 제공된 context가 충분한 경우와 부족한 경우, backfill이 없는 draft와 있는 draft를 포함한다. 정답은 독립 계산과 제공된 근거에서 만든다. Known wrong-number/copied-example/restatement/unsupported-cause output을 negative control로 두고, 평가가 이 차이를 드러내는지 먼저 확인한다.
1. **수정안을 비교한 뒤 최소 구현을 선택한다.** 우선 task-specific 문장을 제거한 shape 예시와 더 명확한 단위·근거 사용 instruction을 비교한다. 필요하면 결정적 코드가 수치 표시를 계산해 제공하는 방식을 검토하되 input projection·byte bound·Spec 영향을 확인한다. 실제로 제공된 Evidence만 context에 추가한다. 변경한 instruction은 새 prompt version으로 식별하고 v1/v2 replay와 digest를 보존한다.
1. **품질 재발을 시스템에서 드러나게 한다.** 대표 사례와 부정 사례를 repository fixture로 남기고 단위 계산·버전·계약 검사 및 반복 가능한 평가 절차를 기존 suite에 연결한다. 알려진 예시 문구의 기계적 일치는 복사 신호로 기록하되 정당한 공통 표현까지 일괄 거부하지 않는다. 임의의 자연어 전체를 판정하는 새 runtime guard는 별도 근거 없이 도입하지 않는다.
1. **같은 조건으로 baseline/candidate를 실행한다.** 하나의 깨끗한 candidate revision에서 기존 v2와 새 version을 모두 실행해 비교 API의 same-revision 조건을 충족한다. 모델·active context·입력·runtime cap을 맞추고 반복 횟수와 비용 한도를 실행 전에 정한다. 모든 호출과 실패·제외 이유를 기록하고 유리한 결과만 선택하지 않는다. 과거 #278 출력은 결함 재현 근거이며 새 비교의 동일 revision baseline을 대신하지 않는다.
1. **사람의 판단과 구현 검증을 마친다.** 아래 완료 기준으로 결과를 검토하고 source 변경에 필요한 focused suite·static checks·독립 review와 최종 head CI를 수행한다. 출력 품질 개선이 확인되지 않으면 schema 통과만을 이유로 후보를 채택하지 않는다.

## Acceptance and Evidence

| Check | Required evidence |
| --- | --- |
| Numeric fidelity | 알려진 오답이 평가에서 드러나고, 후보의 수치·단위·threshold 설명이 사례별 독립 정답과 일치한다. Baseline `0`에서 정의되지 않은 상대 변화율을 만들지 않는다. |
| Context fidelity | 원인·검증 결과를 만들어내지 않으며 draft에 없는 조치를 있는 것처럼 비판하지 않는다. 주장과 실제 제공된 근거를 대조할 수 있다. |
| Added utility | 기존 draft를 넘어 무엇을 먼저 확인하고 그 결과에 따라 어떤 판단이 달라지는지 사람에게 설명할 수 있다. 예시 복사와 단순 재서술은 개선 근거로 채택하지 않는다. |
| Comparable runs | 같은 case/version/facts, implementation revision과 runtime 조건의 baseline/candidate invocation·prompt/output digest, 전체 시도 수와 latency/usage를 남긴다. Attribution이 맞지 않으면 `blocked`/`inconclusive`로 기록한다. |
| Human assessment | `rubric_v1`의 `added_value`, `actionability`, `evidence_awareness`, `uncertainty_handling`, `prioritization` 각각에 사람이 0–2 score와 rationale을 남기고 기존 comparison API에 연결한다. 실제 human evidence가 없으면 미완료로 표시한다. |
| Contract preservation | Closed schema, structured-fact guard, read-only boundary, immutable provenance, 실패 시 typed result, v1/v2 replay와 원문 비노출 회귀를 유지한다. |

Known defect에 대한 offline 검사는 평가 장치의 작동 근거다. 새 live output의 의미적 정확성이나 human utility를 자동으로 증명하지 않는다. 자동 LLM judge, agent의 자체 점수 또는 Langfuse UI 완료 표시를 human assessment로 대체하지 않는다. 평가 authority와 자유 서술 경계는 정본 [Spec](../../openspec/specs/reliability-agentic-review/spec.md)을 따른다.

## Scope and First Action

다음 PR은 output quality와 그 평가·회귀 방지에 한정한다. 새 provider/router, 자동 재시도·JSON repair, approval/recovery 권한 확대, raw response 저장·전송, 별도 평가 플랫폼 구축은 포함하지 않는다. Langfuse projection은 현재 optional opt-in을 유지하며 이 인계를 이유로 활성화하지 않는다.

후속 담당자는 머지된 `main`의 실제 SHA를 확인한 뒤 위 대표 사례와 baseline 평가 계획부터 작성한다. Active Change와 충돌을 확인하고, 정본 계약을 바꾸는 선택은 해당 OpenSpec 계획에 반영한 뒤 구현한다. 성공 기준을 정하지 않은 prompt 반복 수정부터 시작하지 않는다. 현재 blocker는 없으며 실제 human assessment를 완료할 담당자·시점과 live 반복 예산은 다음 PR에서 정해야 한다.
