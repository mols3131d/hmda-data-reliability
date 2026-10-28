---
type: report
title: Review AI Response Retention
description: 실제 모델 응답의 원문을 검증 전에 보존하도록 수정한 결과와 재실행 방법을 정리합니다.
---

# Review AI Response Retention

모델이 반환한 응답 본문을 검증 전에 별도 로컬 파일로 저장하도록 수정했다. 성공·잘못된 JSON·출력 계약 위반·사실 검증 실패 모두 저장된 `response_path`에서 원래 내용을 읽을 수 있다. 저장은 UTF-8 바이트를 그대로 보존하며 공백·개행을 바꾸지 않는다.

## Run and Inspect

```bash
uv run --env-file .env python scripts/run_agentic_review_live.py
```

새 실행 결과의 `response_path`가 원문이다. 현재 로컬 artifact root에서는 `.local/artifacts/pr280-manual/agentic-review/responses/<new-invocation-id>.txt`다. `invocation_path`는 기존처럼 sanitized 호출 기록 JSON을 가리킨다. 형식 검증에 실패해 `output=null`이어도 원문 파일은 남는다.

현재 작업 폴더의 tracked 변경을 포함해 실험할 수 있도록 로컬 `.env`의 revision을 `local-response-retention-worktree`로 지정했다. 모델·timeout·token 상한 등 사용자가 조정한 다른 값은 보존했다. 이는 clean commit의 live 품질 증거가 아니다.

## Validation

- 기준 head는 `314eec7c2bba35d8f515e74247af2da57a92b3a2`이며 이 결과는 그 위의 미커밋 작업 폴더 변경이다.
- 기존 구현에서 검증 전 응답 파일이 없어 회귀 테스트가 실패하는 것을 확인한 뒤 구현했다.
- 핵심 service/store/실제 SDK fake transport/result 계약 검사: **83 passed**.
- Review AI와 Runtime AI 전체 회귀: **275 passed, 1 skipped**. Skip은 optional Langfuse SDK smoke이며 실제 provider를 호출한 결과가 아니다.
- 원문과 sanitized record·콘솔·Langfuse projection 분리, 파일 권한·byte bound·identity 충돌 및 저장 실패 경로를 검증했다.
- Ruff check·format, Review AI source/tests의 ty 검사와 전체 Tach 검사, 전체 OpenSpec strict **24 passed**를 확인했다. 읽기 전용 후속 검토에서 확정된 추가 결함은 없었다.
- 구현 계약과 변경은 [응답 보존 Change](../../openspec/changes/review-ai-retain-provider-responses/tasks.md), 실행 절차는 [평가 가이드](../../docs/development/review-ai-evaluation.md#live-provider-proof)를 따른다.

## Limits

과거 `ar-20261028-8bd47b3a40d6`의 저장되지 않은 본문은 복원할 수 없다. 이번 변경으로 새 실제 모델 호출을 수행하지는 않았으며 사람이 직접 재실행해 새 응답을 확인하면 된다. Runtime이 본문을 반환하기 전에 차단한 oversized/네트워크 실패에는 응답 파일이 없다. 파일 저장 자체가 실패하면 accepted 결과 대신 provenance failure를 반환한다.
