---
type: plan
title: Preserve Committed Recovery Evidence on Cleanup Failure
description: 복구 커밋 뒤 staging 정리가 실패하더라도 실제 변경 상태와 후속 조치 근거를 잃지 않도록 할 목표입니다.
---

# Preserve Committed Recovery Evidence on Cleanup Failure

## Goal

이미 commit된 복구가 staging 임시 디렉터리 종료 오류로 실패처럼 반환될 때 **실제 mutation 완료 상태와 reconciliation 근거를 잃지 않도록** 한다. 오류를 무시하거나 완료된 mutation을 rollback됐다고 주장하지 않는다.

## Evidence

PR #258 [R1/B1 재현](https://github.com/mols3131d/hmda-data-reliability/blob/b6b47606bdabf69221eff94c8f9c69dc03b6cc57/inbox/github-258-cover-sdk-retry-classification/03-review-domain-test-design/validation.md#b1-committed-recovery-cleanup)에서 실제 target은 expected-after였지만 backfill은 mutation metadata 없는 `BackfillValidationError`, schema recovery는 raw `OSError`를 반환했다. 두 경로에서 같은 post-commit cleanup 경계가 문제였다.

## Scope

- **In Scope:** partition/backfill과 schema recovery 두 executor의 **commit 이후 staging 종료 오류** 처리 및 actual target 재조회를 통한 회귀 검증.
- **Out of Scope:** 승인·권한 모델 변경, commit 전 rollback 로직 재작성, 자동 재실행·중복 mutation, 모든 filesystem failure의 일반 정책.
- **Decision Needed:** post-commit cleanup 오류를 어떤 typed result/error로 노출할지는 기존 recovery 계약과 호출자 소비 방식에 맞춰 구현 전에 정한다. 핵심은 실제 after-state와 mutation/reconciliation evidence 보존이다.

## Acceptance

- 정상 commit 이후 staging cleanup 종료만 `OSError`로 주입했을 때 두 API 모두 완료된 mutation 사실을 은폐하지 않는다.
- 별도 DB 조회로 actual after-state를 검증하고, 호출자가 정상 완료와 후속 확인 필요 상태를 구분할 mutation/reconciliation evidence를 확인한다.
- Commit 전 실패와 rollback, 기존 승인 경계 및 정상 recovery 경로는 유지한다.
- 회귀 테스트·관련 검증 실행 결과를 해당 PR에서 직접 기록한다.

## Next

최신 `main` 재현 → 반환 계약과 기존 caller 확인 → 최소 예외 경계 수정 및 test-first 검증 → 리뷰.

## References

- [Backfill recovery contract](../../openspec/specs/reliability-recovery-backfill/spec.md)
- [Schema recovery contract](../../openspec/specs/reliability-schema-recovery/spec.md)
- [R1 review](https://github.com/mols3131d/hmda-data-reliability/blob/b6b47606bdabf69221eff94c8f9c69dc03b6cc57/inbox/github-258-cover-sdk-retry-classification/03-review-domain-test-design/reliability/recovery.md)
