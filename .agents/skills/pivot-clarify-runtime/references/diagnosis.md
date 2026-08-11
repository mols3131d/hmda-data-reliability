# Diagnosis

runtime 문제를 모두 관찰하려 하지 않는다. **실행 후 복원하기 어려우며 오해 비용이 가장 큰 공백 하나**를 먼저 찾는다.

## Reconstruction Questions

다음 질문 중 실제로 답하기 어려운 것을 찾는다.

| Question | Typical signal |
| --- | --- |
| 어떤 경로를 탔는가? | 조건부 실행, skip, retry, fallback의 결과만 보인다. |
| 왜 이 결정이 내려졌는가? | 결과는 있지만 선택 근거가 남지 않는다. |
| 어떤 상태가 바뀌었는가? | mutation 전후나 commit 여부를 복원하기 어렵다. |
| 무엇이 실패했는가? | exception은 있으나 대상, 단계 또는 causal context가 부족하다. |
| 어떤 실행과 연결되는가? | 서로 다른 event/result를 같은 실행으로 묶기 어렵다. |

모든 질문을 동시에 해결하지 않는다. 실제 사용자·유지보수자가 반복적으로 다시 코드를 따라가야 하는 질문을 우선한다.

## Priority

오해했을 때 영향이 큰 순서로 본다.

1. destructive mutation, overwrite, recovery 같은 위험 작업
1. approval, validation, promotion 같은 gate
1. 외부 process·framework·database 실행과 실패
1. 중요한 branch 또는 state transition
1. 일반적인 내부 진행 상황

단순히 로그가 적다는 이유는 관찰 공백의 근거가 아니다.

## Responsibility Boundary

Evidence는 사건을 가장 잘 아는 책임 경계 가까이에 둔다.

- caller가 결과로 의존해야 하는 사실은 return/result surface를 우선한다.
- 실패를 번역하는 경계가 원인 context를 소유한다.
- framework가 실행을 소유하면 framework metadata/log surface를 우선한다.
- 여러 내부 단계의 시간적 흐름이 필요할 때만 logging을 고려한다.

관찰 공백의 주된 원인이 코드 구조나 contract 자체의 불명확성이라면 `pivot-clarify-code`로 분리한다. 실제 defect 여부를 판단해야 하면 review/debugging으로 분리한다.

## Stop Rule

기존 result, metadata, exception 또는 log만으로 질문에 충분히 답할 수 있으면 수정하지 않는다.
