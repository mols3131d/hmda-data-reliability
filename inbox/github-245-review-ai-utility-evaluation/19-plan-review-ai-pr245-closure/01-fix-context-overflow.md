# 01 — Close the Context Overflow Failure Boundary

## Goal

`build_bounded_review_context()`의 context-size overflow가 일반 Python exception으로 service 밖에 탈출하지 않고 안정적인 typed input rejection으로 닫히게 한다.

## Scope

18번 리뷰의 F1만 처리한다.

- context-size overflow를 나타내는 좁은 exception 또는 현재 contract에 맞는 equivalent failure를 사용한다.
- `review_null_spike()`가 해당 preflight failure를 provider 호출 전에 typed `INPUT_REJECTED`로 변환한다.
- 일반 `ValueError`를 넓게 catch해 programming defect를 입력 오류로 숨기지 않는다.
- Provider와 invocation evidence store는 이 rejection path에서 호출되지 않아야 한다.

새 retry framework, generic error hierarchy 또는 Langfuse integration을 추가하지 않는다.

## Evidence to Recheck

- `src/hmda_reliability/review_ai/context.py`
- `src/hmda_reliability/review_ai/prompt.py`
- `src/hmda_reliability/review_ai/service.py`
- `tests/review_ai/test_context.py`
- `tests/review_ai/test_service.py`
- [`../18-review-review-ai-high-confidence/README.md`](../18-review-review-ai-high-confidence/README.md)

## Validation

Oversized but otherwise valid input으로 service-level test를 실행한다.

- typed rejection이 반환된다.
- stable failure code가 존재한다.
- provider가 호출되지 않는다.
- evidence store가 호출되지 않는다.
- unrelated `ValueError`를 입력 오류로 삼키지 않는다.

관련 focused tests와 Python validation을 실행한다.

## Done When

현재 HEAD에서 context overflow가 public service failure contract 안에 머물고 해당 negative path가 test로 증명되면 완료한다. 완료 후에만 02로 이동한다.
