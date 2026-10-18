---
type: plan
title: Reject Malformed Lineage Graph Evidence
description: 손상된 dbt lineage manifest를 정상적인 영향 없음으로 처리하지 않도록 할 목표와 검증 조건입니다.
---

# Reject Malformed Lineage Graph Evidence

## Goal

dbt manifest의 graph container 구조가 잘못됐는데도 downstream/affected assets가 빈 **정상 성공 결과**로 처리되는 결함을 해결한다. 손상된 lineage evidence와 실제 영향 범위가 빈 상황은 구분해야 한다.

## Evidence

PR #258 [G5/I1 재현](https://github.com/mols3131d/hmda-data-reliability/blob/b6b47606bdabf69221eff94c8f9c69dc03b6cc57/inbox/github-258-cover-sdk-retry-classification/03-review-domain-test-design/validation.md#b3-malformed-lineage-object)에서 manifest `{"nodes":"bad","sources":[]}`가 syntactically valid JSON이지만 analyzer는 실패하지 않고 empty-impact success를 반환했다.

## Scope

- **In Scope:** impact manifest parser의 핵심 `nodes`·`sources` graph container 유효성 검증, 공개 analyzer의 typed failure, 정상/비정상 graph 회귀 테스트.
- **Out of Scope:** dbt lineage 모델 재설계, 모든 edge-level 구조 제약의 신규 확장, downstream 계산 알고리즘 변경.
- **Boundary:** 올바른 빈 graph는 성공 가능한 상태로 유지하고 비정상 자료만 거부한다.

## Acceptance

- `nodes` 또는 `sources`에 기대 구조와 다른 container를 둔 대표 manifest가 `ImpactAnalysisError`로 실패한다.
- 정상 빈 manifest와 실제 upstream→staging→mart graph의 기존 영향을 정확히 계산한다.
- Missing artifact·invalid JSON의 기존 failure contract를 유지하고 관련 테스트·CI를 검증한다.

## Next

최신 `main` 재현 → 최소 graph shape 검증 추가 → typed failure/정상 빈 graph 독립 검증 → 리뷰.

## References

- [Impact analysis contract](../../openspec/specs/reliability-impact-analysis/spec.md)
- [G5 review](https://github.com/mols3131d/hmda-data-reliability/blob/b6b47606bdabf69221eff94c8f9c69dc03b6cc57/inbox/github-258-cover-sdk-retry-classification/03-review-domain-test-design/reliability/impact.md)
