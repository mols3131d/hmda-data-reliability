# Diagnosis

runtime 문제를 모두 관찰하려 하지 않는다. **실행 후 답하기 어렵고 오해 비용이 큰 복원 질문 하나**를 먼저 고른다.

## Reconstruction Question

| Question | Typical signal |
| --- | --- |
| 어떤 경로를 탔는가? | skip, retry, fallback 또는 조건부 실행 결과를 구분하기 어렵다. |
| 왜 이 결정이 내려졌는가? | 결과는 남지만 선택 근거가 사라진다. |
| 어떤 상태가 바뀌었는가? | mutation, commit 또는 reconciliation 전후를 복원하기 어렵다. |
| 무엇이 실패했는가? | exception은 있으나 대상, 단계 또는 causal context가 부족하다. |
| 어떤 실행과 연결되는가? | 분리된 event, result, artifact를 같은 실행으로 묶기 어렵다. |

여러 질문이 보여도 가장 위험하거나 반복적으로 코드를 다시 추적하게 만드는 하나를 먼저 해결한다.

## Priority

오해했을 때 영향이 큰 순서로 본다.

1. destructive mutation, overwrite, recovery 같은 위험 작업
1. approval, validation, promotion 같은 gate
1. 외부 process, framework, database 실행과 실패
1. 중요한 branch 또는 state transition
1. 일반적인 내부 진행 상황

로그가 적다는 사실 자체는 관찰 공백의 근거가 아니다.

## Route Elsewhere

- 코드 구조, 이름, caller contract가 주된 병목이면 `pivot-clarify-code`로 분리한다.
- 실제 defect 여부를 판단해야 하면 review/debugging으로 분리한다.
- 지속적인 운영 감시, SLO, telemetry pipeline이 목적이면 monitoring/observability 작업으로 분리한다.
- 성능 원인 분석이 목적이면 profiling/performance 작업으로 분리한다.

## Stop

기존 runtime evidence만으로 선택한 질문에 직접 답할 수 있으면 수정하지 않는다.
