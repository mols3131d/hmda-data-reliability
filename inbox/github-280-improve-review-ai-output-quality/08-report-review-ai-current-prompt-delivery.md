---
type: report
title: Review AI Current Prompt Delivery
description: 버전별 레거시 지원을 제거하고 현재 한국어 단계 실행과 사람 평가로 통일한 결과를 정리합니다.
---

# Review AI Current Prompt Delivery

기준 commit `24b5f26833121de853ce0787c0bb67c3ad25673d`에서 사용자의 후속 지시를 반영했다. 레거시를 별도 경로로 지원하던 구현을 삭제하고 현재 한국어 프롬프트로만 실행한다. 이전 전환 보고서를 이 최종 동작에 맞춰 갱신했다.

## Current Execution

| Entry | Behavior |
| --- | --- |
| `review_ai.review_null_spike` | 근거 검토·초안 비판·종합의 한국어 텍스트 수집 후 코드로 JSON 생성 |
| `review_ai.service.review_null_spike` | 같은 현재 실행 |
| `review_ai.review_null_spike_staged` | 같은 실행의 명시적인 단계 수집 이름 |
| Live CLI | 별도 모드·버전 선택 없이 같은 현재 실행. 시작 시 `Review AI workflow: current (staged-v1).` 표시 |

모델은 JSON을 작성하지 않는다. 원본 사례·이전 assistant 답변을 다음 호출에 함께 전달하고, 코드는 입력의 식별자·수치와 고정 단계 ID·순서·반환된 텍스트만 JSON으로 결합한다. `completed`는 수집·저장 완료이며 자연어의 정확성이나 사람 승인을 뜻하지 않는다.

현재 [Markdown 모듈](../../src/hmda_reliability/review_ai/prompt/)과 [단계 조립기](../../src/hmda_reliability/review_ai/staged/prompt.py)를 사용한다. Workflow identity `staged-v1`과 prompt digest는 출처 기록용이다.

## Removed Support

- 버전별 v1/v2/v3 Markdown snapshot, legacy renderer와 실행 namespace.
- `PromptIdentity`, 입력의 `prompt_identity`, 옛 JSON 출력·검증·결과 계약, 응답 JSON 파서와 structured validator.
- 옛 invocation record reader와 해당 결과에만 연결되던 Langfuse projection. CLI는 외부 projection을 실행하지 않는다.
- CLI의 MODE·PROMPT_VERSION·LEGACY_PROMPT_VERSION·LANGFUSE_EXPORT 읽기와 분기. 별도 호환 alias·fallback·이전 안내 경로도 없다.
- 이전 포맷 전용 회귀와 fixture. 공유 입력·원문 저장·현재 실행의 검증은 현재 계약으로 유지한다.

기존 사용자 artifact와 과거 Inbox 보고서는 삭제하거나 현재 결과로 변환하지 않았다. 현재 runtime은 과거 JSON 기록의 해석·재생 호환을 제공하지 않는다.

## Preserved Guarantees

입력은 immutable snapshot이며 incident/draft identity, 제공된 Evidence 참조, canonical target과 유한한 수치를 검증한다. Provider에는 bounded allowlist만 전달하고 사례 데이터가 system 질문을 바꾸지 못하게 한다.

반환된 UTF-8 원문은 검증 전에 별도 파일에 저장한다. 빈 답변·잘림·provider 실패·저장 실패·누적 입력 초과·시간 예산 소진은 후속 호출을 중단하고 이미 저장된 원문·checkpoint를 남긴다. Create-only 저장, 원자적 쓰기, 충돌 차단과 digest 검증을 유지한다.

연결·읽기 대기와 단계·전체 예산은 각각 10/300/360/1200초, retry는 0회가 로컬 시작값이다. 설정한 예산이 동기 호출을 즉시 강제 취소한다는 보장은 없다.

사람 평가의 입력은 `StagedReviewOutput`과 `workflow_id`로 전환했다. 다섯 rubric 기준, 명시적 사람 결정, 동일 사례·수치·revision 비교 차단을 유지하고 단계 순서와 원문 공백·개행까지 digest에 포함한다. 독립 수치 oracle 3사례·텍스트 control 8개와 현재 포맷의 정적 golden을 사용한다. 이는 실제 모델 출력의 품질 평가 결과가 아니다.

## Run The Current Checkout

사용자가 이전에 실행한 main `1794d3dc`는 변경 전 코드다. 현재 구현은 PR 작업 폴더에서 실행한다.

```bash
cd /home/mols3131d/workspaces/hmda-data-reliability/.local/worktrees/pr280-output-quality
uv run --env-file .env python scripts/run_agentic_review_live.py
```

이 작업 폴더의 `.env`에서는 불필요한 모드·버전·projection 선택 키를 제거했다. 모델·credential·시간 예산은 유지했다. 첨부된 read-only snapshot은 수정하지 않았다.

## Verification

- 구현 전 공개 API·입력의 레거시 의존 7건, CLI 모드 분기 1건, 현재 평가 전환 42건의 실패를 확인했다.
- Review AI/Runtime AI 전체 **261 passed**. 현재 API·CLI·실제 SDK 전송, 입력 검증, 실패 시 원문 보존, 저장 충돌, 시간 예산, 평가 회귀를 포함한다.
- Wheel을 checkout 밖의 isolated Python에서 import해 현재 세 단계의 한국어 메시지 digest가 source와 같고 삭제한 모듈·리소스가 배포물에도 없음을 확인했다.
- Ruff·format·ty·Tach·Markdown·Inbox·diff와 문서 Mermaid syntax/preview가 통과했다. OpenSpec strict는 **30 passed, 0 failed**다. 완료된 이전 Change 2개는 정본을 재적용하지 않고 원문 그대로 archive했다.
- 실제 모델 생성과 현재 commit의 hosted CI는 재검증하지 않았다. 합성 control의 평가 점수는 사람의 실제 판정으로 취급하지 않는다.

요구사항은 [Prompt Spec](../../openspec/specs/review-ai-prompt-engineering/spec.md), 실행 경계는 [Review Spec](../../openspec/specs/reliability-agentic-review/spec.md), 사용법은 [개발 가이드](../../docs/development/review-ai-prompts.md), 작업 근거는 [Change Tasks](../../openspec/changes/review-ai-unify-current-prompt/tasks.md)가 소유한다.
