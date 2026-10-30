---
type: guide
title: Review AI Human Review Guide
description: 가상 컨텍스트의 실제 한국어 답변을 Langfuse native 실험·비교·사람 평가로 검토하는 안내서입니다.
tags:
  - review-ai
  - output-quality
  - human-review
  - langfuse
---

# Review AI Human Review Guide

**검토할 것은 가상의 사고 정보를 받은 실제 모델의 답변이다.** 입력과 근거 검토 → 초안 비판 → 종합의 원문을 읽고 수치·근거·초안 해석과 다음 판단에 주는 가치를 평가한다. 이 검토에 실제 HMDA 적재나 dbt 실행은 필요하지 않다. 모델은 한국어 텍스트로 답하며 JSON은 코드가 만든다.

현재 실행·등록 절차의 정본 안내는 [Evaluation Guide](../../docs/development/review-ai-evaluation.md), 프롬프트 운영은 [Prompt Guide](../../docs/development/review-ai-prompts.md)다. 이 문서는 [PR #280](https://github.com/mols3131d/hmda-data-reliability/pull/280)의 사람이 읽을 검토 순서를 제공한다.

## Review Basis

- Execution: 이 PR의 현재 checkout과 실제 HEAD를 사용한다. 같은 환경 파일로 다른 checkout을 실행해도 이 구현을 쓰는 것은 아니다.
- Historical evidence: [이전 native 구현 보고서](12-report-review-ai-native-langfuse-delivery.md)의 검증은 해당 revision의 기록이다. 이번 중복 계층 제거 이후의 증거로 소급하지 않는다.
- Human evidence: 실제 서버의 Prompt·Dataset·experiment·UI와 사람이 입력한 품질 점수는 이 안내서 작성만으로 검증되지 않는다.

`completed`는 수집·저장 완료이며 사실성·유용성·승인이 아니다. SDK 반환이나 flush도 UI 표시나 사람 평가를 대신하지 않는다. 점수·Queue 완료를 GitHub Ready 전환·승인·병합으로 해석하지 않는다.

## Register Once And Run

저장소 최상위 디렉터리에서 [환경 예제](../../.env.example)를 참고해 `LANGFUSE_*`와 `OPENAI_BASE_URL`·`OPENAI_API_KEY`를 설정한다. 사용 중인 환경 파일을 덮어쓰거나 자격 증명을 문서·Git·로그에 복사하지 않는다. 기존 live/enable opt-in·SDK extra·과거 환경 선택은 없다.

처음 사용하는 Langfuse 프로젝트에서만 다음 등록을 실행한다. 이 명령은 remote Prompt·합성 Dataset에 쓴다. 모델 태그는 실제 서버에 설치된 값을 사용한다.

```bash
uv sync
uv run --env-file .env python -m hmda_reliability.review_ai.evaluation.setup \
  --model qwen3.5:4b-8k-local
```

Setup을 반복하면 새 prompt version이나 중복 Dataset item이 생길 수 있다. 이후 프롬프트 편집·label·점수 설정과 대기열은 Langfuse UI에서 관리하고 실험 전마다 setup을 실행하지 않는다. 기본 `production`의 세 chat prompt와 첫 prompt의 model·token·timeout config를 확인한다.

```bash
git rev-parse HEAD
uv run --env-file .env python -m hmda_reliability.review_ai.evaluation.experiment \
  --dataset hmda-review-ai-staged-v1 \
  --name human-review \
  --prompt-label production
```

같은 Dataset snapshot 비교가 필요하면 서버에 존재하는 UTC 시각을 `--dataset-version`으로 지정한다. 초기 세 사례는 직렬 실행하며 모두 성공하면 아홉 단계다. 단계 시작·종료는 stderr에 표시되고 SDK가 experiment 결과를 출력한다. 토큰 진행률·예상 완료 시각을 추정하는 heartbeat는 없다.

`OPENAI_BASE_URL`의 localhost는 이 SDK task 머신의 모델 주소다. Langfuse Cloud UI가 직접 모델을 호출하는 연결과 구분한다. Workflow 시작 전에 remote prompt를 못 읽으면 `prompt_unavailable`이며 로컬 seed를 대신 실행하지 않는다.

## Open The Actual Evidence

Langfuse Dataset의 해당 experiment run을 열고 사례별 output과 실제 generation을 확인한다. Generation input에는 실제 system 지시·canonical JSON·이전 history가 있고 prompt name/version·model·usage를 함께 볼 수 있다. 모델 응답이 반환된 경우 로컬 원문은 원격 output 갱신 전에 저장된다.

| Local artifact | What to inspect |
| --- | --- |
| `agentic-review/staged/<workflow_id>/workflow.json` | 실제 revision·canonical input·설정·prompt version·단계 상태·digest |
| `agentic-review/responses/<workflow_id>-<stage_id>.txt` | 공백·개행을 보존한 실제 UTF-8 답변 |
| 단계별 checkpoint | 응답 종료 이유·failure·시도·시간·원문 경로 |
| 같은 workflow의 `output.json` | 입력 facts와 고정 순서의 세 텍스트를 코드로 취합한 결과 |

저장 루트는 `HMDA_RELIABILITY_ARTIFACTS_DIR`다. Core status·workflow ID로 로컬 기록을 찾는다. 실패하면 마지막 단계의 `failure_code`와 raw부터 확인한다. 본문 반환 전 실패에는 raw가 없고 경로가 있어도 전체 완료는 아닐 수 있다. [실패 진단](../../docs/development/review-ai-evaluation.md#diagnose-a-failed-stage)을 따른다.

모든 stage의 `deterministic_facts`는 코드가 입력에서 복사한 값이다. 이 값이 맞아도 모델 설명이 틀릴 수 있으므로 원문을 직접 읽는다. 전체 원문이나 개인 절대 경로를 PR 문서에 붙여 넣지 않는다.

## Compare Input And Answer

[실행 사례](../../src/hmda_reliability/review_ai/evaluation/cases.json)의 `review_input`과 실제 전달된 `canonical_input`을 기준으로 읽는다. [독립 oracle·controls](../../tests/review_ai/evaluation/fixtures/output_quality_staged_v1.json)는 검토자 자료이며 모델의 정답·실제 응답·사람 점수가 아니다.

| Case | Numeric expectation | Evidence and draft |
| --- | --- | --- |
| `null-spike-missing-context` | 1% → 21%, 증가 20%p, 기준 10%p, 상대 증가율 2000% | Profile만 제공. 원인·dbt 검사 완료는 미확정. 원천 점검은 이미 초안에 있고 backfill 제안은 없음 |
| `null-spike-zero-baseline` | 0% → 12%, 증가 12%p, 기준 5%p, 상대 증가율 정의 불가 | 기준값 0으로 나누거나 임의 상대 증가율을 만들면 안 됨 |
| `null-spike-supplied-context-backfill` | 1% → 21%, 증가 20%p, 기준 10%p | Metadata·관계·실패한 not-null 검사 제공. 원인 미확정. Backfill은 원인 확인·사람 승인 후 필요성과 범위를 검토하는 초안 |

`delta=0.19999999999999998`은 입력의 부동소수점 보존 표현이다. 설명에서 20%p로 읽을 수 있다. 20%p 증가·2000% 상대 증가·10%p 탐지 기준을 섞지 않는지 확인한다.

1. 근거 검토에서 관측 사실·추정·누락을 구분하며 없는 원인이나 검증 완료를 만들지 않는지 읽는다.
1. 초안 비판에서 실제 조치를 읽고 이미 있는 원천 점검을 새 제안처럼 반복하거나 없는 backfill을 전제하지 않는지 읽는다.
1. 종합에서 앞선 오류를 반복하지 않고 확인 순서·결과별 다음 판단을 설명하는지 읽는다.
1. 모든 단계에서 한국어 설명·원본 식별자·수치를 보존하며 승인이나 실행을 이미 마쳤다고 주장하지 않는지 확인한다.

## Score In Langfuse

사람이 UI에서 아래 기준의 categorical 0·1·2를 설정하고 평가 대상 trace를 Annotation Queue에 넣는다. 작성 방법은 [현재 평가 절차](../../docs/development/review-ai-evaluation.md#human-evaluation)를 따른다. 점수 의미와 실제 문장을 함께 판단한다.

| Criterion | 0 | 1 | 2 |
| --- | --- | --- | --- |
| `added_value` | 입력·초안 반복 | 유용한 누락·관찰 하나 | 추가 분석이 다음 판단을 바꿈 |
| `actionability` | 막연한 확인 요청 | 대상을 특정 | 방법과 결과별 다음 행동 연결 |
| `evidence_awareness` | 없는 근거·원인 단정 | 제공 근거와 한계 인정 | 실제 근거 활용·부족한 근거 구분 |
| `uncertainty_handling` | 미확정을 사실로 표현 | 불확실성 표시 | 사실·가설·판단 영향 구분 |
| `prioritization` | 순서 없는 나열 | 먼저 볼 항목 지정 | 이유와 결과별 분기 설명 |

오류가 있으면 단계·문장과 올바른 근거를 사유에 남긴다. Native comment는 선택 기능이며 프로젝트가 모든 기준·동일 작성자·non-empty 사유를 다시 읽는 `--check` 판정기는 없다. 사람의 판단 이유를 설명할 기록은 native annotation에 남긴다. 높은 총점으로 사실 오류를 숨기지 않고 출력 실패·자료 누락은 보류한다.

## Compare And Decide

Native compare에서 같은 Dataset version·평가 기준과 양쪽 실제 prompt version·model·코드 revision을 확인한다. 의도한 코드 변경이면 SHA 차이를 허용하고 그 외 조건이 다르면 직접 개선 비교를 보류한다. 실패·누락·미평가 사례를 제외해 결과를 좋게 보이게 하지 않는다.

사람이 채택·거절·유지 의견과 사유를 남긴다. 점수 평균·Queue 완료·테스트 통과가 결정을 자동 생성하지 않는다. Baseline이 없으면 단일 출력만 평가한다. 실제 품질 평가와 GitHub의 Ready·승인·병합은 각각 별도 사람 결정이다.
