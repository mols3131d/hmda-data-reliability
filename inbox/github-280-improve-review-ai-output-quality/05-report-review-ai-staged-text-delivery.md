---
type: report
title: Review AI Staged Text Delivery
description: 단계별 한국어 텍스트와 코드 JSON 취합 구현, 실행 방법과 실제 검증의 한계를 정리합니다.
---

# Review AI Staged Text Delivery

모델은 근거 검토·초안 비판·종합의 세 질문에 한국어 텍스트로 답하고, 코드가 원입력 식별자·수치와 세 원문을 JSON으로 직렬화한다. 기존 변경은 `77761a7527d3413d72fb0e83bdab9a9d99ea1152`로 먼저 커밋·푸시했고, 이 보고서는 그 이후 단계 실행 구현의 결과다.

## Run And Inspect

기존 로컬 설정으로 다음 명령을 실행한다. 모드 생략 기본값은 staged다.

```bash
uv run --env-file .env python scripts/run_agentic_review_live.py
```

결과의 `output_path`는 단계별 원문이 들어 있는 코드 생성 JSON이다. `workflow_path`는 원문 없는 실행 기록이며 `stages[].response_path`와 `record_path`가 각 단계의 원문·checkpoint를 가리킨다. 세 단계가 끝나기 전에 실패하면 output을 만들지 않고 반환된 원문과 이전 기록을 남긴다.

| Contract | Meaning |
| --- | --- |
| `completed` | 세 답변의 수집·저장 완료. 사실성·검토 가치·사람 승인과 구별 |
| `stages[{stage_id,text}]` | 모델 답변의 공백·개행을 보존한 collection |
| 원입력 facts | 코드가 직접 복사. 모델 prose에서 분류·priority·근거 참조를 추출하지 않음 |
| Context | 같은 canonical input과 완료된 assistant 답변을 매 호출에 유지 |
| Bounds | 누적 입력 byte, per-call timeout·retry·출력 cap, 고정 세 단계 |

기존 JSON 응답과 validator를 비교·재현할 때는 `HMDA_AGENTIC_REVIEW_MODE=structured`를 명시한다. 기존 prompt version 설정은 이 모드에 적용된다. Staged Langfuse 전송은 `skipped_staged_mode`로 표시한다. 자세한 실행·출처 구분은 [평가 가이드](../../docs/development/review-ai-evaluation.md#staged-text-review), 모듈 구성은 [Prompt Composition](../../docs/development/review-ai-prompts.md#staged-text-workflow)을 따른다.

## Verification

- Review AI/Runtime AI: **346 passed, 1 skipped**. Optional Langfuse SDK media smoke가 생략됐다.
- 실제 SDK와 fake HTTP를 연결해 JSON forcing 생략·assistant 이력·세 단계 원문과 코드 JSON을 검증했다. 중간 length·빈 답변·provider/storage 실패·누적 입력 상한에서 후속 중단과 기록 보존도 확인했다.
- 기존 v1/v2/v3 golden digest를 보존했다. Wheel/sdist와 checkout 밖의 단계 리소스 로딩을 확인했다.
- Ruff·format·ty·Tach·Markdown·Inbox·diff 및 OpenSpec strict 검증을 수행했다. 정확한 실행 항목은 [Change Tasks](../../openspec/changes/review-ai-stage-text-reviews/tasks.md#validation)에 기록했다.

## Live Attempt

현재 작업 폴더에서 `local-staged-text-worktree` 표식으로 합성 사례를 한 번 실행했다. Retry 0, 각 단계 timeout 60초·생성 상한 4096토큰으로 제한했다. 모델 서버 조회는 가능했지만 첫 생성 요청에서 본문을 받지 못해 다음 결과로 끝났다.

- Workflow: `sr-20261028-6543e4292f04`
- Status/failure: `unavailable / provider_connection_error`
- 물리 호출: 1회. 후속 두 단계는 호출하지 않았다.
- 로컬 manifest: `.local/artifacts/pr280-staged-smoke/agentic-review/staged/sr-20261028-6543e4292f04/workflow.json`
- 본문이 반환되지 않아 raw response와 output JSON은 없다. 실패 checkpoint·manifest는 남았으며 현재 verifier로 다시 확인했다.

초기 smoke 프로세스는 verifier 수정 전 코드를 로드해 추가 검증 실패 문구를 출력했다. 필수 prompt identity와 canonical scalar 타입 대조를 수정하고 같은 실패 기록을 모델 재호출 없이 재검증했다. 구현은 fake HTTP까지의 전체 경로에서 통과했으며, 실제 모델의 세 단계 완료·한국어 품질·human rubric과 현재 commit의 hosted CI는 아직 확인하지 않았다.
