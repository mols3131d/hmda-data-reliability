# 03 — Align Provider-Visible and Allowed Evidence IDs

## Goal

Provider가 prompt에서 볼 수 있는 citable Evidence ID 집합과 deterministic validator의 allowlist를 같은 bounded selection으로 만든다.

## Scope

18번 리뷰의 F3만 처리한다.

현재 설계가 유지된다면 가장 작은 변경은 canonical prompt의 `draft.evidence_refs` projection도 selected bounded Evidence ID set으로 제한하는 것이다. 원본 `RemediationDraft` 자체를 변경할 필요는 없다.

다른 evidence-selection 정책, RAG, broader context retrieval 또는 prompt redesign을 이 작업에 섞지 않는다.

## Evidence to Recheck

- `src/hmda_reliability/review_ai/contracts.py`
- `src/hmda_reliability/review_ai/context.py`
- `src/hmda_reliability/review_ai/prompt.py`
- `src/hmda_reliability/review_ai/service.py`
- `src/hmda_reliability/review_ai/validator.py`
- `tests/review_ai/test_prompt_provider.py`
- `tests/review_ai/test_validator.py`

## Validation

`max_evidence`보다 많은 valid Evidence를 가진 input을 사용한다.

- top-level prompt evidence는 selected set만 노출한다.
- draft projection의 citable refs도 같은 selected set을 사용한다.
- validator allowlist가 그 집합과 동일하다.
- omitted evidence를 provider-visible ID로 남기지 않는다.
- 실제 fabricated ID는 계속 거부한다.

## Done When

Provider가 실제로 본 유효 ID를 validator가 fabricated evidence로 오판할 수 있는 경로가 없어지고 regression test가 이를 고정하면 완료한다. 완료 후에만 04로 이동한다.
