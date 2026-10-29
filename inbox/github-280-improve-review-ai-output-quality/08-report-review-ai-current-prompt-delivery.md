---
type: report
title: Review AI Current Prompt Delivery
description: 일반 실행을 현재 한국어 프롬프트로 통일하고 버전별 JSON 검토를 레거시로 분리한 결과를 정리합니다.
---

# Review AI Current Prompt Delivery

기준 commit `a6d299e64596de88487e1708acabbba992a0f7e0` 이후 일반 API와 live CLI를 같은 현재 한국어 단계별 프롬프트로 통일했다. v1/v2/v3는 일반 실행에서 선택하지 않는다.

## Current And Legacy

| Entry | Behavior |
| --- | --- |
| `review_ai.review_null_spike` | 근거 검토·초안 비판·종합의 텍스트를 수집하고 코드가 JSON 생성 |
| `review_ai.service.review_null_spike` | 같은 현재 실행 |
| 기본 CLI 또는 `MODE=staged` | 현재 실행. 시작 시 `Review AI workflow: current (staged-v1).` 표시 |
| `review_ai.legacy.review_null_spike` | 명시적으로 전달한 identity의 과거 JSON 검토·검증 |
| `MODE=legacy` | `LEGACY_PROMPT_VERSION`에 v1/v2/v3 명시 필수. 옛 version 환경 변수로 fallback하지 않음 |

일반 API의 반환형은 의도적으로 `StagedReviewResult`로 바뀐다. 이전 JSON 결과가 필요한 호출자는 legacy import로 옮긴다. `MODE=structured`는 호출 전에 이전 방법을 안내하며 거부한다. 일반 환경의 기존 `HMDA_AGENTIC_REVIEW_PROMPT_VERSION`은 값을 출력하지 않고 무시한다.

현재 조합은 책임별 Markdown과 일반 한국어 정책을 사용한다. 과거 완성 본문은 [legacy snapshot](../../src/hmda_reliability/review_ai/prompt/legacy/)으로 동결해 현재 모듈을 바꿔도 기존 version의 digest가 바뀌지 않는다. 일반 import는 legacy 리소스를 읽지 않는다. 더 오래된 실행은 기록된 project_revision으로 재현한다.

## Run The Current Checkout

사용자가 실행한 main `1794d3dc`는 이번 변경 전 코드다. 환경 설정만으로 새 코드가 되지 않는다. main을 병합하거나 checkout을 바꾸지 않았으며 현재 구현은 PR 작업 폴더에서 실행한다.

```bash
cd /home/mols3131d/workspaces/hmda-data-reliability/.local/worktrees/pr280-output-quality
uv run --env-file .env python scripts/run_agentic_review_live.py
```

이 작업 폴더의 `.env`는 MODE=staged를 명시하고 옛 PROMPT_VERSION을 제거했다. 모델·credential·시간 예산은 유지했다. 첨부된 read-only snapshot과 다른 checkout의 `.env`는 변경하지 않았다.

## Verification

- Review AI/Runtime AI **407 passed, 1 skipped**. 일반 공개 API·직접 service·CLI의 현재 선택과 명시적 legacy 회귀를 확인했다.
- 기존 v1/v2/v3 golden digest 및 snapshot 바이트를 보존했고, wheel을 checkout 밖에서 import해 현재·legacy 리소스를 확인했다.
- Ruff·format·ty·Tach·Markdown·OpenSpec strict **32 passed, 0 failed**, 문서 Mermaid 검증·preview를 완료했다.
- 실제 CLI 설정 로딩으로 현재 기본 함수와 legacy 미로딩을 확인했다. 실제 모델 생성과 현재 commit의 hosted CI는 재검증하지 않았다.

요구사항은 [Prompt Spec](../../openspec/specs/review-ai-prompt-engineering/spec.md), 실행 경계는 [Review Spec](../../openspec/specs/reliability-agentic-review/spec.md), 사용법은 [개발 가이드](../../docs/development/review-ai-prompts.md), 작업 근거는 [Change Tasks](../../openspec/changes/review-ai-unify-current-prompt/tasks.md)가 소유한다.
