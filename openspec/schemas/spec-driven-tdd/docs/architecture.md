# Architecture

## Purpose

이 schema는 OpenSpec Change의 planning lifecycle과 artifact dependency를 정의하고, Apply를 프로젝트 지침에 맞는 TDD-compatible implementation으로 연결한다.

## Workflow

```mermaid
flowchart LR
    P[Proposal] --> S[Specs]
    S --> D[Design]
    D --> T[Tasks]
    T --> A[Apply]
```

## Artifact Responsibilities

| Artifact | Responsibility |
| --- | --- |
| Proposal | 변경 이유, 범위와 영향받는 Capability |
| Specs | 외부에서 관찰 가능한 행동 계약 |
| Design | 구현에 필요한 기술적 결정, 책임 경계와 검증 전략 |
| Tasks | 독립적으로 검증 가능한 구현 결과와 진행률 |

이 분리는 같은 판단을 여러 artifact에 복제하지 않고 각 단계가 다음 단계에 필요한 정보만 제공하기 위한 것이다.

## Design Rationale

### Outcome-Based Tasks

TDD의 RED/GREEN/REFACTOR는 implementation feedback loop다. 이를 별도 progress item으로 모델링하면 실제 구현 결과보다 task 수가 빠르게 늘어난다. 따라서 Tasks는 실행 phase가 아니라 검증 가능한 구현 결과를 중심으로 추적한다.

### Bounded Feedback

구현 중 발견한 문제를 별도 review-remediation workstream으로 누적하면 feedback 자체가 다시 planning과 review를 만드는 재귀가 생긴다. 현재 범위의 문제는 기존 계획의 owning surface로 되돌리고, 독립적인 새 범위는 현재 Change와 분리하는 방향을 사용한다.

## Contract Ownership

| Owner | Contract |
| --- | --- |
| [`../schema.yaml`](../schema.yaml) | artifact DAG, 목적·의존성·완료 조건과 Apply 의미 |
| [`../templates/`](../templates/) | artifact structure, field, parser surface와 구조에 종속된 작성 규칙 |
| [`baseline/DIRECTIVE.md`](baseline/DIRECTIVE.md) | 장기 보존할 requirement, decision, invariant와 변경 근거 |
| Project `openspec/config.yaml` | project-specific context, naming과 추가 규칙 |

이 문서는 위 계약을 다시 정의하지 않고 구조와 설계 이유만 설명한다.
