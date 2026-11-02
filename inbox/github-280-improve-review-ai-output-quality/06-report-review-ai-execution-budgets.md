---
type: report
title: Review AI Execution Budgets
description: 단계별 검토의 환경 설정, 시간 예산과 실패 기록 개편 및 검증 범위를 정리합니다.
---

# Review AI Execution Budgets

기준 commit `fa0645055db03d5f5a416e19f992400ad2b4a65f` 이후 연결·읽기 대기, 단계·전체 예산을 분리했다. 설정 정본은 [환경 예제](../../.env.example)와 [운영 안내](../../docs/development/review-ai-prompts.md#timeouts-and-execution-budgets), 요구사항은 [OpenSpec](../../openspec/specs/reliability-agentic-review/spec.md#requirement-staged-execution-time-budgets)이 소유한다.

## Local Configuration

| Setting | Value | Meaning |
| --- | --- | --- |
| `HMDA_AGENTIC_REVIEW_CONNECT_TIMEOUT_SECONDS` | 10 | 연결 대기 제한 |
| `HMDA_AGENTIC_REVIEW_READ_TIMEOUT_SECONDS` | 300 | 각 응답 읽기 대기 제한 |
| `HMDA_AGENTIC_REVIEW_STAGE_BUDGET_SECONDS` | 360 | 단계의 rendering·호출·retry와 원문 저장을 포함한 채택 예산 |
| `HMDA_AGENTIC_REVIEW_WORKFLOW_BUDGET_SECONDS` | 1200 | 전체 단계의 후속 실행·결과 채택 예산 |
| `HMDA_AGENTIC_REVIEW_MAX_RETRIES` | 0 | 최초 시도 외의 추가 transport 재시도 수 |

로컬 `.env`에 새 시간 설정 네 개만 추가했다. 기존 TIMEOUT 300초·retry 0과 model·credential·출력 상한은 유지했다. CLI가 위 typed 설정을 읽는 것을 provider 호출 전에 확인했다. `.env`는 Git에서 제외되며 PR에는 예제만 포함한다.

READ를 명시하면 기존 TIMEOUT보다 우선한다. Staged에서 READ가 없으면 명시된 TIMEOUT, 그것도 없으면 300초를 사용한다. Structured에서 새 phase를 생략하면 기존 scalar fallback을 유지한다. 단계·전체 예산은 staged 전용이다. 정확한 범위와 유효값은 운영 안내를 따른다.

## Failure And Evidence

실제 SDK timeout은 `provider_timeout`, 연결 오류는 `provider_connection_error`, 실행 예산 소진은 `stage_budget_exhausted` 또는 `workflow_budget_exhausted`로 구분한다. 호출 시작 전 소진은 시도 0회로 남긴다. SDK hidden retry는 0이며 세 단계 물리 호출 상한은 `3 * (max_retries + 1)`이다.

늦게 반환된 bounded 응답도 원문 저장 후 예산 실패로 처리한다. 이전 checkpoint와 raw는 유지한다. 마지막 collection 저장 중 시간이 끝나면 결과를 completed로 채택하지 않으며 이미 생성한 output 경로와 digest는 진단용으로 보존·검증한다. SDK가 본문 없이 timeout을 반환한 경우 저장 가능한 raw는 없다.

네트워크 phase timeout은 총 wall time의 상한이 아니다. 예산도 진행 중 동기 호출이나 원격 추론의 강제 종료를 보장하지 않는다. 단계 elapsed_ms는 checkpoint 쓰기 전, workflow elapsed_ms는 최종 manifest 쓰기 전에 측정한다. 실패 진단 기록의 마지막 저장까지 강제 중단하지 않는다.

## Verification

- Review AI/Runtime AI **400 passed, 1 skipped**. SDK와 가짜 HTTP, monotonic clock을 사용해 실제 대기 없이 timeout·retry·예산 실패와 원문 보존을 검증했다.
- Ruff·format·ty·Tach·Markdown·diff·OpenSpec strict **31 passed, 0 failed**, wheel build 및 새 설정 모듈 포함 확인을 완료했다. [Change Tasks](../../openspec/changes/review-ai-budget-staged-execution/tasks.md#validation)에 범위를 기록했다.
- 독립 검토에서 추가 P1/P2 결함은 확인하지 못했다. 과거 JSON의 미기록 설정은 None으로 읽으며 기존 prompt digest와 canonical input은 유지한다.
- Git fixture probe에서 상속된 Git-local 환경을 pytest child 경계에서 제거함을 확인했다. 같은 경계로 pre-push 검증을 수행한다.
- 실제 모델 생성과 이번 revision의 hosted CI는 아직 확인하지 않았다. [이전 live 실패](05-report-review-ai-staged-text-delivery.md#live-attempt)를 현재 코드의 timeout 분류·성공 또는 품질 증거로 취급하지 않는다.

## Next Run

```bash
uv run --env-file .env python scripts/run_agentic_review_live.py
```

같은 합성 컨텍스트로 세 번 질의하며 실제 데이터 적재는 하지 않는다. 기본 staged 모드의 workflow_path·각 response_path·output_path를 확인한다. 로컬 시작값은 모델에서 검증된 최적값이나 완료 보장이 아니다.
