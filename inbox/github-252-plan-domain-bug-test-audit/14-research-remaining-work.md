---
type: research
title: PR 252 Remaining Work
description: 현재 PR head의 남은 구현과 acceptance 조건을 코드·명세·CI에 대조하고 최소 후속 범위를 조사합니다.
tags:
  - reliability
  - testing
---

# PR 252 Remaining Work

> [!NOTE]
> 남은 제품 변경은 R-DET-01의 zero-threshold 의미 확정과 회귀 수정이다. 기존 네 수정 단위의 로컬 검증·독립 리뷰에 더해 조사 기준 head의 prospective-merge CI도 성공했다. `0`을 유지하면서 실제 양의 악화만 탐지하는 선택을 권장하지만, 이 Research가 계약 결정을 대신 확정하지는 않는다.

## Question

PR #252의 전체 완료에 어떤 구현·결정·검증이 남았으며, 이미 해소된 항목과 분리한 최소 후속 범위는 무엇인가?

## Scope

- 2026-10-17, PR Open / Draft / mergeable, head `69cc4002ad7fb51e116beec8ae83ff22b33f7d37`.
- GitHub가 반환한 base SHA는 `8bc62fa6ec995f2e57456d55712b36ff11b1f1d9`, main은 `6ed9882ae8bed628c24931b960c18327ac60f9af`다. 두 값을 혼동하지 않는다.
- Detector·threshold model·직접 소비자·기존 테스트·canonical spec, 현재 checklist와 CI·review evidence를 대조했다.
- Source/test/spec 변경이나 runtime 재실행은 하지 않았다. 기존 187개 파일 감사를 반복하지 않는다.

## Findings

### Current CI And Previous Fixes Are Verified

Head를 지정해 workflow run을 조회했을 때 [CI Lite 39018118751](https://github.com/mols3131d/hmda-data-reliability/actions/runs/39018118751)은 completed / success였다. Job `117354349801`의 Checkout prospective merge, Sync dependencies, Check Python dependency boundaries, Verify package build, Validate Python, Run selected tests가 모두 실제 success였다. Test step이 skip된 green이 아니다.

PR merge revision은 `45ff6151dd78d8d5f0d9cc9775e0e56507ed2bbd`이고 commit message는 head `69cc4002`를 main `6ed9882a`에 합친 revision임을 식별한다. 이 조합의 통합 CI 미확정은 해소됐다. 이후 head/base에는 자동 적용하지 않는다. Skip된 actionlint·OpenSpec·JSON/TOML·zizmor 등은 해당 변경 경로가 없는 검사다.

현재 source/test tree는 [독립 리뷰](13-review-remediation-implementation.md)의 revision `e49eee7352b0deab87f8c507f21606afc42e64c9`와 동일하다. [12](12-report-remediation-loops.md)의 926 passed / 2 skipped와 별도 Airflow 5 passed는 이전 직접 실행 근거이며 이번 조사에서 재실행한 수치가 아니다. 사람의 approval은 0이고 changes requested는 없다. Agent의 bounded clear는 사람의 approval이 아니다.

### Zero Is Currently A Valid Public Input

[Threshold model](../../src/hmda_reliability/reliability/detection/thresholds.py#L11)은 volume ratio와 null delta에 `ge=0.0`을 선언한다. [DetectionRequest](../../src/hmda_reliability/reliability/detection/request.py#L21)는 이를 공개 입력으로 받는다. `0`을 거부하면 지금 유효한 caller 입력이 invalid가 되는 호환성 변경이다.

[Detector](../../src/hmda_reliability/reliability/detection/detector.py#L51)는 `drop_ratio < threshold`, `delta < threshold`일 때만 제외한다. 변화량과 threshold가 모두 0이면 두 조건이 false라 volume/null incident를 생성한다. 이 source는 감사 baseline 이후 변경되지 않아 [08의 실제 재현](08-report-cloud-validation.md)이 여전히 적용된다.

기본값은 0.5/0.1이고 [quality gate](../../src/hmda_reliability/reliability/quality_gate.py#L18)는 1.0/0.05를 사용한다. 이 직접 소비자들이 zero를 사용한다고 주장할 근거는 없다. 영향은 zero를 명시한 caller의 경계값에 한정한다.

### Positive Threshold Equality Must Be Preserved

[Canonical spec](../../openspec/specs/reliability-incident-detection/spec.md#L25)의 volume/null requirement는 `이상`을 사용하고 현재 구현도 equality를 검출한다. [quality gate exact-delta regression](../../tests/reliability/test_quality_gate.py#L71)도 이 의미를 보호한다. `<`를 `<=`로만 바꾸면 양수 threshold와 정확히 같은 악화까지 제외하므로 적절하지 않다.

Spec의 Normal comparison은 `threshold를 넘지 않을 때` incident가 없다고 표현해 equality 해석이 specific requirement와 어긋날 여지가 있다. 후속 결정은 **실제 양의 악화 조건**과 **그 악화가 threshold 이상이라는 조건**을 분리해 문구·테스트·구현을 일치시켜야 한다. 동작 계약을 바꾸는 선택은 [OpenSpec boundary](../../openspec/README.md)에 따라 delta Spec에서 먼저 다룬다.

### Missing Baseline And Freshness Are Separate Boundaries

[06](06-review-reliability-detection-boundaries.md)의 R-DET-02는 baseline에 없는 null-rate를 0으로 간주하는 별도 Note다. 이를 이번 수정에 포함하면 비교 가능한 column 집합이라는 별도 계약 결정이 추가되므로 필수 범위로 승격하지 않는다.

Freshness는 baseline 대비 악화가 아니라 관측 age를 threshold와 비교한다. [freshness implementation](../../src/hmda_reliability/reliability/detection/detector.py#L119)과 canonical freshness scenario를 유지해야 하며 volume/null의 positive-delta guard를 모든 규칙에 적용해서는 안 된다.

## Options

| Criterion | Allow Zero, Detect Positive Degradation | Reject Zero |
| --- | --- | --- |
| 기존 valid input | 유지 | 입력 호환성 변경 |
| 변화 없는 profile | volume/null incident 없음 | 입력 단계 거부 |
| 작은 실제 악화 | 0 설정에서 탐지 | 양수 임계값 별도 선택 필요 |
| 주 변경 위치 | detector 두 분기와 회귀·명세 정합화 | threshold validation, caller/config, 회귀·명세 변경 |
| 현재 평가 | 권장: 기존 설정 surface를 보존하는 최소 선택 | 0 금지가 제품 정책일 때 선택 |

권장은 분석 결과이며 아직 채택된 결정이 아니다. 기존 질문에 대한 사용자 답변은 없고, 이 조사 요청을 특정 선택의 승인으로 해석하지 않았다.

## Implications

남은 항목은 [체크리스트](03-plan-audit-completion-checklist.md)의 I5와 I8이며 기존 I1–I4·I6을 다시 구현할 필요는 없다.

| Step | Needed result |
| --- | --- |
| 계약 선택 | 0 허용/거부, 양수 equality 유지와 Normal comparison 문구 정합화 |
| 회귀 RED | 무변화, volume만 악화, null만 악화, 둘 다 악화, 개선, 양수 exact-threshold, zero-row baseline의 독립 oracle |
| 최소 구현 GREEN | 좁은 owner만 수정하고 schema/freshness 규칙 유지 |
| 영향 검증 | basic detector·quality gate부터 검증한 뒤 source 변경에 해당하는 전체 CI |
| Independent gate | detector 변경 독립 검토; 기존 네 단위 clear는 unchanged 범위에서 재사용 |
| Delivery/readiness | 현재 revision으로 03/07과 PR을 갱신하고 전체 acceptance 재판정 |

Local full suite의 두 skip(zizmor cache, Windows prerequisite)과 외부 LLM/Langfuse live 미실행은 이 bounded detector 작업의 필수 구현 항목이 아니다. Ready 전환·approval·merge는 인간 권한으로 남긴다.

## Open Questions

- `0` 허용 + 양의 악화만 탐지하는 권장안을 채택할지, 설정에서 `0`을 금지할지 미확정이다.
- 후속 변경의 CI·독립 리뷰는 해당 변경 후 갱신해야 한다. 이번 성공은 조사 기준 head에 대한 근거다.
