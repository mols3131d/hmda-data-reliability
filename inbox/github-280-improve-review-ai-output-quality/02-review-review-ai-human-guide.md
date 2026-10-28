---
type: review
title: Synthetic Context and AI Response Review
description: PR 280의 가상 입력과 실제 모델 응답을 나란히 읽고 사람이 품질을 판단하기 위한 검토 자료입니다.
tags:
  - review-ai
  - output-quality
  - human-review
---

# Synthetic Context and AI Response Review

검토 대상은 **가상 사고 정보를 AI에게 주었을 때 나온 응답**이다. 사람이 입력 context의 적절성을 확인하고, 실제 응답이 그 정보에 맞으며 판단에 도움이 되는지 검토한다. 실제 데이터를 적재하거나 profile·dbt 검사를 수행하는 작업이 아니다. 아래의 테이블·검사 결과·대응 초안은 모두 모델에게 주는 가상 상황의 구성 요소다.

응답 보존 수정 후 새 실행은 검증에 실패해도 실제 모델 본문을 `response_path`에 저장한다. 재실행과 검증 결과는 [응답 보존 보고](03-report-review-ai-response-retention.md)를 따른다. 아래 과거 응답의 보존 한계는 수정 전 실행에 해당한다.

앞선 안내서는 코드·CI 검토를 중심에 두어 이 목적을 충분히 돕지 못했다. 사용자 정정에 따라 입력 → 실제 응답 → 사람의 판단 순서로 다시 구성했다.

## Context Given to the AI

세 사례의 공통 대상은 `raw.hmda_loans`의 2025 partition, `income` 컬럼이다. [입력 자료](../../tests/review_ai/evaluation/fixtures/output_quality_v1.json)에서 각 사례의 `review_input`을 읽어 기존 prompt projection으로 전달한다. `oracle`, `human_review_questions`, `controls`는 검토자용 자료이며 모델에게 주는 정답이나 실제 응답이 아니다.

| Case | AI에게 제공하는 가상 상황 | 제공하는 대응 초안 |
| --- | --- | --- |
| 정보 부족 | 결측 비율 `0.01` → `0.21`, 증가 탐지 기준 `0.10`. Profile 근거만 있고 테이블·관계·dbt 결과와 원인 정보는 없음 | 원천 컬럼·partition 점검, not-null test 추가, profile·dbt 재실행과 결측률 확인. Backfill 없음 |
| 기준값 0 | 결측 비율 `0` → `0.12`, 증가 탐지 기준 `0.05`. 나머지 정보는 첫 사례와 같음 | 첫 사례와 같은 점검·재검증 초안. Backfill 없음 |
| 정보 추가 | 첫 사례와 같은 비율에 테이블 정보·upstream/downstream·실패한 not-null test를 추가. 원인은 여전히 미확정 | 기존 점검·재검증에 더해 원인 확인과 사람 승인 후 backfill의 필요성과 범위를 검토하자는 조건부 제안 |

세 번째 사례에는 구체적으로 다음을 준다.

- 테이블: `income`, `loan_amount` 컬럼은 각각 `DOUBLE`, schema hash는 `sha256:stable`.
- 관계: upstream은 `source.hmda_2025`, downstream은 `analytics.hmda_income`; `source.hmda_2025`에서 `raw.hmda_loans`로 연결됨.
- 검사 결과: `not_null_income`의 상태는 `fail`, artifact ID는 `fixture-dbt-run-2025`.
- Backfill: 원인 확인과 사람의 승인을 전제로 필요성·범위를 검토한다는 초안이며 실행 지시나 승인 완료가 아님.

여기서 사람이 먼저 볼 것은 **이 정도 정보로 AI에게 무엇을 기대할 수 있는가**다. 정보 부족 사례에서는 불확실성을 인정하고 필요한 확인을 제안해야 한다. 정보 추가 사례에서는 제공된 관계와 실패 관측을 활용하되 원인을 지어내지 않아야 한다.

## Actual AI Responses Available

[PR 280 준비 보고](01-report-output-quality-preparation.md)는 새 provider 호출을 0회로 기록한다. 현재 작업 폴더에서 새 v2/v3 응답 기록도 찾지 못했다. Corpus의 10개 출력은 수작업 합성 예시이므로 실제 AI의 답으로 채점하지 않는다.

지금 확인할 수 있는 과거 실제 모델 응답은 [PR 278의 보존된 발췌](../github-278-resolve-review-ai-live-schema/04-plan-review-ai-output-quality-follow-up.md#confirmed-numeric-error)다. 전체 응답 파일은 이 작업 폴더에 없으므로 아래 내용으로 한정해 읽는다. 이는 당시 v2 실행이며 PR 280의 새 v3 결과가 아니다.

| Given context | Retained actual response | 사람이 확인할 점 |
| --- | --- | --- |
| 비율 `0.01` → `0.21`, 증가 탐지 기준 `0.10` | `qwen2.5-coder:7b`가 `increased by 199.99999999999998%`, `threshold of 100%`라고 설명 | 정확한 설명은 1% → 21%, 증가 20%p, 기준 10%p. 상대 증가율을 쓰면 2000% |
| 원천 점검을 이미 제안한 초안, backfill 없음 | 같은 응답이 `Check source completeness first.`, `Confirm the cause before backfill.` 등 v2 예시 네 문장을 그대로 사용 | 실제 상황을 검토해 얻은 추가 제안인지, 예시를 반복하거나 초안에 없는 조치를 전제한 것인지 |

해당 호출은 `ar-20261028-a613ff9cd836`, 당시 revision은 `babea53600c48d63049c2fa83c85ccfeb0a1c976`다. 위 문구는 보존 문서에서 읽은 발췌이며 이번 세션에서 모델을 다시 실행해 얻은 답이 아니다.

## Review the Next Model Response

새 실제 응답을 확보하면 각 사례의 입력 옆에 응답을 놓고 다음을 순서대로 판단한다.

1. **입력을 정확히 읽었는가?** 비율·변화량·탐지 기준을 구별하는가? 기준값 0에서 정의되지 않는 상대 증가율을 만들어내지 않는가?
1. **주어진 정보 안에서 말하는가?** 가상 context에 없는 원인이나 검사 완료를 주장하지 않는가? 제공한 실패 관측·관계 정보는 적절히 사용하는가?
1. **실제 초안을 검토하는가?** 이미 제안된 내용을 반복하거나 없는 backfill을 비판하지 않는가?
1. **다음 판단에 도움이 되는가?** 무엇을 먼저 확인할지, 확인 결과에 따라 조사 방향이 어떻게 달라질지 구체적으로 제시하는가?

예를 들어 “원인을 확인하라”와 “동일 partition의 원천에서도 결측이 증가했으면 수집 경로를, 원천이 온전하면 변환 경로를 우선 조사하라” 사이에 추가 가치가 있는지 사람이 판단한다. 이 문장은 설명용이며 새 모델 응답을 대신하지 않는다.

실제 응답을 읽은 뒤 사람이 `rubric_v1`의 `added_value`, `actionability`, `evidence_awareness`, `uncertainty_handling`, `prioritization`에 각각 0–2점과 이유를 남긴다. 이번 안내서는 점수나 채택 결정을 작성하지 않았다. 실행·기록의 상세 절차는 [평가 가이드](../../docs/development/review-ai-evaluation.md#baseline-and-candidate-comparison)를 따른다.

## Evidence Boundary

이 문서는 가상 입력·수작업 예시·과거 실제 응답 발췌·아직 없는 새 응답을 구별한다. 코드 검사와 CI는 [구현 보고](01-report-output-quality-preparation.md)의 배경 근거이며 실제 응답의 유용성을 대신하지 않는다. 새 모델 응답에 대한 사람 검토는 아직 시작하지 않았다.
