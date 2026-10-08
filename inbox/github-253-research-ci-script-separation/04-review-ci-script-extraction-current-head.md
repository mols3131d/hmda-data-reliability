---
type: review
title: CI Script Extraction Current Head Review
description: PR #253의 CI script extraction 리뷰를 baseline과 재현 근거로 보정하고 과거 reviewed revision, 기존 검증 공백과 로컬 보완 상태를 구분한다.
tags:
  - ci
  - github-actions
  - testing
---

# CI Script Extraction Current Head Review

> [!IMPORTANT]
> **Corrected assessment**: F1은 이번 변경이 새로 만든 회귀가 아니라 기존의 필수 test target 검증 공백이다. `tach=true` 복구만으로 누락을 검출할 수 있다는 권고는 철회한다. 새 correctness blocker를 입증하지는 못했으며, 원 리뷰 시점의 PR 설명에는 별도의 readiness 보완이 필요했다. 아래 로컬 보완은 원격 반영이나 현재 PR의 approval을 뜻하지 않는다.

- **Target**: PR [#253](https://github.com/mols3131d/hmda-data-reliability/pull/253)
- **Revision**: branch `agent/research-ci-script-separation`, reviewed base `5532dca2fd93696d40ba870471fa2359c5662335`, reviewed head `60e73c07a0386a43d165955e46bb74f3a6a9def3`. 2026-10-03 보정과 로컬 검증은 HEAD `21fbaa9f72e4193a32259bd8f4853f83838b5e08` 위의 미커밋 작업 트리를 기준으로 한다. 과거 reviewed pair는 유지한다.
- **Scope**: 원 리뷰는 CI workflow, scripts, classifier routing, contract tests와 CI/testing 문서를 다뤘다. 이번 보정은 F1의 원인·수정안, 관련 negative control, 로컬 계약 테스트 보완과 evidence provenance에 한정한다. Extraction 전체를 새로 검토한 결과는 아니다.

원 리뷰는 subagent를 호출할 수 없는 환경에서 같은 컨텍스트로 baseline·diff·test·CI evidence를 검증했다. 이 한계는 보정 후에도 유지하며 과거 리뷰를 독립 `review-lead` 결과로 소급 승격하지 않는다.

## Findings

| ID | Severity | Finding | Action |
| --- | --- | --- | --- |
| F1 | Minor | Baseline과 reviewed head 모두 Tach step의 필수 pytest target 누락을 검출하지 못한다. | 독립 target oracle로 보완한다. `tach=true` 복구 권고는 철회한다. |
| F2 | Major | 원 리뷰 시점의 PR 설명이 구현·검증 상태를 반영하지 않았다. | 현재 원격 head 기준으로 설명을 갱신하고 미커밋 로컬 보완을 구분한다. |

## Details

### F1: Required Target Coverage

Minor, 기존 공백이다. 이를 CI-only routing 변경의 새 regression으로 단정한 원 설명은 정정한다.

#### F1 Locations

- [CI workflow](../../.github/workflows/ci-lite.yml)
- [Classifier](../../scripts/ci/classify_changes.sh)
- [Classifier tests](../../tests/scripts/test_ci_classifier.py)
- [CI step tests](../../tests/scripts/test_ci_steps.py)

#### F1 Evidence

Baseline은 workflow 변경에서 `tach=true`를 선택했다. Reviewed head는 workflow와 CI helper 변경을 두 CI 계약 모듈로 라우팅하고 source·dependency·Tach 변경은 별도로 검증한다. 이는 [구현 계획](00-plan-ci-validation-and-script-extraction.md#scope)의 의도된 선택이며 `tach=false` 자체가 defect는 아니다.

Baseline과 reviewed head의 workflow assertion은 setup 조건과 `tach check` 문자열을 확인하지만 세 필수 pytest target 전체를 독립적인 기대값으로 검사하지 않았다. 보완 전 두 계약 모듈은 정상 상태에서 114 passed였고, YAML을 읽는 순간에만 `tests/scripts/test_tach_config.py`를 제거한 메모리 내 변형에서도 114 passed였다. `tach=true`를 강제한 기존 setup·command assertion도 통과했다. 이 실험은 계약 테스트의 false green을 재현한 것이며 변형된 실제 Actions run을 실행한 것은 아니다.

#### F1 Impact

후속 workflow 수정에서 필수 regression test가 명령에서 빠져도 기존 계약 테스트는 누락을 검출하지 못한다. 그러나 이는 baseline에도 있었으며, `tach=true`여도 변경된 명령에 남은 대상만 실행한다. 실행 횟수 증가와 누락 검출은 서로 다른 주장이다.

#### F1 Action

CI-only routing과 source·dependency 검증 범위는 유지한다. [새 계약 테스트](../../tests/scripts/test_ci_steps.py)는 실제 YAML의 Tach step을 fake CLI로 실행하고 selector, `tach check` 및 세 pytest target을 독립적인 argv 기대값과 비교한다. 두 필수 명령의 실패 전파도 검증한다. 로컬 보완 후 각 target을 하나씩 제거한 세 negative control이 모두 assertion에서 실패했다.

### F2: Description Readiness

Major, 원 리뷰 시점의 lifecycle evidence gap이며 code correctness finding과 구분한다.

#### F2 Locations

- [PR #253](https://github.com/mols3131d/hmda-data-reliability/pull/253)
- [Review readiness contract](../../docs/development/vcs-git/pull-request.md#review-readiness)

#### F2 Evidence

원 리뷰의 PR 설명은 조사 단계만 서술하고 `head: 4f6c996`을 기록했다. 보정 시작 시 원격 head는 `21fbaa9f72e4193a32259bd8f4853f83838b5e08`이지만 설명은 같은 상태였다. 실제 diff에는 script extraction과 contract tests가 포함되므로 description의 scope와 validation이 현재 변경을 반영해야 한다.

#### F2 Action

PR 설명을 현재 원격 head의 구현·검증 근거로 갱신한다. 로컬 보완은 아직 미커밋 상태이므로 원격 head에 포함됐다고 표현하지 않는다. 보고서의 과거 reviewed head가 현재와 다르다는 사실 자체는 blocker가 아니며 과거 revision metadata를 현재 head로 덮어쓰지 않는다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| Pass | Exact revision comparison | Git snapshot으로 baseline classifier·assertion과 reviewed head를 대조했다. 보완 전 workflow, classifier와 두 계약 모듈의 blob은 `60e73c07…`와 `21fbaa9…`가 동일했다. |
| Pass | Historical Actions evidence | [CI Lite run 37085921046](https://github.com/mols3131d/hmda-data-reliability/actions/runs/37085921046)은 `60e73c07…` 대상 `pull_request` run이며 2026-10-03T01:23:42Z에 생성됐다. Markdown·Inbox·Python·selected tests는 success, Tach step은 skipped였다. 이는 로컬 보완의 CI 근거가 아니다. |
| Pass | Pre-remediation negative control | 테스트 대상 하나를 메모리에서 제거해도 기존 두 모듈은 114 passed였다. 기존 `tach=true` assertion도 누락을 검출하지 못했다. |
| Pass | Focused local pytest | `uv run --no-sync pytest tests/scripts/test_ci_classifier.py tests/scripts/test_ci_steps.py -q -p no:sugar -p no:cacheprovider --color=no --tb=short`: 미커밋 보완 상태에서 117 passed. |
| Pass | Required-target negative controls | 세 필수 target을 하나씩 메모리 내에서 제거했으며 새 `test_workflow_tach_step_runs_required_checks`는 세 경우 모두 assertion failure와 pytest exit 1로 검출했다. 정상 workflow는 수정하지 않았다. |
| Pass | Local static checks | 수정한 step test module의 Ruff check, Ruff format check, `ty check` 통과. |
| Not Verified | Original review execution | 원 리뷰에서는 pytest·Bash 검증과 독립 subagent orchestration을 재실행하지 않았다. 이번 보완 근거가 원 리뷰의 실행 이력을 바꾸지는 않는다. |
| Not Verified | Remediation on Actions | 로컬 보완은 미커밋·미푸시 상태다. 새 계약 테스트를 포함한 원격 CI는 실행하지 않았다. |

## Risks and Limits

Fake CLI 테스트는 workflow wiring, argv와 실패 전파를 검증하며 실제 Tach dependency semantics를 대신 증명하지 않는다. Source·dependency·Tach 변경의 runtime check는 유지한다. Prospective merge SHA는 이번 보정에서 확인하지 않았으며 Actions의 PR head SHA와 동일하다고 가정하지 않는다.

Git C-quoted 특수 파일명 누락과 OpenSpec intermediate dangling symlink 제한은 [앞선 리뷰](03-review-ci-script-extraction-commit.md)의 별도 follow-up으로 유지한다. 이번 보정이나 테스트 보완의 범위로 흡수하지 않는다.

```yaml
revision:
  base: 5532dca2fd93696d40ba870471fa2359c5662335
  head: 60e73c07a0386a43d165955e46bb74f3a6a9def3
```
