---
type: openspec-spec-driven-tdd-design
category: design
title: "Utility Evaluation Boundaries"
description: "기존 review input/provenance 경계를 보존하면서 bounded context와 human comparison을 추가한다."
---

## Technical Delta

`review_ai` 내부에 context projection과 utility evaluation을 둔다. `BoundedReviewContext`는 기존 immutable `AgenticReviewInput`에서만 만들며, source별 priority와 stable evidence ID 정렬을 사용한다. Evidence payload는 context projection에서 제한된 JSON 값으로 잘라내고, context gap은 caller가 제공하지 않은 expected source와 Evidence로 확정할 수 없는 root-cause 성격을 별도 code로 표현한다. Context projection은 prompt canonical input과 invocation evidence에 포함되어 같은 application revision에서 재생성할 수 있어야 한다.

`AgenticReviewOutput`에는 backward-compatible default를 가진 `utility_contributions` collection을 추가한다. 기존 historical invocation JSON이 새 field 없이도 읽히도록 optional empty default를 사용하고, 새 utility evaluation은 contribution이 있는 output만 utility proof candidate로 평가한다. Contribution reference는 기존 provided Evidence subset에 대해 validator가 확인한다.

Evaluation은 provider 호출이나 LLM judge를 소유하지 않는다. `rubric_v1`은 다섯 criterion과 0–2 integer human score를 사용하며, 각 evaluation은 모든 criterion의 rationale을 저장한다. Control fixture는 사람이 미리 작성한 positive/negative output과 score를 사용하고, evaluator는 score threshold와 expected verdict를 결정론적으로 검증한다.

Comparison record는 invocation JSON을 수정하지 않는 별도 create-only JSON evidence다. `case_id`와 `case_version`, rubric identity, baseline/candidate invocation ID, change-under-test, criterion별 score delta, human decision/rationale를 한 record에 묶는다. Baseline promotion은 이 slice가 자동으로 수행하지 않으며, human decision이 `accept`인 evidence만 promotion 후보로 표시한다. `blocked`/`inconclusive`는 fail-closed로 기록한다.

기존 `review_null_spike()`의 read-only/provider/provenance 순서와 `RecoveryProposal` + human approval boundary는 변경하지 않는다. `runtime_ai`와 deterministic Reliability contract에는 새 dependency를 추가하지 않는다.

## Verification Shape

- Context unit tests는 ordering, source provenance, missing/unconfirmed gap distinction, payload/collection bounds와 stable digest를 확인한다.
- Review contract/service tests는 utility contribution parse, evidence reference guard, prompt/provenance context projection과 legacy output compatibility를 확인한다.
- Evaluation unit/component tests는 five-criterion completeness, positive/negative control discrimination, same-case comparison, mismatch/blocker와 create-only reload을 확인한다.
- Controlled representative fixture는 network 없이 baseline/candidate records와 human decision evidence를 생성하고, 실제 provider proof는 별도 opt-in 경계로 남긴다.
