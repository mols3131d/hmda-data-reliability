---
type: plan
title: Bind Recovery Profile to Approved Observation Scope
description: Recovery 성공 증거의 profile 범위가 승인된 observation과 어긋나는 문제를 막기 위한 목표입니다.
---

# Bind Recovery Profile to Approved Observation Scope

## Goal

성공한 복구의 검증 profile이 실제 승인된 observation 범위와 다른 데이터 집합을 측정하면서도 `validation_passed=True`로 반환되는 결함을 막는다. Profile population이 복구 대상 observation과 일치하거나 잘못된 요청을 거부하도록 한다.

## Evidence

PR #258 [R2/B2 재현](https://github.com/mols3131d/hmda-data-reliability/blob/b6b47606bdabf69221eff94c8f9c69dc03b6cc57/inbox/github-258-cover-sdk-retry-classification/03-review-domain-test-design/validation.md#b2-profile-scope-alignment)에서 정상 요청의 `partition_column`만 `income`으로 바꾸자 partition `2025`의 실제 observation은 2행인데 backfill/schema 두 API가 0행 profile을 성공 증거로 반환했다.

## Scope

- **In Scope:** 두 recovery 요청의 profile discriminator/partition 범위 검증, request와 검증 후 실제 profile evidence의 정렬, 회귀 테스트.
- **Out of Scope:** content identity 알고리즘, 임의의 profile 품질 threshold 신설, 승인 없는 recovery 허용, 무관한 profile 지표 확대.
- **Boundary:** 현행에서 정상인 `activity_year`·`source_year` 동등 범위를 유지하고 mutation/observation 범위 구분을 보존한다.

## Acceptance

- 정상 승인된 요청에서 `partition_column="income"`으로 범위만 어긋나게 만든 경우 두 API 모두 유효한 성공 profile을 반환하지 않는다.
- 거부 경로라면 target state가 유지되고, 정렬 경로라면 검증된 profile population이 실제 승인 observation과 일치한다.
- 정상 backfill 및 table-wide schema recovery, replay/approval 경계는 유지한다.
- 현재 코드에서 실패를 고정한 테스트와 수정 후 관련 검증 근거를 남긴다.

## Next

최신 `main` 재현 → 현행 정본과 허용 동등 범위 확인 → 최소 request/profile boundary 수정 → 회귀 테스트·리뷰.

## References

- [Backfill recovery contract](../../openspec/specs/reliability-recovery-backfill/spec.md)
- [Schema recovery contract](../../openspec/specs/reliability-schema-recovery/spec.md)
- [R2 review](https://github.com/mols3131d/hmda-data-reliability/blob/b6b47606bdabf69221eff94c8f9c69dc03b6cc57/inbox/github-258-cover-sdk-retry-classification/03-review-domain-test-design/reliability/recovery.md)
