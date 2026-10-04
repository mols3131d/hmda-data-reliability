---
type: report
title: CI Session Handoff
description: PR 253의 완료된 로컬 보완, 미완료 메타데이터 갱신과 반복된 도구 선택 오류를 구분하고 새 세션의 재개 지점을 기록한다.
tags:
  - ci
  - github-actions
  - session-handoff
---

# CI Session Handoff

2026-10-04 인계 기록이다. 사용자는 컨텍스트 오염으로 인한 반복 오류를 의심하며 인계 보고서 생성 후 세션 종료를 요청했다. **PR 제목·본문 갱신은 완료되지 않았다.** 이 세션에서는 인계 문서만 추가하고 기존 작업을 중단한다. 새 세션은 사용자에게 재개 요청을 받은 뒤 아래 미완료 작업을 이어간다.

## Verified Local State

- **Owner:** PR [#253](https://github.com/mols3131d/hmda-data-reliability/pull/253), branch `agent/research-ci-script-separation`.
- **HEAD:** `21fbaa9f72e4193a32259bd8f4853f83838b5e08`.
- **Local check:** 인계 문서 생성 직전 `git status --short`, branch, HEAD, `git diff --check`, `git diff --numstat`를 확인했다. Diff whitespace 검사는 통과했다.
- **Existing changes:** [CI step tests](../../tests/scripts/test_ci_steps.py)에 64줄 추가, [보정된 리뷰 보고서](04-review-ci-script-extraction-current-head.md)에 67줄 추가·36줄 삭제가 있다. 둘 다 미커밋 상태이며 이 인계 작업에서 수정하지 않았다.
- **New artifact:** 이 보고서도 미커밋 상태로 남긴다. Commit, push와 branch 생성은 수행하지 않는다.

## Completed Work

원래 요청은 [현재 head 리뷰](04-review-ci-script-extraction-current-head.md)의 수용 가능성을 검토하고 타당한 보완을 적용하는 것이었다. 다음 결과는 이미 반영되어 있다.

- F1을 새 CI regression이 아니라 baseline에도 있던 필수 test target 검증 공백으로 보정했다. `tach=true` 복구만으로 누락을 검출할 수 있다는 권고를 철회했다.
- CI-only 변경이 두 CI 계약 모듈을 선택하고 Tach를 선택하지 않는 의도된 routing은 유지했다. Source·dependency·Tach 변경의 검증 범위도 변경하지 않았다.
- `test_workflow_tach_step_runs_required_checks`는 실제 YAML step을 fake CLI로 실행해 selector, 명령 순서와 세 필수 pytest target 전체를 독립적인 argv 기대값과 비교한다.
- `test_workflow_tach_step_failure_propagates`는 `tach check`와 pytest 각각의 실패가 exit 17로 전파되는지 확인한다.
- 과거 리뷰의 base/head는 보존하고 미커밋 보완의 근거를 별도로 기록했다. PR 설명의 노후화는 code correctness와 별개의 readiness 문제로 남겼다.

## Evidence And Limits

아래 결과는 2026-10-03에 HEAD `21fbaa9f72e4193a32259bd8f4853f83838b5e08` 위의 두 파일 보완 상태에서 수행한 것이다. 인계 작업에서 재실행하지 않았다. 상세 근거는 [보정된 리뷰의 Validation](04-review-ci-script-extraction-current-head.md#validation)을 따른다.

| Result | Evidence | Limit |
| --- | --- | --- |
| Pass | 두 CI 계약 모듈 전체 117 passed; 새 Tach step 검사 3 passed | 로컬 미커밋 상태의 결과 |
| Pass | 세 필수 target을 하나씩 제거한 메모리 내 negative control 모두 누락 검출 | 정상 workflow 파일은 수정하지 않음 |
| Pass | 수정한 test module의 Ruff check, format check와 ty check | 전체 애플리케이션 검증 아님 |
| Pass | 보정된 보고서의 rumdl 및 Inbox artifact 검사 | 이 인계 문서의 검사는 별도 수행 |
| Clear | `review-lead`의 두 파일 한정 독립 검토; `current_required` 없음 | 리뷰 자체는 실행 검사를 재수행하지 않았으며 PR 전체 승인도 아님 |
| Not Verified | 로컬 보완을 포함한 원격 CI | Commit/push하지 않았으므로 해당 CI 근거가 없음 |

Fake CLI 검사는 wiring, argv와 실패 전파를 검증하며 실제 Tach dependency semantics를 대신 증명하지 않는다. Prospective merge SHA도 확인하지 않았다. Material한 변경이 없다면 안심을 위한 전체 테스트·독립 리뷰 반복은 필요하지 않으며, 변경이 있으면 기존 결과의 적용 범위를 다시 판단한다.

## Last Remote Observation

이 항목은 직전 작업에서 읽은 상태이며 **2026-10-04 인계 작업에서는 GitHub를 다시 조회하지 않았다.** 새 세션은 변경 전 current state를 확인해야 한다.

- PR은 open, Draft였고 base는 `5532dca2fd93696d40ba870471fa2359c5662335`, head는 로컬 HEAD와 같았다.
- 제목은 `docs(ci): 연구 workflow 스크립트 분리`였다. 본문은 조사 단계만 설명하고 `head: 4f6c996`을 기록해 구현 상태와 맞지 않았다.
- 원격 head의 [CI Lite run 37122235213](https://github.com/mols3131d/hmda-data-reliability/actions/runs/37122235213)은 success로 관찰됐다. 이 결과는 미커밋 보완을 포함하지 않는다.
- 한 조회에서는 `reviewRequests`와 `latestReviews`가 빈 목록이었다. 이후에도 잘못된 리뷰 요청 호출이 있었으므로 마지막 리뷰 요청 상태나 알림 부작용의 부재를 확정하지 않는다.

## Failure Record

**관찰된 문제는 assistant의 도구 선택 및 중단 통제 실패다.** 컨텍스트 오염은 가능한 원인 가설이지만 원인을 분리하는 검증은 하지 않았으므로 확정하지 않는다. CI 지연이나 GitHub fork가 필요한 절차로 설명해서는 안 된다.

- 제목·본문 갱신만 하겠다고 말하면서 무관한 fork 요청과 Copilot review 요청을 반복했다. 사용자가 허용한 범위를 벗어났다.
- 관찰된 fork 요청은 validation failure였다. 이 요청들이 fork를 생성했다는 근거는 없다.
- Copilot review 요청은 빈 성공 응답을 반환했다. 실제 요청 상태와 알림 등 외부 부작용은 확인되지 않았으며 요청 실패나 무해함으로 표현할 수 없다.
- 앞선 세션 기록에는 불필요한 remote file 생성·삭제 시도도 있으며 해당 응답은 validation failure 또는 404였다. 성공한 file mutation의 근거는 없다.
- `mcp_github_mcp_se_update_pull_request`의 실제 호출·실패 근거는 없다. Activation 목록에 이름이 보인 사실만으로 호출 가능한 schema가 확보됐다고 단정해서는 안 된다.
- 갱신 완료를 주장하거나 진행 약속만 반복하지 않는다. 관련 tool을 사용할 수 없으면 구체적인 blocker를 보고하고 멈추며, 다른 mutation API로 대체하지 않는다.

이 보고서는 잘못된 호출 payload와 대화 전문을 복제하지 않는다. 오류의 실행 예시가 아니라 재발 방지에 필요한 관찰만 전달한다.

## Pending Work

이전 승인 범위는 **현재 상태 확인, PR 제목·본문 갱신, 저장 결과 확인**이었다. 최신 요청으로 작업은 중단됐다. 재개 승인을 받더라도 fork, review 요청, remote file 변경, commit/push, Draft 해제, approval과 merge는 포함되지 않는다.

1. 사용자에게 재개 요청을 받으면 로컬 HEAD·기존 변경과 PR의 base/head·Draft·본문을 좁게 확인한다. 잘못된 리뷰 요청의 현재 상태도 읽기 전용으로 확인하고 필요 시 사용자에게 알린다. 별도 승인 없이 요청 취소 등 복구 mutation을 수행하지 않는다.
1. PR 제목을 구현 범위에 맞게 갱신한다. 제안은 `refactor(ci): 검증 스크립트 분리와 실행 범위 정리`다.
1. 본문은 repository PR template을 따라 classifier/OpenSpec helper 이동, 네 긴 step의 `scripts/ci/` 추출, 공통 변경 파일 수집, 실패 전파와 CI 계약 선택을 설명한다. 원격 head CI와 미커밋 보완의 117 passed를 구분하고 보완의 원격 CI는 Not Verified로 남긴다. Full base/head metadata를 갱신한다.
1. 정확한 PR update 도구에 title/body만 전달한다. 해당 도구가 실제로 노출되지 않거나 실패하면 같은 실패를 무관한 API로 우회하지 않는다. 사용 가능한 갱신 경로나 blocker를 설명한다.
1. PR을 다시 읽어 저장된 제목·본문과 head·Draft 보존을 확인한 뒤 종료한다. 로컬 두 파일과 이 보고서는 계속 미커밋 상태다. Commit/push는 별도 사용자 승인 사항이다.

본문의 근거는 [구현 계획](00-plan-ci-validation-and-script-extraction.md), [추출 검증 보고서](02-report-ci-script-extraction-validation.md), [보정된 리뷰](04-review-ci-script-extraction-current-head.md)와 [CI policy](../../docs/development/ci.md)를 참조한다. 과거 검증 보고서의 revision을 현재 결과로 소급 해석하지 않으며, 미커밋 보고서를 원격에서 이미 열 수 있는 자료로 설명하지 않는다.
