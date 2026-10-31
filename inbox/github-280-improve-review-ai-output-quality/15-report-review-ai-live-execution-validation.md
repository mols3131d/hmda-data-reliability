---
type: report
title: Review AI Live Execution and Validation Delivery
description: 실제 Langfuse Cloud 및 Ollama 모델을 연동한 프롬프트 등록, 단계별 실험 검증, 원문 보존 확인 및 PR 갱신 결과를 기록합니다.
tags:
  - langfuse
  - review-ai
  - evaluation
  - validation
---

# Review AI Live Execution and Validation Delivery

실제 Langfuse Cloud 및 로컬 Ollama(`qwen3.5:4b-8k-local`) 환경을 연동하여 프롬프트 등록, 3단계 대화 실험 실행, 로컬 원문 보존 검증을 수행하고 GitHub PR #280 본문에 실증 근거를 반영했습니다.

## Execution Overview

- **환경 설정**: 워크스페이스 상위 `.env`의 `LANGFUSE_*` 인증 정보를 로컬 worktree `.env`에 동기화.
- **실행 대상**: 로컬 Ollama `qwen3.5:4b-8k-local`, Langfuse Cloud Dataset `hmda-review-ai-staged-v1`.
- **코드 기준**: HEAD `fb6cfb8a9fc5500b51c5ef188ab8312fefb6b8a1`.

## Validation Findings

### Prompt and Dataset Registration

`uv run --env-file .env python -m hmda_reliability.review_ai.evaluation.setup --model qwen3.5:4b-8k-local` 1회 실행으로 다음 자산을 Langfuse Cloud에 정상 등록했습니다.

- 한국어 seed text 프롬프트 9개 등록
- 단계별 chat 프롬프트 3개(`evidence_review`, `draft_critique`, `synthesis`, `production` label) 등록
- 합성 Dataset `hmda-review-ai-staged-v1` 및 3개 검토 사례 item 등록

### Initial Run: Fault Isolation and Empty Raw Retention

초기 설정(`max_tokens=1024`, `prompt_version=1`)으로 실행한 1차 실험(`staged-review`, Run `832021d5-78ec-4434-b99c-5d2c2cd9b5a2`) 결과입니다.

- 로컬 워크플로: `sr-20261031-f82419892fdb`, `sr-20261031-2c5f3de57823`, `sr-20261031-2e90fee209fc`
- 3개 사례 모두 `evidence_review` 단계에서 Qwen3.5 Thinking 과정 중 1,024 토큰을 모두 소진했습니다.
- `finish_reason="length"`, `content_bytes=0`으로 인해 `status="validation_failed"`, `failure_code="stage_response_empty"` 발생.
- 실패 판정 전 0-byte 원문 파일(`.txt`)과 checkpoint JSON이 로컬 provenance 계약대로 보존됨을 확인했습니다.

### Second Run: Full Stage Completion

코드 변경 없이 Langfuse Prompt Management에서 `hmda-review-ai/evidence_review` 프롬프트 설정을 `version=2`(`max_tokens: 4096`, `production` label)로 갱신한 뒤 2차 실험(`staged-review-4k`, Run `2b35cb66-3dab-4719-9caf-30fd446cc54b`)을 실행했습니다.

3개 사례, 총 9개 단계가 모두 정상 완주(`status="completed"`)되었으며 로컬 원문 및 코드 취합 JSON 저장을 확인했습니다.

| Case ID | Workflow ID | 수치 및 의미 검토 결과 |
| --- | --- | --- |
| `null-spike-supplied-context-backfill` | `sr-20261031-97ff7445766d` | 1% → 21%, 20%p 증가(기준 10%p) 구분. 제공된 `table_metadata`, `catalog`, `dbt_artifact`(fail) 인용. 근본 원인 미확정 명시 및 백필 초안 검토 전 사전 원인 조사 우선순위 제안. |
| `null-spike-zero-baseline` | `sr-20261031-5f57be605fb9` | 0% → 12%, 12%p 증가(기준 5%p) 구분. **"기준 null rate가 0이므로 상대적 증가율은 정의되지 않습니다"** 명시. 빈 `backfill_actions` 오독 없음. |
| `null-spike-missing-context` | `sr-20261031-cfa40601f402` | 1% → 21%, 20%p 증가(기준 10%p)와 상대 증가율 2,000% 구분. 누락된 3개 근거 식별 및 계획된 검증 조치와 완료 결과 명확히 분리. |

### API Deprecation Notice

Langfuse Cloud 신규 조직에서는 레거시 엔드포인트 `GET /api/public/datasets/{name}/runs` 호출 시 `410 LEGACY_API_UNAVAILABLE_FOR_NEW_ORGANIZATION` 에러(2026-11-16 완전 폐지 예정)가 반환됩니다. 현재 프로젝트 구현은 OpenTelemetry 기반 `dataset.run_experiment()`를 사용하므로 실험 실행 및 트레이스 적재에는 영향이 없습니다.

### PR Description Update

GitHub PR #280 본문([.local/pr280-body.md](../../.local/pr280-body.md))의 `Validation`과 `Risks` 섹션에 이번 CI Lite 통과 및 실제 Langfuse Cloud / Ollama 검증 결과를 반영했습니다.

## Remaining Human Gates

- **Langfuse UI 평가**: `staged-review-4k` 실행 결과에 대해 Langfuse UI에서 5개 평가 기준(`added_value`, `actionability`, `evidence_awareness`, `uncertainty_handling`, `prioritization`) 점수와 사유를 사람이 직접 기록.
- **PR 승인 및 병합**: Draft 해제, 인간 코드 리뷰 및 최종 머지 판단.
