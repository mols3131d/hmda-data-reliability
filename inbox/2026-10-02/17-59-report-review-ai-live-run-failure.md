---
type: report
title: Review AI Live Run Failure Report
description: 2026-10-02 Review AI live provider 실행의 schema validation 실패와 Langfuse Cloud 미전송 상태를 기록한다.
tags:
  - domain:review-ai
  - capability:live-proof
  - langfuse
---

# Review AI Live Run Failure Report

## 결론

2026-10-02 live provider 실행은 Ollama 응답 후 Review AI 응답 파싱·스키마 검증 경로에서 실패했다. Invocation은 `accepted`가 아니므로 accepted output의 Langfuse projection은 생성할 수 없지만, 실패 상태의 최소 메타데이터 projection은 지원된다. 이번 실행에서는 노출된 credential을 사용하지 않도록 Langfuse export를 끈 상태로 실행했으므로 Cloud ingestion이나 UI 표시 여부는 검증하지 않았다.

## 실행 근거

| 항목 | 관찰값 |
| --- | --- |
| Invocation | `ar-20261002-975b6bdd2b7a` |
| 결과 | `validation_failed` |
| Failure code | `response_schema_invalid` |
| Provider model | `qwen2.5-coder:7b` |
| Latency | 약 17.5초 |
| Token usage | prompt 1,046 / completion 519 / total 1,565 |
| Langfuse export | 실행 시 `HMDA_LANGFUSE_EXPORT=false`로 비활성화 |
| Artifact | [invocation evidence](../../.local/artifacts/agentic-review/invocations/ar-20261002-975b6bdd2b7a.json) |

설정 점검에서는 live opt-in과 Langfuse export opt-in이 켜져 있고 Cloud base URL 및 두 key가 설정되어 있음을 값 자체를 노출하지 않고 확인했다. 단, 실제 실행은 command-line override로 export를 끈 상태였다.

## 해석과 한계

- 실행이 provider 응답 단계까지 도달했다는 것은 artifact의 latency와 token usage로 확인된다.
- 실패 상태이므로 accepted output의 Langfuse projection을 기대할 수 없다. 실패 상태 자체의 최소 메타데이터 projection은 가능하지만, 이번 실행은 export를 꺼 실제 전송을 하지 않았다.
- Artifact에는 `parsed_output: null`, `validation: null`이 저장되어 있고 원시 model output도 없다. `response_schema_invalid`는 JSON 파싱 오류와 스키마 검증 오류를 함께 나타내므로 정확한 위반 원인은 이 증거만으로 특정할 수 없다. 후속 [응답 실패 조사](18-06-research-review-ai-response-failure.md)에 근거와 진단 한계를 기록했다.
- `HMDA_LANGFUSE_EXPORT=false` 실행은 로컬 provider proof를 분리해 확인한 것이며 Langfuse Cloud 연동 검증은 아니다.
- 이전 `.env` 검토 중 Langfuse secret key 값이 대화에 노출된 것으로 기록되어 있다. 2026-10-02 사용자가 키 교체 완료를 확인했다. 이는 사용자 확인에 따른 상태 갱신이며, 새 키의 인증이나 Cloud ingestion 성공을 검증한 것은 아니다. 새 키 값은 이 보고서에 기록하지 않는다.
- Repository의 [Review AI Evaluation guide](../../docs/development/review-ai-evaluation.md)는 `submitted_unverified`도 원격 저장의 증거로 간주하지 않으며, Cloud UI에서 observation을 확인하도록 요구한다.

## 다음 조치

1. 키 교체는 사용자 확인 기준 완료됐다. 새 값을 채팅, 로그, 보고서 또는 Git에 넣지 않는다.
1. 기존 invocation에는 비교할 `parsed_output`이 없으므로, 후속 조사 결과를 바탕으로 안전한 오류 진단 방법을 정한 뒤 재실행에서 실패 지점을 특정한다. 필요하면 provider 응답 형식 또는 prompt/runtime 설정을 조정하고, 진단 산출물에는 불필요한 입력 내용을 복사하지 않는다.
1. 수정 후 live proof를 다시 실행해 `accepted`인지 확인한다.
1. 교체한 key로 Langfuse export를 켜서 다시 실행한다. `submitted_unverified`가 나오면 성공으로 단정하지 말고 UI에서 `review-ai-post-hoc-projection` observation의 invocation, revision, digest와 입출력을 대조한다.

## 재현 명령

Langfuse 전송 없이 provider 경로만 재실행:

```bash
HMDA_LANGFUSE_EXPORT=false uv run --extra langfuse --env-file .env python scripts/run_agentic_review_live.py
```

전체 설정 및 projection 절차는 [Review AI Evaluation guide](../../docs/development/review-ai-evaluation.md)를 따른다. 이 보고서는 해당 실행의 비정규 작업 기록이며 canonical 절차나 구현 계약을 대체하지 않는다.
