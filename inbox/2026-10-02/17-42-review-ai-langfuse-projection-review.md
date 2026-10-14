---
type: review
title: Review AI Langfuse Projection Review
description: 현재 Review AI의 선택적 Langfuse projection 구현과 테스트가 synthetic-only, opt-in, evidence-bound contract를 지키는지 검토한다.
tags:
  - domain:review-ai
  - capability:langfuse-projection
  - llmops
---

# Review AI Langfuse Projection Review

> [!IMPORTANT]
> **Clear with limitations** — 로컬 projection 경로에서 material defect는 확인하지 못했다. 합성 입력 일치, 실패 상태 데이터 최소화, 선택적 자식 프로세스, 크기·시간 제한 및 검증 테스트가 의도된 경계를 뒷받침한다. 실제 Langfuse ingestion·UI와 human annotation은 검증하지 못했다.

- **Target** — [Langfuse projection implementation](../../src/hmda_reliability/review_ai/evaluation/langfuse.py), 관련 tests와 [Review AI Evaluation guide](../../docs/development/review-ai-evaluation.md)
- **Revision** — `2c3b61cd021267649f1cbc76f1c149abf93598f9` (`agent/refactor/review-ai-evaluation-subdomain`)
- **Scope** — 선택적 projection payload 생성, annotation completeness 검사, SDK child 전송·격리 및 직접 관련 테스트. 이전 remediation 보고서는 현재 코드와 차이를 확인하는 참고자료로만 사용했다.

## Findings

확인된 material finding 없음. Langfuse observation은 `span`으로 기록되며 generation으로 자동 분류되지 않지만, 현재 contract가 provider 호출 후 검증된 synthetic 결과를 post-hoc 투영하는 것이므로 이 검토에서는 결함으로 판정하지 않았다. generation/model/token 분석을 요구하는 후속 사용 사례가 생기면 별도 contract 검토가 필요하다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | Focused projection tests | `uv run pytest -q tests/review_ai/evaluation/test_langfuse_projection.py`: 33 passed. |
| ✅ Pass | Local contract inspection | `project_invocation()`은 전체 canonical input을 `expected_input`과 대조하고 accepted 결과에만 허용 필드를 투영한다. 실패 상태는 최소 metadata만 내보낸다. |
| ✅ Pass | Export boundary inspection | 전송은 opt-in이며 URL/key 검사, payload byte 상한, child environment allowlist, timeout, media upload 비활성화와 결과 비간섭 처리가 확인됐다. 반환 상태 `submitted_unverified`도 원격 저장을 주장하지 않는다. |
| ⚪ Not Verified | Current Langfuse documentation | Skill에서 요구하는 공식 best-practices 및 observation-type 문서 fetch가 네트워크 도메인 정책에 차단됐다. 현재 평가는 저장소의 명시된 contract와 기존 SDK-specific test evidence를 사용했다. |
| ⚪ Not Verified | Remote ingestion and human utility | 이 실행에서는 실제 Langfuse project에 전송하지 않았다. 원격 trace/UI 출력, annotation 절차와 사람의 rubric 채점은 확인하지 않았다. |

## Risks and Limits

- 성공 종료는 remote ingestion 증거가 아니다. 가이드에 따라 Langfuse UI에서 observation, invocation, revision, digest와 input/output을 확인해야 한다.
- 과거 remediation report의 SDK media processor 검증은 현재 코드가 이를 비활성화하는 설정을 포함한다는 보조 evidence다. 이번 실행은 해당 integration test 자체를 별도로 선택 실행하지 않았고, optional SDK가 현재 환경에 설치되어 있는지도 확인하지 않았다.
- 현재 projection은 호출 당시의 provider generation을 재구성하지 않고 사후 span 하나를 기록한다. 모델/token 비교가 목적이 되면 generation type, model/usage 관측 가능성, 기록된 latency와 projection span duration의 해석을 함께 재검토해야 한다.
