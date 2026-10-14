---
type: report
title: Review AI Langfuse Input Type Fix Completion
description: PR #251 Langfuse 입력 JSON 타입 불일치 수정의 구현, 검증, 독립 리뷰와 푸시 근거를 기록한다.
tags:
  - domain:review-ai
  - capability:langfuse-projection
  - llmops
---

# Review AI Langfuse Input Type Fix Completion

2026-10-02 KST. [12번 코드 리뷰](12-review-review-ai-langfuse-code.md)의 F1을 수정하고 검증했다. 변경은 canonical JSON 비교와 회귀 검증에 한정하며, live Langfuse 전송이나 annotation 운영을 완료했다는 뜻은 아니다.

## Change

- [`project_invocation()`](../../src/hmda_reliability/review_ai/evaluation/langfuse.py)은 record의 canonical input과 독립 생성한 synthetic input을 기존 deterministic JSON encoder 결과로 비교한다. JSON 객체의 키 순서 차이는 허용하지만 `true`와 `1` 같은 JSON 타입 차이는 거부한다.
- [Projection regression test](../../tests/review_ai/evaluation/test_langfuse_projection.py)는 boolean 값을 정수로 바꾸고 prompt digest를 재계산한 record를 JSON으로 저장·복원한 뒤에도 projection이 입력 불일치로 거부하는지 확인한다. Harness 경로에서도 exporter를 호출하지 않고 `accepted` 결과, 종료 코드 0과 기존 invocation 파일을 보존하는지 검증한다.
- 정상 projection 검증은 독립 생성 입력의 key 순서를 바꿔도 입력, output, prompt digest와 output digest가 보존되는지 확인한다.

## Delivery

- **Branch:** `agent/refactor/review-ai-evaluation-subdomain`
- **Commit:** `6b5d19dac4f34caca5ff63531ed69251817dfe49` (`fix(review-ai): preserve JSON types in input check`)
- **Remote:** `origin/agent/refactor/review-ai-evaluation-subdomain`에 push 완료. Push 직전 원격은 이전 commit `5ef06cf`와 일치했고, push가 성공했다.
- 커밋에는 구현 파일과 해당 테스트 파일만 포함했다. 기존 미추적 Inbox 자료와 `skills-lock.json`은 포함하지 않았다.

## Verification

| Check | Result | Evidence |
| --- | --- | --- |
| Regression before fix | Fail as expected | 입력 타입만 다르고 digest를 재계산한 JSON round-trip record에 기존 구현은 `ValueError`를 발생시키지 않았다. |
| Projection module | Pass | 현재 파일 기준 `.venv/bin/python -m pytest tests/review_ai/evaluation/test_langfuse_projection.py -q`: **34 passed**, skip 없음. |
| Related Review AI and Runtime AI suites | Pass | 수정 검증 중 `tests/review_ai tests/runtime_ai`: **188 passed**, skip 없음. |
| Push hook | Pass | Push 전 영향 범위 테스트 **53 passed**; Ruff check와 format check도 통과했다. |
| Static and architecture checks | Pass | Ruff check/format, `ty check` (두 변경 파일), `tach check`, `git diff --check`; 편집기 진단 없음. |
| Independent review | Clear | Quality/adversarial specialist가 변경 범위와 현재 코드를 검토했고 `review-lead` 최종 판정은 `clear`였다. 리뷰한 소스·테스트 tree는 commit `6b5d19d`에 포함된 tree와 동일하다. |

## Limits

실제 provider 호출, Langfuse 원격 ingestion/UI 확인과 사람의 rubric 평가는 수행하지 않았다. 현재 Langfuse 공식 문서 fetch는 네트워크 도메인 정책으로 차단됐다. 이번 수정은 SDK 사용 방식을 바꾸지 않으며, remote 운영 동작에 대한 주장은 하지 않는다.
