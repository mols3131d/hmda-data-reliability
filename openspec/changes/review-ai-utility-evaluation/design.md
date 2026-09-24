---
type: openspec-spec-driven-tdd-design
category: design
title: "Utility Evaluation Boundaries"
description: "기존 review input/provenance 경계를 보존하면서 bounded context와 human comparison을 추가한다."
---

## Technical Delta

`review_ai` 내부에 context projection과 utility evaluation을 둔다. `BoundedReviewContext`는 기존 immutable `AgenticReviewInput`에서만 만들며, source별 priority와 stable evidence ID 정렬을 사용한다. Evidence payload는 context projection에서 제한된 JSON 값으로 잘라내고, context gap은 caller가 제공하지 않은 expected source와 Evidence로 확정할 수 없는 root-cause 성격을 별도 code로 표현한다. Context projection은 prompt canonical input과 invocation evidence에 포함되어 같은 application revision에서 재생성할 수 있어야 한다.

`AgenticReviewOutput`에는 backward-compatible default를 가진 `utility_contributions` collection을 추가한다. 기존 historical invocation JSON이 새 field 없이도 읽히도록 optional empty default를 사용한다. Human rubric은 output 전체를 평가하며 contribution의 존재 자체를 utility 통과 조건으로 사용하지 않는다. Contribution reference는 기존 provided Evidence subset에 대해 validator가 확인한다.

Evaluation은 provider 호출이나 LLM judge를 소유하지 않는다. `rubric_v1`은 다섯 criterion과 0–2 integer human score를 사용하며, 각 evaluation은 모든 criterion의 rationale을 저장한다. Positive, restatement-negative, hedging-negative fixture는 rubric이 추가 가치와 구체적 행동 가능성을 구분하는지 테스트하지만 runtime quality-basis model이나 durable control hierarchy를 만들지 않는다.

Comparison은 baseline과 candidate의 명시적 `output_kind`, 완전한 human rubric score, 동일 case/version/rubric/revision 및 deterministic facts를 확인하고, mismatch가 있으면 blocked evidence를 만든다. 별도 quality-basis hierarchy, proof bundle, create-only store 또는 synthetic score runner를 두지 않는다. Context overflow는 전용 typed preflight failure로 `input_rejected/context_too_large`에 매핑하고, canonical prompt의 draft Evidence reference는 bounded context에서 선택한 ID만 노출한다.

Comparison model은 invocation JSON을 수정하지 않고 `case_id`와 `case_version`, rubric identity, baseline/candidate invocation ID, change-under-test, criterion별 score delta, human decision/rationale를 한 record에 묶는다. 저장소는 이 slice의 책임이 아니며 호출자가 필요한 evidence를 직렬화할 수 있다. Baseline promotion은 이 slice가 자동으로 수행하지 않으며, human decision이 `accept`인 evidence만 promotion 후보로 표시한다. `blocked`/`inconclusive`는 fail-closed로 기록한다.

기존 `review_null_spike()`의 read-only/provider/provenance 순서와 `RecoveryProposal` + human approval boundary는 변경하지 않는다. `runtime_ai`와 deterministic Reliability contract에는 새 dependency를 추가하지 않는다.

## Verification Shape

- Context unit tests는 ordering, source provenance, missing/unconfirmed gap distinction, payload/collection bounds와 stable digest를 확인한다.
- Review contract/service tests는 utility contribution parse, evidence reference guard, prompt/provenance context projection과 legacy output compatibility를 확인한다.
- Evaluation unit/component tests는 five-criterion completeness, test-fixture control discrimination, baseline/candidate role 및 same-case comparison, mismatch/blocker와 JSON round-trip을 확인한다.
- Representative fixtures는 사람 점수를 미리 채운 proof로 가장하지 않고 comparison serialization/rendering을 검증한다. 실제 provider와 human evaluation은 별도 evidence 경계로 남긴다.
