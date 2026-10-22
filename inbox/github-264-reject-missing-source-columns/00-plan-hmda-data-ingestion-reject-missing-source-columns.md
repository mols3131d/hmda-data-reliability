---
type: plan
title: Reject Missing Columns in Mixed HMDA Sources
description: 다중 파일 적재에서 개별 원천의 필수 컬럼 누락을 정상 데이터로 처리하지 않도록 수정할 목표와 범위입니다.
---

# Reject Missing Columns in Mixed HMDA Sources

## Goal

여러 HMDA CSV/Parquet를 함께 적재할 때 개별 파일의 필수 컬럼이 없어도 `UNION ALL BY NAME` 결과가 이를 `NULL`로 채워 정상 적재되는 결함을 막는다. 결합된 테이블뿐 아니라 **각 입력 파일의 구조 계약**을 충족해야 성공하도록 한다.

## Evidence

PR #258 [G2/F1 mixed-source probe](https://github.com/mols3131d/hmda-data-reliability/blob/b6b47606bdabf69221eff94c8f9c69dc03b6cc57/inbox/github-258-cover-sdk-retry-classification/03-review-domain-test-design/validation.md#a1-mixed-source-schema)에서 정상 파일과 `income` 없는 파일을 함께 입력했을 때 full/partition load 모두 2행 성공을 반환했다. 해당 보고서는 수정 전 재현 근거이며, 착수 시 최신 `main`에서 재확인한다.

## Scope

- **In Scope:** `hmda_data.ingestion`의 파일별 required-column 검증과 full/partition 두 공개 적재 경로의 회귀 테스트.
- **Out of Scope:** 타입 강제, 실제 `NULL` 값 거부, 전체 ingestion 재설계, partition rollback·파일별 sibling 보호 등 별도 finding.
- **Boundary:** Full load의 현행 validation-after-replacement semantics와 partition 실패 시 기존 범위 보존 정책을 임의로 바꾸지 않는다.

## Acceptance

- 정상 파일 + 필수 컬럼 누락 파일을 섞으면 두 loader 모두 누락 컬럼을 식별할 수 있는 validation failure를 반환한다.
- Full load는 기존 실패 상태의 관찰 계약을, partition load는 실패 전 대상 행 집합·provenance를 유지한다.
- 컬럼은 존재하지만 값이 `NULL`인 파일 및 유효한 CSV/Parquet 혼합 적재는 계속 성공한다.
- 실패를 먼저 재현하는 테스트와 수정 후 관련 영역 검증을 같은 revision에서 기록한다.

## Next

최신 `main`에서 재현 → 관련 contract 대조 및 최소 구현 경계 결정 → test-first 수정 → 관련 테스트·CI 및 인간 리뷰.

## References

- [Source contract validation](../../openspec/specs/hmda-data-ingestion/spec.md)
- [G2 review](https://github.com/mols3131d/hmda-data-reliability/blob/b6b47606bdabf69221eff94c8f9c69dc03b6cc57/inbox/github-258-cover-sdk-retry-classification/03-review-domain-test-design/hmda-data/ingestion.md)
