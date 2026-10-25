---
type: review
title: HMDA Data Test Design Review
description: HMDA Data의 ingestion·EDA·synthetic와 contracts 하위 영역의 테스트 설계 판정을 모아 확인합니다.
---

# HMDA Data Test Design Review

> [!NOTE]
> 실제 파일·DB와 고정 값 oracle을 쓰는 점은 강하다. 원본 보존과 파일별 구조 검증에서는 현재 오동작을 확인했으며, 일부 destructive 경계의 회귀 보호가 부족하다.

- **Target**: HMDA Data domain과 추적 중인 4개 하위 패키지.
- **Revision**: `3ab899100fc0b35e23d464bd761f3b144a978ae7`.
- **Scope**: test 6개·support 2개 전체를 quality/adversarial이 독립 검토. Source·Spec은 관련 경로를 targeted 대조했다.

## Findings

| ID | Severity | Finding | Action |
| --- | --- | --- | --- |
| H1 | Major | source/output overlap에서 원본 삭제 | [Synthetic F1](synthetic.md#f1--major-overlapping-input-and-output) |
| H2 | Major | 다중 파일의 필수 컬럼 누락이 합쳐진 schema에 가려짐 | [Ingestion F1](ingestion.md#f1--major-mixed-source-schema) |
| H3 | Major | DELETE 후 INSERT 실패의 atomic rollback 보호 부족 | [Ingestion F2](ingestion.md#f2--major-mid-replacement-rollback) |
| H4 | Major | file-scoped 교체가 같은 연도 sibling을 보존하는 oracle 부족 | [Ingestion F3](ingestion.md#f3--major-same-year-sibling-preservation) |
| H5 | Minor | 증거 갱신 cleanup 실패로 JSON·Markdown 불일치 | [EDA F1](eda.md#f1--minor-evidence-pair-cleanup-boundary) |
| H6 | Minor | numeric summary 분위수·음수의 독립 기대값 부족 | [EDA F2](eda.md#f2--minor-numeric-summary-oracle) |
| H7 | Minor | fake lock이 loader의 실제 DB path 연결 오류를 가릴 수 있음 | [Ingestion F4](ingestion.md#f4--minor-loader-lock-identity) |
| H8 | Minor | row-drop의 희소 연도 보존 oracle 부족 | [Synthetic F2](synthetic.md#f2--minor-sparse-year-row-drop) |

H1·H2·H5는 현재 구현에 대한 임시 데이터 probe로 확인했다. 나머지는 기존 보호장치와 대조한 정적 설계 공백이다. 전부 후속 작업 제안이며 이번 보고 작업에서 구현하지 않았다.

## Subdomain Reports

| Subdomain | What The Tests Establish | Report |
| --- | --- | --- |
| contracts | docstring만 있는 placeholder; 별도 executable model 없음 | [Contracts](contracts.md) |
| ingestion | 파일 발견, 값·provenance 보존, 반복 적재, CAS·temporal rejection, 실제 partition 조회 | [Ingestion](ingestion.md) |
| eda | 고정 row/null/grain, portable evidence, dirty revision 거부, read-only/source bytes·cleanup | [EDA](eda.md) |
| synthetic | 실제 Parquet의 결함 크기·type, strict null 증가, 입력 순서 결정성, 연도 naming·ingestion 연결 | [Synthetic](synthetic.md) |

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | 두 관점의 전체 test assertion 검토 | [파일별 inventory](../inventory.md), Batch A |
| ✅ Pass | 현재 suite 실행 | [954 passed / 2 skipped](../validation.md#test-execution), 전체 기준 |
| ❌ Fail | 세 계약 반례 | [A1–A3](../validation.md#confirmed-counterexamples) |
| ⚪ Not Verified | 정적 gap의 mutation 실행 | 통과 가능한 오류를 도출했으며 실제 mutant suite는 미실행 |

## Risks And Limits

전체 실제 HMDA 원천의 재분석이나 모든 concurrency 조합을 검증한 보고서는 아니다. 테스트 통과나 독립 검토 완료를 인간 검토의 일괄 생략 근거로 해석할 수 없다.
