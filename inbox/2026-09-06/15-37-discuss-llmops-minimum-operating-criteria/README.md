---
type: discuss
title: "LLMOps Minimum Operating Criteria"
description: "현재 프로젝트에서 검증 가능한 가장 작은 LLMOps feedback loop와 완료 기준을 토론한다."
status: "in_progress"
discussion:
  id: "2026-09-06-llmops-minimum-operating-criteria"
  type: explore
  exchange: iterative
  cadence: scheduled
  decision_authority: human
  lead: A
  started_at: "2026-09-06T15:37:41+09:00"
  ends_at: "2026-09-06T16:02:41+09:00"
  active_topic: t1
---

## Goal

현재 프로젝트에서 “LLMOps가 정상 작동한다”고 인정할 수 있는 가장 작은 feedback loop와 검증 가능한 완료 기준을 도출한다. 특정 플랫폼이나 자동화 수준이 아니라 실제 AI review의 품질을 반복 평가하고 변경 판단에 사용할 수 있는 최소 운영 능력을 찾는다.

## Session

- **Start** - 2026-09-06 15:37:41 KST
- **End** - 2026-09-06 16:02:41 KST
- **Duration** - 25 minutes

## Topic

### T1. Minimum Operating Criteria

- **Status** - active
- **Question** - live invocation, deterministic validation, provenance를 넘어 어떤 조건까지 충족해야 최소 LLMOps feedback loop가 닫혔다고 볼 수 있는가?
- **Done When** - A와 B가 필수 기준과 제외 기준을 검증 가능한 문장으로 좁히거나, 남은 차이가 사람의 우선순위 선택으로만 남는다.

## Current State

기준 revision은 현재 `main`의 `52fa171a781585e5bb11e1b589ca27e40a043b84`다. A의 첫 turn은 기존 trace/provenance/structured validation/live proof를 “운영 관찰과 안전한 contract의 기반”으로 인정하되, 이것만으로 답변의 실제 유용성을 검증했다고 보지 않는다. 다음 eligible participant는 B이며, A는 새로운 B turn이 생기기 전에는 추가 argumentative turn을 작성하지 않는다.

## References

- [`docs/VISION.md`](../../../docs/VISION.md)
- [`docs/mvp.md`](../../../docs/mvp.md)
- [`docs/ARCHITECTURE.md`](../../../docs/ARCHITECTURE.md)
- [`docs/domains/review-ai.md`](../../../docs/domains/review-ai.md)
- [`docs/domains/runtime-ai.md`](../../../docs/domains/runtime-ai.md)
- [`openspec/specs/reliability-agentic-review/spec.md`](../../../openspec/specs/reliability-agentic-review/spec.md)
- [`scripts/run_agentic_review_live.py`](../../../scripts/run_agentic_review_live.py)
- [`tests/review_ai/test_live_harness.py`](../../../tests/review_ai/test_live_harness.py)
- [`inbox/2026-09-04/15-02-research-orchestration-airflow-reliability-integration/00-brief-orchestration-design.md`](../../2026-09-04/15-02-research-orchestration-airflow-reliability-integration/00-brief-orchestration-design.md)
- [`inbox/2026-09-04/15-02-research-orchestration-airflow-reliability-integration/01-discussion-orchestration-design.md`](../../2026-09-04/15-02-research-orchestration-airflow-reliability-integration/01-discussion-orchestration-design.md)

## Synthesis

진행 중이다. 세션 종료 또는 stop condition 충족 시 A가 `최소 기준`, `제외`, `현재 상태`, `가장 큰 병목`, `다음 한 단계`만 남기는 짧은 최종 synthesis로 교체한다.
