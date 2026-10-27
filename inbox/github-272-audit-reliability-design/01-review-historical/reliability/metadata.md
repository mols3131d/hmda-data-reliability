---
type: review
title: Reliability Metadata Test Design Review
description: 실제 DuckDB에서 수집한 metadata evidence의 필드·오류 경계와 테스트 oracle을 검토합니다.
---

> [!WARNING]
> Historical evidence only: PR #258 (`bdce0f4e`). 이전 findings는 현재 main의 결함/승인 근거가 아닙니다. [새 plan](../../00-plan-reliability-tests.md)에 따라 재검증 후 판정합니다.

# Reliability Metadata Test Design Review

> [!NOTE]
> 실제 DB의 exact schema·count·timestamp를 검사한다. 이 범위에서 추가 material finding은 확인하지 못했다.

- **Target**: Reliability metadata.
- **Revision**: `3ab899100fc0b35e23d464bd761f3b144a978ae7`.
- **Scope**: [test_table_metadata_evidence.py](../../../../tests/reliability/test_table_metadata_evidence.py) 전체와 관련 builder·계약.

## Findings

채택한 material finding은 없다. Schema hash의 단독 oracle은 prefix 수준이지만, 실제 column/type/nullability 비교와 [profile의 schema 변화 테스트](profiling.md)가 보완한다. 이를 metadata 전체가 검증되지 않는 문제로 확대하지 않는다.

## Design Assessment

19행의 정상 사례는 실제 DuckDB에 만든 table에서 정확한 컬럼·type·nullability, row count `1`, evidence identity와 고정 timestamp를 비교한다. 57행의 missing-table 사례는 domain error를 요구한다. Builder·DB 조회를 mock하지 않아 schema 수집 자체가 경로에 남는다.

이 테스트는 metadata 수집 계약의 증거다. 모든 DB adapter·운영 테이블 규모 또는 content identity의 모든 민감도를 검증하는 것은 아니다. Content와 complete-table identity는 [Profiling 리뷰](profiling.md)의 별도 oracle로 연결한다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | 독립 body·oracle 검토 | Batch B quality/adversarial |
| ✅ Pass | 현재 실행 | [전체 실행 근거](https://github.com/mols3131d/hmda-data-reliability/blob/bdce0f4e8e871b1301bac8f8ab3a37c7ba50bd91/inbox/github-258-cover-sdk-retry-classification/03-review-domain-test-design/validation.md#test-execution) |
