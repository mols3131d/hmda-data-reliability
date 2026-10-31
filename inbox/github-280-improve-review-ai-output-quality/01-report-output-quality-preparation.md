---
type: report
title: Review AI Output Quality Preparation
description: PR 280의 v3 후보·품질 corpus 구현과 검증 근거 및 남은 live·human 평가를 인계합니다.
tags:
  - review-ai
  - evaluation
  - output-quality
status: in-progress
---

# Review AI Output Quality Preparation

**로컬 구현은 완료했으며 v3는 평가 전 후보다. PR 전체 acceptance는 아직 충족하지 않았다.** 다음 단계에는 live 호출 예산과 실제 사람 평가 담당자가 필요하다. 이번 작업의 provider 호출과 실제 human assessment는 각각 0회다.

## Revision and Scope

- PR: [#280](https://github.com/mols3131d/hmda-data-reliability/pull/280), branch `agent/feat/improve-review-ai-output-quality`, Draft 유지.
- Remote base: `1794d3dc3473d63c1b2b686e96279471e0904f87`; 시작 head: `425466daf95993bd182a81931f04184556681343`.
- 구현·검증 기준: `4d5c0f9cb253bd07b3f2619af6f64e375c71a0da`. 이 보고서 이후 문서 commit은 해당 코드 검증과 구별한다. 최종 head 및 CI는 PR의 현재 상태를 확인한다.
- 기존 두 evaluation/Langfuse Change는 로컬 구현 task가 완료된 별도 owner다. 이번 변경은 [review-ai-ground-output-explanations](../../openspec/changes/review-ai-ground-output-explanations/proposal.md)의 3개 로컬 구현 결과를 소유한다.

## Result and Evidence Boundary

[`output_quality_v1.json`](https://github.com/mols3131d/hmda-data-reliability/blob/24b5f26833121de853ce0787c0bb67c3ad25673d/tests/review_ai/evaluation/fixtures/output_quality_v1.json)에 portable 입력 3개, 독립 수치 oracle과 합성 출력 10개를 고정했다. 기존 사례, baseline-zero/다른 threshold, 추가 evidence/backfill 유무를 구별한다. 기존 static comparison golden은 보존했다.

| Check | Observed result |
| --- | --- |
| Independent numeric oracle | 1% → 21%, 증가 20 percentage points, threshold 10 percentage points, 상대 증가율 2000%; 0% → 12%에서는 상대 증가율 정의 불가 |
| Structured guard | 올바른 structured facts를 가진 wrong-number prose, copied-example, restatement, unsupported-cause, nonexistent-draft-action 및 baseline-zero 상대 증가율 오답도 accepted |
| Contrast | Structured current rate를 바꾼 control은 `deterministic_contradiction`으로 rejected |
| Human utility API | 점수·근거·identity·digest와 비교 조건을 검증한다. Prose를 자동 채점하거나 사람의 결정을 생성하지 않는다. |

합성 control의 결함 label은 agent가 작성한 검토 보조 자료다. 수치 계산·계약 검증과 달리 의미적 label이나 positive output을 실제 사람의 평가 결과로 취급하지 않는다. Exact example match도 제한된 복사 신호다.

선택 가능한 [`v3` instruction](../../src/hmda_reliability/review_ai/prompt/README.md#composition)은 내용 예시를 제거하고 단위·zero baseline·실제 evidence/draft·결과에 따른 다음 판단을 안내한다. `v1`/`v2` instruction과 digest, Python 기본 `v1`, live 기본 `v2`, canonical projection, structured validator 및 evaluation serialization을 보존했다. v3의 실제 준수율·정확성·utility 개선은 입증하지 않았다.

## Validation

| Check | Result |
| --- | --- |
| Test first | v3 미지원 상태에서 관련 4개 실패와 historical 기준 7개 통과를 확인한 뒤 구현 |
| Domain regression | `python -m pytest -q tests/review_ai tests/runtime_ai`: **261 passed, 1 skipped** |
| Skip | Optional Langfuse SDK media smoke의 dependency 미설치. 실제 Langfuse ingestion/UI를 검증하지 않음 |
| Static | Review AI source/tests Ruff check·format·ty, 전체 Tach 통과 |
| Contracts and documents | 전체 OpenSpec strict 23개, 변경 Markdown, Inbox validator, JSON Biome, `git diff --check` 통과 |
| Independent review | `review-lead`가 quality/adversarial 정적 검토를 조정해 **clear**. Confirmed current_required finding 없음. 실행 결과를 독립 재실행하거나 live 품질을 승인한 검토는 아님 |

검토 기준은 시작 head 위의 source/test/spec/guide diff다. Tracked target diff fingerprint는 `df22a2a2a1613c49be6d1f2b759f45fcd1783ad4`, 새 test/corpus blob은 각각 `ff59c6dbac2625b8bf945baf70600a128faaca73`, `7a070ba40eb12c4d5fe296f99dde9ff433bc906c`다. Inbox 진행 문서는 해당 독립 검토 대상에서 제외했다.

## Remaining Work

1. **Live budget:** 동일 모델·양자화·실제 context·Thinking 조건에서 3개 사례 × v2/v3 × 2회 = 최대 12회 prompt 비교를 제안했으나 아직 확정되지 않았다. Context/Thinking 비교의 추가 호출은 별도 예산이다. Retry와 실패를 포함해 모든 시도를 남긴다.
1. **Provider conditions:** 기존 결정인 16K 우선·32K 후속 검증은 유지하되 이번 작업에서 Ollama 설정을 변경하거나 GPU 메모리·offload·지연시간을 측정하지 않았다. 실제 활성 상태를 먼저 확인한다. 모델 카드의 기본값만으로 설치된 Ollama 상태를 추정하지 않는다.
1. **Human assessment:** 담당자가 각 accepted output을 독립 oracle·실제 evidence/draft와 대조하고 `rubric_v1` 다섯 criterion의 0–2점과 근거를 기록한다. 같은 revision의 exact output identity로 비교하고 사람이 `accept`/`reject`/`no_change`를 결정한다.

실행 방법과 전 시도 기록·평가 절차는 [Evaluation Guide](../../docs/development/review-ai-evaluation.md#baseline-and-candidate-comparison)를 따른다. 예산·평가 담당자가 정해지기 전에는 live/human proof를 미검증으로 남긴다. 따라서 전체 PR의 `review readiness`는 `not_ready`이며 로컬 구현 검토의 `clear`와 구별한다. Ready 전환·approval·merge는 수행하지 않았다.
