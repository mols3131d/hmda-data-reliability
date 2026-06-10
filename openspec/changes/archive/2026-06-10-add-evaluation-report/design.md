## Context

MVP scope는 `normal_partition`, `row_count_drop`, `null_spike`, `schema_drift`, `freshness_delay`, `downstream_impact`를 최소 incident case로 둔다. evaluation report는 각 case의 기대 결과와 실제 결과를 사람이 빠르게 비교할 수 있어야 한다.

## Goals / Non-Goals

**Goals:**

- case별 detection 성공 여부를 계산한다.
- case별 remediation/action 성공 여부를 계산한다.
- 전체 성공률을 Pydantic report 모델로 반환한다.
- Markdown `evaluation_report.md`를 생성한다.

**Non-Goals:**

- dashboard UI
- notebook 렌더링
- 외부 LLM 평가
- test runner orchestration

## Decisions

### Evaluation 입력은 case result 모델로 둔다

평가 엔진은 pipeline 실행 자체를 소유하지 않는다. detection/remediation/backfill 실행 결과를 `EvaluationCaseResult`로 받아 집계만 담당한다.

### normal case는 expected incident가 없어야 성공이다

`expected_incident_types`가 비어 있으면 실제 detected incident도 없어야 detection 성공으로 본다.

### Markdown은 결정적 문자열로 생성한다

보고서는 CI와 로컬에서 diff가 쉽도록 표 기반 Markdown으로 만든다. timestamp는 report 모델의 `generated_at`에만 둔다.

## Risks / Trade-offs

- [Risk] 실제 pipeline runner가 없으면 입력 생성은 호출자 책임이다. -> MVP에서는 기능별 deterministic 결과를 조합해 report 생성 가능성을 먼저 고정한다.
- [Risk] action success 기준이 단순 subset 비교다. -> action contract가 안정되면 severity별 가중치를 후속으로 추가한다.
