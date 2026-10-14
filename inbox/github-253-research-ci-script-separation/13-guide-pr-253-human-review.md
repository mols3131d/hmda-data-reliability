---
type: guide
title: "PR 253 Human Review Guide"
description: "PR #253의 인간 리뷰에서 확인할 순서, 검증 보존 조건, Skills lock 호환성 경계와 승인 전 남은 판단을 안내한다."
tags:
  - ci
  - pull-request
  - human-review
---

# PR 253 Human Review Guide

[PR #253](https://github.com/mols3131d/hmda-data-reliability/pull/253)의 **CI 분리와 중복 제거가 필요한 검증을 보존하는지, Skills lock 호환성의 제한을 받아들일 수 있는지**를 사람이 판단하기 위한 가이드다. 확인된 문제는 수정을 요청하고, 문제가 없으면 검토한 범위와 남은 한계를 기록한다. 이 문서는 리뷰 결과나 승인 기록이 아니며, 공통 기준은 [Pull Request Reviews](../../docs/development/vcs-git/pull-request-review.md)를 따른다.

## Start Here

1. PR 본문의 `Summary`, `Changes`, `Validation`, `Risks`를 읽고 변경 목적과 미검증 범위를 확인한다.
1. 아래 근거와 현재 base/head·CI를 비교한다. 다르면 영향받은 변경과 검증 근거부터 갱신하고, 과거 결과를 현재 결과로 취급하지 않는다.
1. `Review Focus` 순서로 diff와 관련 테스트를 대조한다. 테스트 존재와 통과 기록을 구분하고, fake CLI 검사가 실제 dependency·runtime 동작까지 증명한다고 해석하지 않는다.
1. `Record The Decision`에 따라 문제, 검토 범위와 남은 위험을 기록한다. 인간 review 진입 준비 상태와 correctness 승인·병합 판단은 별개다.

### Evidence Basis

2026-10-05 PR 본문 갱신 후 확인한 상태다. 최신 상태의 정본은 GitHub이며 아래 값은 리뷰를 시작할 때 대조할 기준이다.

| Item | Evidence |
| --- | --- |
| Base | `5532dca2fd93696d40ba870471fa2359c5662335` |
| Head | `851788ccba3defc4f873c00d304666c3a1164598` |
| Prospective merge | `c60e09214541a446ede897dae44f2a528b8bf31e`; 부모가 위 base/head와 일치 |
| CI | [CI Lite run 37277685706](https://github.com/mols3131d/hmda-data-reliability/actions/runs/37277685706): success; selected tests `416 passed`, CI non-unit 보완 `66 passed, 95 deselected` |
| Review state | Open·Draft; 조회 당시 submitted review와 review thread 없음 |

현재 head는 [이전 리뷰](12-review-pr-253-merge-readiness.md)의 reviewed head `7ceb39a70fec8e3d15716c69fa3419a19aec5ead`에 리뷰 문서만 추가한 commit이다. 이전 리뷰의 오래된 PR 본문 문제는 본문 갱신으로 해소했지만, 그 검토를 현재 전체 PR의 fresh independent dual review나 인간 승인으로 확대하지 않는다.

이 가이드를 commit·push하면 head가 다시 바뀐다. 문서만 추가했더라도 새 head·CI와 PR 본문의 revision을 재확인하며, 추가 코드 변경이 있으면 영향받은 리뷰 범위도 다시 검토한다.

필요하면 다음 읽기 전용 명령으로 GitHub 상태와 diff를 확인한다. 로컬 HEAD의 성공만으로 prospective merge 검증을 대체하지 않는다.

```bash
gh api repos/mols3131d/hmda-data-reliability/pulls/253 --jq '{base: .base.sha, head: .head.sha, draft: .draft, state: .state}'
gh pr checks 253 --repo mols3131d/hmda-data-reliability
gh pr diff 253 --repo mols3131d/hmda-data-reliability
```

## Review Focus

### 1. CI Selection And Failure Propagation

먼저 [Admission](../../docs/development/ci/admission.md)과 [Change Impact](../../docs/development/ci/change-impact.md)를 읽는다. [Workflow](../../.github/workflows/ci-lite.yml)에서 조건과 환경값이 [classifier](../../scripts/ci/classify_changes.sh), [변경 파일 수집](../../scripts/ci/changed_files.sh), [OpenSpec mapping](../../scripts/ci/classify_openspec.sh)으로 어떻게 전달되는지 diff를 따라 확인한다.

- [ ] CI-only 변경은 CI 계약 테스트를 선택하되 source·dependency·Tach 변경의 필수 검증은 유지하는가?
- [ ] 잘못된 Git 비교와 필수 도구 실패가 nonzero로 전파되는가? 오류가 빈 변경 목록이나 성공으로 바뀌지 않는가?
- [ ] 영향이 불명확한 Spec 변경은 검증 범위를 넓히거나 실패시키는가? Helper 추출 이후 같은 선택 계약을 유지하는가?

근거는 [classifier 테스트](../../tests/scripts/ci/test_ci_classifier.py), [OpenSpec 테스트](../../tests/scripts/ci/test_ci_classifier_openspec.py), [Python 선택 테스트](../../tests/scripts/ci/test_ci_classifier_python.py), [workflow 테스트](../../tests/scripts/ci/test_ci_workflow.py)에서 확인한다. 선택 결과뿐 아니라 실패 경로를 보호하는 assertion도 읽는다.

### 2. Duplicate Removal Without Coverage Loss

[pytest 실행 스크립트](../../scripts/ci/pytest.sh), workflow 조건과 [pytest 계약 테스트](../../tests/scripts/ci/test_ci_pytest.py)를 함께 읽는다. 이 가이드의 항목 번호와 별개로, 구현 보고서의 `F1`은 두 중복 실행 제거를 뜻한다.

- [ ] AST guard 제외는 같은 실행에서 앞선 boundary 단계가 성공한 경우에만 적용되는가? Boundary 자체의 `tach check`와 세 필수 target은 남아 있는가?
- [ ] 독립 local 실행·boundary skip·full-unit 뒤 CI non-unit 보완은 필요한 검증을 생략하지 않는가?
- [ ] 별도 runtime smoke 생략은 두 smoke target을 실제 포함하는 full-tests가 성공했을 때만 적용되는가? Unit-only 실행 뒤 smoke는 유지되는가?
- [ ] Workflow와 테스트가 함께 target을 누락해도 통과하지 않도록 필수 target의 기대값이 독립적으로 고정돼 있는가?

[F1 Execution Record](11-ci-cost-and-complexity-improvement/plan.md#execution-record)의 collection 비교와 target 제거 negative control을 참고한다. `819 → 817`은 AST guard 2개만 제외하고 smoke 5개를 보존한 collection 근거이며, 전체 817개 테스트 실행이나 시간 절감의 증명은 아니다.

### 3. Skills Lock Compatibility And Trust Boundary

[Route sources](../../scripts/agent_routes/sources.py)의 hash 검증을 [회귀 테스트](../../tests/scripts/test_generate_agent_routes.py)와 대조한다. Vendor 근거와 로컬 검증은 [Merge Preparation](08-agent-routes-skills-lock-compatibility/02-report.md#2026-10-05-merge-preparation)이 소유한다.

- [ ] 전체 폴더 hash가 기본이며, ref 없는 허용 source의 root Skill에서만 `SKILL.md` 단일 파일 hash도 인정하는가? Optional `skillPath`가 제한을 우회하지 않는가?
- [ ] 다른 source·명시적 ref·nested Skill의 전체 폴더 검증과 변경 내용 거부가 유지되는가?
- [ ] Skill 이름의 유일성과 예약문자 경로 처리가 보존되고, 검증 후 immutable source URL을 생성하는가? Hash를 revision으로 사용하거나 branch·경로를 추측하지 않는가?
- [ ] HTTP 전송 중단과 조회 오류는 실패로 남는가? `--check` 실패가 기존 route를 수정하지 않는가?

허용 범위는 `vercel`, `vercel-labs`, `heygen-com`, `remotion-dev` owner 또는 `zapier/connectors` source다. Lock에 blob·clone 설치 방식이 없어 ref 없는 허용 root에서 두 vendor hash 형식을 구분할 수 없다는 한계를 검토한다. 실제 project lock이 tracked되지 않으므로 최신 CI의 route validation을 실제 lock의 end-to-end 증명으로 읽지 않는다.

### 4. CI Documentation And Blocking Boundaries

[CI 계약 번들](../../docs/development/ci/README.md)과 [Testing Guide](../../docs/development/testing.md#pull-request-ci)를 최종 동작에 대조한다. 세부 동작은 [Markdown 계약](../../docs/development/ci/markdown-validation.md), [Inbox 제외 정책](../../docs/development/ci/markdown-validation.md#inbox-exclusion), [Markdown 스크립트](../../scripts/ci/markdown.sh), [step 테스트](../../tests/scripts/ci/test_ci_steps.py)를 확인한다.

Inbox 제외는 이 가이드의 기준 revision 이후 문서 정책 변경이다. 아래 기준 revision의 검증 기록을 새 제외 정책이 CI 구현에 반영됐다는 근거로 사용하지 않는다.

- [ ] Formatting 제안이 disposable workspace에 한정되고, PR branch에 자동 commit·write-back을 하지 않는가?
- [ ] 비차단 Inbox Markdown lint와 차단하는 Docs lint·Inbox metadata 검증을 구분하는가?
- [ ] 문서의 local 명령, module CLI와 selector 설명이 새 구현을 가리키는가?

현재 CI의 과거 Inbox 링크 MD057 진단 8건은 비차단이다. 새 검증 누락과 혼동하지 않으며, 과거 경로 cleanup은 별도 후속 작업으로 분리한다.

### 5. Cost Claims And Accepted Limits

[F2 Measurement](11-ci-cost-and-complexity-improvement/research.md#f2-measurement)의 결론만으로 환경 분리를 승인하지 않는다. 로컬 WSL2 full sync 중앙값은 cold `25.64s`, warm `0.23s`이며, cold는 빈 uv cache, warm도 새 venv 기준이다. 기록된 Actions 표본의 cache 복원 약 `10s`와 sync `3s`는 해당 run의 관측이지 최신 run의 시간이나 환경 축소 절감량이 아니다.

- [ ] 측정된 전체 환경 비용과 미측정인 작은 환경의 이득을 구분하는가? 기존 전체 환경 유지 권고에 동의하는가?
- [ ] F1 반복 시간·실제 과금 절감, 작은 환경의 fixture/plugin·정적 검사 동등성을 검증한 것으로 표현하지 않는가?

환경 분리·새 lock/cache 체계·F3 build 조건 조정은 이번 변경에서 제외됐다. 추가 요구가 필요하다고 판단하면 이유와 새 scope를 명시하고, 단순 개선 선호를 이번 PR의 correctness blocker로 만들지 않는다.

## Record The Decision

문제는 [review template](../../.github/templates/pull-request-review.md)을 따라 root cause별로 위치·근거·영향·필요한 변경을 기록한다. 특정 diff line에 귀속되는 문제는 inline comment로, 검토 범위와 공통 결론은 review body에 둔다. 문제가 없다는 결론도 미검토 범위를 숨기지 않는다.

기록할 최소 정보는 다음과 같다. 아래는 실제 리뷰 결과가 아닌 작성 틀이다.

```text
State basis: 검토한 exact base/head 또는 prospective merge revision
Scope: 검토한 영역과 미검토 영역
Findings: 위치·근거·영향·필요한 변경, 또는 확인된 문제 없음
Validation: 직접 수행한 검사와 제공받은 CI/보고서 근거를 구분
Remaining risks: 수용한 제한, 추가 확인이 필요한 사항, 별도 follow-up
```

수정이 필요하면 `Request Changes`, 충분히 검토했고 수용 가능하면 플랫폼과 계정이 허용하는 `Approve`, 판단 근거가 부족하거나 일부 범위만 검토했다면 `Comment`와 남은 조건을 기록한다. Author와 같은 GitHub identity의 self-review는 approval이나 independent review로 표현하지 않는다.

### Before Merge

- [ ] 현재 base/head, PR description, prospective merge CI와 적용되는 blocking feedback이 일치하는지 다시 확인했다.
- [ ] 수행하지 않은 전체 suite·실제 lock 검증·fresh full-PR independent dual review를 완료했다고 주장하지 않고, 남은 한계가 판단에 어떤 영향을 주는지 기록했다.
- [ ] Required checks와 approval 요구사항을 확인했다. Protection·rules 조회의 HTTP 403을 승인 불필요의 근거로 사용하지 않았다.
- [ ] 필요한 review와 중요한 conflict가 해소됐다. Ready 전환·승인·merge는 각각 별도 lifecycle action으로 판단한다.

공통 readiness·lifecycle 기준은 [Pull Requests](../../docs/development/vcs-git/pull-request.md#review-readiness)를 따른다. 이 가이드 생성이나 체크리스트 자체가 Draft 해제·승인·병합을 수행하거나 권한을 부여하지는 않는다.
