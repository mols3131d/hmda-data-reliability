---
type: review
title: CI Test Design Review
description: CI classifier·OpenSpec routing·선택 실행·workflow 진입과 prospective merge 검사 테스트의 fail-safe 경계를 검토합니다.
---

# CI Test Design Review

> [!NOTE]
> 선택기·명령 실패·중복 검사의 oracle은 구체적이다. 불확실한 OpenSpec inventory와 workflow 생성·revision 계약은 보강이 필요하다.

- **Target**: CI selection·admission·execution 테스트.
- **Revision**: `3ab899100fc0b35e23d464bd761f3b144a978ae7`.
- **Scope**: [CI tests](../../../../tests/scripts/ci/)의 test 6개·support 3개 전체, 실제 classifier/runner·workflow·CI 계약 대조.

## Findings

| ID | Severity | Finding | Action |
| --- | --- | --- | --- |
| C1 | Major | uncertain Change inventory가 OpenSpec 구조 검증을 넓히지 않는다 | bulk validation 또는 selector failure를 oracle로 고정 |
| C2 | Major | top-level PR trigger·path filter·checkout revision을 검증하지 않는다 | 전체 workflow의 진입·prospective merge 정책 검사 |

## Design Assessment

| Area | Scenario And Independent Oracle | Boundary And Limit |
| --- | --- | --- |
| Changed files/classifier | rename/delete·invalid comparison·missing test dir의 정확한 selector와 실패 | 실제 임시 Git/CLI, unknown scope에서 full Python 선택 보호 |
| OpenSpec | canonical Spec→정상 active Change pairing, unknown capability bulk | uncertain inventory의 fallback은 C1 |
| Python/pytest | selected target·argv·exit, 성공한 boundary 이후에만 guard 중복 제외 | 외부 tool은 fake command; skip 자체를 broad success로 보지 않음 |
| Workflow wiring | step 조건·순서·환경, action pinning, credentials 비보존, 실패 전파 | fixture가 steps만 보여 top-level entry는 C2 |
| Audits | pinned zizmor/actionlint command·flags·failure propagation | 실제 audit cache 사례 1개는 이번 환경에서 skip |

주요 근거는 [classifier](../../../../tests/scripts/ci/test_ci_classifier.py) 174·186행, [OpenSpec](../../../../tests/scripts/ci/test_ci_classifier_openspec.py) 89행, [Python routing](../../../../tests/scripts/ci/test_ci_classifier_python.py), [pytest](../../../../tests/scripts/ci/test_ci_pytest.py) 116행, [steps](../../../../tests/scripts/ci/test_ci_steps.py) 495행, [workflow](../../../../tests/scripts/ci/test_ci_workflow.py)이다.

### C1 — Major: Uncertain OpenSpec Inventory

#### Locations: C1

- [test_ci_classifier_openspec.py](../../../../tests/scripts/ci/test_ci_classifier_openspec.py)
  - 정상 active Change pairing이 중심이다.
- [classify_openspec.py](../../../../scripts/ci/classify_openspec.py)
  - `add_related_changes`의 uncertainty fallback은 full test/type만 선택한다.
- [run_checks.py](../../../../scripts/ci/run_checks.py)
  - bulk가 false이면 선택된 Spec/Change만 검증한다.
- [change-impact 계약](../../../../docs/development/ci/change-impact.md)
  - 영향 범위를 확정할 수 없을 때 검증 범위를 안전하게 넓혀야 한다.

#### Evidence: C1

Lead의 실제 CLI probe에서 missing inventory·symlinked Change·잘못된 related path 모두 exit 0, `full_tests/full_type=true`였지만 `openspec_bulk=false`, Spec은 `example-capability` 하나, Change targets는 빈 값이었다. [E2 실행 기록](../validation.md#e2-uncertain-openspec-routing)에서 명령·fixture 경계를 확인한다.

정상 pairing·unknown capability의 bulk·전체 Python 검증 선택은 이미 보호된다. Canonical Spec 변경은 원래 full Python이므로 uncertain fallback이 OpenSpec 구조 검사에는 아무 변화를 주지 않는 것이 문제다.

#### Impact: C1

관련 active Change를 확정하지 못해도 해당 구조 검증은 생략될 수 있다. 전체 pytest/type이 문서·Change 구조의 유효성 검사를 대신하지 않는다.

#### Action: C1

대표 uncertainty case를 추가하고 필요한 전체 OpenSpec 검증 또는 selector failure를 요구한다. 정황별로 안전한 fallback을 선택하되 성공한 좁은 검증으로 uncertainty를 숨기지 않는다. 이번 보고에서 selector를 수정하지 않았다.

### C2 — Major: Workflow Entry And Revision

#### Locations: C2

- [CI conftest](../../../../tests/scripts/ci/conftest.py)
  - `workflow_steps`가 `jobs.check.steps`만 반환한다.
- [test_ci_workflow.py](../../../../tests/scripts/ci/test_ci_workflow.py)
  - checkout SHA·credential은 검사하지만 trigger·ref는 검사하지 않는다.
- [admission 계약](../../../../docs/development/ci/admission.md)
  - main PR의 prospective merge 검증.

#### Evidence: C2

Current workflow는 정상이다. 격리 복사본에서 PR entry에 `paths-ignore: ['src/**']`를 넣거나 checkout을 PR head ref로 바꿔도 기존 bootstrap+workflow 58개가 모두 통과했다. 전체 workflow를 보는 witness는 각각 실패했다. [E1 negative control](../validation.md#e1-bootstrap-and-workflow-negative-controls)은 YAML 구조 검증이며 실제 hosted GitHub 이벤트 실험은 아니다.

#### Impact: C2

선택기가 정확해도 workflow가 시작하지 않거나 다른 revision을 검사하는 회귀를 놓칠 수 있다. 현재 remote branch protection이나 실제 merge 우회가 확인됐다는 의미는 아니다.

#### Action: C2

전체 workflow의 `pull_request/main`, workflow-level path filter 부재, prospective merge checkout 구성을 작은 고정 contract test로 확인한다. 기존 step pinning·failure propagation oracle은 유지한다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | 독립 full-body·helper 검토 | Batch E 두 관점, 9개 CI 파일 |
| ❌ Fail | 현재 uncertain inventory fail-safe | Lead CLI 3개 fixture의 좁은 OpenSpec 선택 |
| ✅ Pass | 격리 workflow 반례 구별력 | 기존 tests 유지 통과·새 policy witness 실패 |
| ⚪ Not Verified | hosted Actions·실제 OpenSpec CLI validation | selector 실행과 외부 도구 실행을 구분 |
