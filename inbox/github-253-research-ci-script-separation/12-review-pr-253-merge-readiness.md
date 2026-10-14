---
type: review
title: "PR 253 Merge Readiness Review"
description: "PR #253의 현재 구현, CI admission, route 호환성과 live GitHub evidence를 대조해 병합 준비 수준을 검토한다."
tags:
  - "domain:ci"
  - "github"
  - "pull-request"
---

# PR 253 Merge Readiness Review

> [!IMPORTANT]
> **Revise** — Reviewed head `7ceb39a70fec8e3d15716c69fa3419a19aec5ead`의 구현에서는 새로운 correctness blocker를 발견하지 못했고 current prospective merge CI도 성공했다. 다만 PR description이 이전 head·CI와 F2 측정 전 상태를 가리켜 repository Review Readiness의 Description·Validation 조건을 충족하지 못한다. 코드 수정 없이 PR body evidence를 current state로 갱신하고 human review를 거친 뒤 merge를 판단한다.

- **Target** — [PR #253](https://github.com/mols3131d/hmda-data-reliability/pull/253) `refactor(ci): 검증 계약 정리와 route 호환성 보완`
- **Revision** — base `5532dca2fd93696d40ba870471fa2359c5662335`, head `7ceb39a70fec8e3d15716c69fa3419a19aec5ead`, prospective merge `1f4b1be9c28d2c52c35a18853491cb7a6bc3f767`
- **Scope** — PR 전체의 CI script 분리와 change-impact routing, F1 중복 실행 제거, CI 계약 테스트·문서, Agent Route generator와 Skills CLI lock 호환성, 현재 PR description·CI·review state를 검토했다.

## Findings

| ID | Severity | Finding | Action |
| --- | --- | --- | --- |
| F1 | 🟠 **Major** | PR description과 Validation evidence가 현재 head보다 이전 상태라 review readiness가 current하지 않다. | PR body의 revision·CI·route compatibility·F2 상태를 현재 evidence로 갱신한 뒤 readiness를 다시 판정한다. |

## Details

### F1 · PR Description and Validation Are Stale

🟠 **Major**

#### Locations

- [PR #253](https://github.com/mols3131d/hmda-data-reliability/pull/253)
  - `Changes`
  - `Validation`
  - `Boundaries`
  - `revision`
- [`docs/development/vcs-git/pull-request.md`](../../docs/development/vcs-git/pull-request.md)
  - `Review Readiness`
- [`08-agent-routes-skills-lock-compatibility/02-report.md`](08-agent-routes-skills-lock-compatibility/02-report.md)
  - `2026-10-05 Merge Preparation`
- [`11-ci-cost-and-complexity-improvement/research.md`](11-ci-cost-and-complexity-improvement/research.md)
  - `F2 Measurement`

#### Evidence

Live PR state에서 base는 `5532dca2fd93696d40ba870471fa2359c5662335`, head는 `7ceb39a70fec8e3d15716c69fa3419a19aec5ead`다. 그러나 PR body의 revision metadata는 head `ec81d5d3abb27b036a50ed79e73b18565199f394`를 가리킨다.

PR body의 `Current prospective merge CI`도 이전 [CI Lite run 37216063423](https://github.com/mols3131d/hmda-data-reliability/actions/runs/37216063423)과 `405 passed`를 current evidence로 기록한다. 현재 head에 연결된 [CI Lite run 37262509072](https://github.com/mols3131d/hmda-data-reliability/actions/runs/37262509072)은 success이고 prospective merge `1f4b1be9c28d2c52c35a18853491cb7a6bc3f767`을 checkout했다. Selected tests는 `416 passed in 11.47s`, CI non-unit 보완은 `66 passed, 95 deselected in 2.61s`다. Dependency lock·sync, package build, Python validation과 chatbot route validation은 성공했고, dependency boundary와 별도 runtime smoke는 현재 분류에서 skipped이므로 통과로 세지 않는다.

이전 body 이후 head에는 `01bf613fa9898756da7549a0e58ea52b0b177b22`의 root blob lock hash 호환성 보완과 `7ceb39a70fec8e3d15716c69fa3419a19aec5ead`의 F2 환경 비용 측정 기록이 포함됐다. 현재 body는 Skills CLI version 1 lock을 전체 폴더 hash 검증으로만 설명하고 F2를 다음 follow-up으로 적어 이 두 변경의 current state를 충분히 반영하지 않는다.

Repository의 Review Readiness 계약은 description의 scope·claim과 validation evidence가 현재 base/head에 적용 가능해야 하며 material state가 바뀌면 이전 assessment를 stale로 본다. 따라서 구현 품질과 별개로 현재 PR lifecycle evidence는 `ready`로 확정할 수 없다.

#### Impact

PR body만 읽는 human reviewer는 실제 현재 head에서 무엇이 바뀌었고 어느 prospective merge revision이 검증됐는지 잘못 판단할 수 있다. 특히 route compatibility fix와 F2 측정 상태가 이전 설명에 가려지고, old test count와 old revision이 current evidence처럼 보인다. 이는 코드 correctness defect는 아니지만 merge 전 evidence boundary를 흐리므로 acceptance 전에 정리해야 한다.

#### Action

코드나 테스트를 추가 수정하지 않고 PR body만 current evidence에 맞춘다.

- revision head를 `7ceb39a70fec8e3d15716c69fa3419a19aec5ead` 기준으로 갱신한다.
- current CI를 run `37262509072`와 `416 passed`, `66 passed, 95 deselected` 기준으로 갱신한다.
- root blob lock compatibility가 허용 source의 root `SKILL.md` hash를 제한적으로 지원하며 다른 source·explicit ref·nested Skill의 전체 폴더 검증은 유지한다는 최종 동작을 반영한다.
- F2 cold/warm 측정이 완료됐고 현재 권고가 기존 전체 환경 유지라는 상태를 반영한다.
- skipped step을 pass로 표현하지 않고 branch protection·required approval처럼 확인하지 못한 항목은 unknown으로 남긴다.

갱신 후 current head와 CI가 유지되는지 다시 확인하고 human review를 진행한다. Ready 전환·approval·merge는 별도 lifecycle action이며 이 review artifact가 권한을 부여하지 않는다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | Current prospective merge CI | [Run 37262509072](https://github.com/mols3131d/hmda-data-reliability/actions/runs/37262509072)은 success다. Checkout은 prospective merge `1f4b1be9c28d2c52c35a18853491cb7a6bc3f767`, selected tests는 `416 passed`, CI complement는 `66 passed, 95 deselected`다. |
| ✅ Pass | CI admission과 중복 제거 경계 | [`scripts/ci/`](../../scripts/ci/)와 [`tests/scripts/ci/`](../../tests/scripts/ci/)를 대조했다. Invalid comparison과 tool failure는 nonzero로 전파하고, boundary/runtime smoke 중복 제거는 선행 검사가 성공한 경우에만 적용되도록 계약 테스트가 고정한다. 새로운 fail-open path는 확인하지 못했다. |
| ✅ Pass | Skills CLI root blob compatibility | `01bf613f`의 보완은 허용 vendor/root `SKILL.md`에만 blob hash fallback을 적용하고 explicit ref·nested Skill의 기존 folder hash contract를 유지한다. 관련 회귀 테스트와 current route validation은 성공했다. |
| ✅ Pass | Mutable PR review state | 조회 시 PR은 Open·Draft·mergeable이며 submitted review, review thread와 conversation comment가 없다. 기존 blocking feedback은 확인되지 않았다. |
| ❌ Fail | Review Readiness freshness | Current head는 `7ceb39a...`이나 PR body metadata와 current CI claim은 `ec81d5d...` 및 이전 run을 가리킨다. F1에 따라 body refresh가 필요하다. |
| ⚪ Not Verified | Branch protection과 required approval | 연결 권한으로 protection/ruleset의 approval requirement를 확인할 수 없었다. 확인 불가를 approval 불필요로 해석하지 않는다. |
| ⚪ Not Verified | Full independent dual-review execution | 이 review는 단일 ChatGPT session의 심층 검토다. Repository에 기록된 scoped independent review evidence는 참고했지만 현재 전체 PR에 대한 별도 두 reviewer의 fresh independent execution을 수행했다고 주장하지 않는다. |

## Risks and Limits

- 현재 repository에는 실제 `skills-lock.json`이 tracked되지 않아 current CI의 route validation은 실제 project lock artifact를 end-to-end로 읽은 증거가 아니다. Version 1 compatibility는 fixture·contract tests와 upstream behavior 대조 근거에 의존한다.
- CI 로그에는 과거 Inbox artifact의 이동·삭제된 경로를 가리키는 MD057 진단 8건이 남지만 `inbox/**` Markdown lint는 현재 admission contract상 non-blocking이다. 별도 cleanup 가치는 있으나 #253 merge blocker로 확대하지 않는다.
- 이 artifact는 reviewed head `7ceb39a...`의 snapshot을 기록한다. 이 파일 자체를 branch에 추가하는 delivery commit은 reviewed revision에 포함되지 않으므로, 실제 merge 판단은 report delivery 이후의 새 head와 새 CI state를 다시 확인해야 한다.
