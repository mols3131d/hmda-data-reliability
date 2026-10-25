---
type: review
title: Reliability Impact Test Design Review
description: dbt lineage 해석과 downstream 영향 분석에서 정상 JSON의 구조 손상을 검출하는지 검토합니다.
---

# Reliability Impact Test Design Review

> [!NOTE]
> 정상 graph의 exact downstream oracle은 강하다. 구조가 잘못된 manifest를 영향 없음으로 성공 처리하는 경로를 놓친다.

- **Target**: Reliability impact.
- **Revision**: `3ab899100fc0b35e23d464bd761f3b144a978ae7`.
- **Scope**: [test_impact_analysis.py](../../../../tests/reliability/test_impact_analysis.py) 전체, analyzer·manifest parser와 canonical 계약.

## Findings

| ID | Severity | Finding | Action |
| --- | --- | --- | --- |
| I1 | Major | parse 가능한 JSON의 잘못된 graph container를 빈 graph로 낮춰 성공한다 | 대표 구조 오류에 typed failure oracle 추가 |

## Design Assessment

22·46·70행의 정상 사례는 실제 JSON graph에서 source→staging→mart, model name/node ID, 정확한 affected-assets·artifact path·evidence refs를 비교한다. Domain traversal을 mock하지 않는다. Run-results는 존재하는 `{}` fixture이므로 실제 dbt 실행 성공을 증명하는 입력은 아니다.

### I1 — Major: Malformed Graph Shape

#### Locations

- [test_impact_analysis.py](../../../../tests/reliability/test_impact_analysis.py)
  - 90행의 invalid-manifest 사례는 `not-json`만 사용한다.
- [manifest.py](../../../../src/hmda_reliability/reliability/impact/manifest.py)
  - 56행 이후 resource container 해석에서 잘못된 타입을 건너뛴다.
- [impact Spec](../../../../openspec/specs/reliability-impact-analysis/spec.md)
  - `Lineage artifact validation`.

#### Evidence

Caller [B3 probe](../validation.md#b3-malformed-lineage-object)에서 manifest `{"nodes":"bad","sources":[]}`와 존재하는 run-results를 입력했을 때 success와 빈 downstream·affected-assets를 반환했다. JSON syntax/root-type와 missing run-results 방어는 있지만 이 내부 shape 오류는 구별하지 못한다.

#### Impact

손상된 증거와 실제 영향 없음이 같은 성공 결과가 된다. Incident 후속 조치가 불완전한 영향 범위를 정상 결과로 사용할 수 있다.

#### Action

정상 JSON이지만 `nodes`·`sources`의 container가 잘못된 대표 사례에 `ImpactAnalysisError`를 요구한다. 정상적인 빈 graph와는 구분한다. `depends_on.nodes` 등 edge-level 구조 오류는 같은 parser의 후속 검토 대상으로 묶을 수 있지만 이번 probe에서 실행한 것으로 표시하지 않는다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | 독립 full-body 검토 | Batch B quality/adversarial |
| ✅ Pass | 현재 정상 suite | [실행 근거](../validation.md#test-execution) |
| ❌ Fail | 구조 오류 계약 probe | malformed graph가 empty success로 반환됨 |
