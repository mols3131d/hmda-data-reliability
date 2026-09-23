# 02 — Complete the Durable Quality Basis

## Goal

대표 utility comparison이 참조하는 durable quality basis가 OpenSpec이 요구하는 control discrimination을 실제로 모두 보존하게 한다.

## Scope

18번 리뷰의 F2만 처리한다.

Quality basis는 최소한 다음 semantic role을 구분하고 같은 case/revision에서 검증해야 한다.

- compliant positive → `PASS`
- deterministic fact/draft restatement negative → `FAIL`
- actionability/prioritization이 없는 hedging negative → `FAIL`

Control 의미를 `control_id` 문자열 규칙에 숨기지 않는다. 현재 canonical contract가 다른 명시적 representation을 채택했다면 그 구조를 따른다.

Representative proof가 세 control 결과를 durable evidence로 저장하고 comparison이 그 완전한 basis를 참조하게 한다. 이 작업에서 evaluator framework를 일반화하지 않는다.

## Evidence to Recheck

- `openspec/changes/review-ai-utility-evaluation/specs/reliability-agentic-review/spec.md`
- `src/hmda_reliability/review_ai/evaluation.py`
- `scripts/run_review_ai_utility_proof.py`
- `tests/review_ai/test_utility_evaluation.py`
- `tests/scripts/test_review_ai_utility_proof.py`

## Validation

- required role 하나가 빠지면 quality basis가 valid가 되지 않는다.
- 세 role의 expected/observed outcome이 맞아야 한다.
- case/revision mismatch가 fail-closed 한다.
- representative proof를 store/reload한 뒤 세 control 결과와 basis digest가 유지된다.
- comparison이 해당 complete basis digest를 참조한다.

## Done When

독립 hedging test가 존재하는 것에 그치지 않고, 실제 durable basis 자체가 세 required role을 모두 증명하면 완료한다. 완료 후에만 03으로 이동한다.
