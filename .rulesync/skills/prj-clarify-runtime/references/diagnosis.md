# Diagnosis

runtime 문제를 모두 관찰하려 하지 않는다. **실행 후 답하기 어렵고 오해 비용이 큰 복원 질문 하나**를 먼저 고른다.

## Route Before Instrumenting

먼저 runtime evidence가 실제 병목인지 확인한다.

| Main question | Route |
| --- | --- |
| 실행 후 무엇이 일어났는지 복원하기 어렵다 | `prj-clarify-runtime` |
| 코드를 읽어도 의미, 책임 또는 caller contract를 이해하기 어렵다 | `prj-clarify-code` |
| 현재 동작이 올바른지, defect인지 판단해야 한다 | `prj-review-code` 또는 debugging workflow |
| 어떤 test나 validation으로 동작을 증명할지 설계해야 한다 | `prj-testing-context` |
| 실행 boundary나 책임 자체를 재설계해야 한다 | architecture/design |
| 지속적인 상태 감시, alert, SLO가 필요하다 | monitoring/observability |
| 왜 느리거나 자원을 많이 쓰는지 찾아야 한다 | profiling/performance |

주된 문제가 runtime evidence가 아니면 clarification 명목으로 logging이나 metadata를 추가하지 않는다.

## Reconstruction Question

| Question | Typical signal |
| --- | --- |
| 어떤 경로를 탔는가? | skip, retry, fallback 또는 조건부 실행 결과를 구분하기 어렵다. |
| 왜 이 결정이 내려졌는가? | 결과는 남지만 선택 근거가 사라진다. |
| 어떤 상태가 바뀌었는가? | mutation, commit 또는 reconciliation 전후를 복원하기 어렵다. |
| 무엇이 실패했는가? | exception은 있으나 대상, 단계 또는 causal context가 부족하다. |
| 어떤 실행과 연결되는가? | 분리된 event, result, artifact를 같은 실행으로 묶기 어렵다. |

여러 질문이 보여도 가장 위험하거나 반복적으로 코드를 다시 추적하게 만드는 하나를 먼저 해결한다.

## Debt Form

복원 질문을 어렵게 만드는 주된 형태를 하나 고른다.

| Form | Signal |
| --- | --- |
| Missing | 필요한 결과, 이유 또는 실패 context가 남지 않는다. |
| Duplicate | 같은 사실이 여러 layer나 surface에서 반복된다. |
| Misowned | 사실을 가장 잘 아는 boundary와 evidence 위치가 다르다. |
| Noisy | routine detail이 많아 중요한 event를 찾기 어렵다. |
| Disconnected | 필요한 evidence는 있으나 같은 실행으로 연결하기 어렵다. |

## Priority

오해했을 때 영향이 큰 순서로 본다.

1. destructive mutation, overwrite, recovery 같은 위험 작업
1. approval, validation, promotion 같은 gate
1. 외부 process, framework, database 실행과 실패
1. 중요한 branch 또는 state transition
1. 일반적인 내부 진행 상황

로그가 적거나 많다는 사실 자체는 관찰 공백의 근거가 아니다.

## Stop

기존 runtime evidence만으로 선택한 질문에 직접 답할 수 있으면 수정하지 않는다.
