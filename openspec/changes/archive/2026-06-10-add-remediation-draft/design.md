## Context

현재 MVP 흐름은 profile -> detection -> impact까지 이어진다. 다음 단계는 사람이 승인할 수 있는 조치 초안을 만들어야 한다.

이번 slice는 외부 LLM 호출 없이 deterministic LangGraph workflow로 시작한다. State는 `TypedDict`, node는 triage/rca/plan 1단계씩 둔다.

## Goals / Non-Goals

**Goals:**

- LangGraph workflow로 incident/evidence/lineage를 해석한다.
- RCA summary, affected assets, recommended actions, dbt test suggestions, backfill/validation actions를 만든다.
- 결과를 Pydantic `RemediationDraft`로 검증한다.

**Non-Goals:**

- LLM provider 연동
- 자동 backfill 실행
- approval 처리
- Jira/Slack ticket 생성

## Decisions

### Deterministic workflow로 시작한다

MVP 재현성을 위해 rule mapping 기반 node를 사용한다. LangGraph 구조는 유지하되 외부 LLM 호출은 후속 확장으로 둔다.

### RemediationDraft는 Pydantic output contract로 둔다

approval/backfill slice가 stable한 필드를 참조해야 하므로 dict가 아닌 Pydantic 모델로 반환한다.

### Incident recommended_actions를 보존/보강한다

Detector가 생성한 action을 기본값으로 삼고 incident type별 필수 action을 추가한다.

## Risks / Trade-offs

- [Risk] deterministic RCA는 표현력이 낮다. -> MVP 평가 가능성을 우선하고 LLM 기반 개선은 후속으로 둔다.
- [Risk] rule mapping이 늘어날 수 있다. -> incident type별 helper로 분리한다.
