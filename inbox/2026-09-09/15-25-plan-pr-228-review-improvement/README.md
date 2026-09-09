---
type: plan
title: PR #228 Review Improvement Plan
description: canonical OpenSpec Spec와 직접 연결된 active Change의 admission validation을 보강하고 그 근거를 loop artifact로 남기는 실행 계획이다.
tags:
  - ci
  - openspec
  - pr-228
  - review-improvement
---

# PR #228 Review Improvement Plan

## Target

- Pull Request: [#228](https://github.com/mols3131d/hmda-data-reliability/pull/228)
- Reviewed source: `f7b8ee808e416519c596f0767e1e30d5283c4bcd`
- Improvement branch: `agents/pr-228-review-improvement-loop`

## Goal

canonical `openspec/specs/<capability>/**` 변경이 해당 Spec의 delta를 직접 소유하는 active Change까지 같은 blocking OpenSpec admission 범위에 포함하도록 classifier와 regression contract를 보강한다.

## Scope

- `.github/workflows/classify_changes.sh`의 direct active Change discovery
- `tests/test_ci_classifier.py`의 pairing·mixed-input regression
- current PR review에 대응하는 Research, Plan, Work, Review Inbox artifacts

### Out of Scope

- OpenSpec CLI 내부 구현 변경
- unrelated application/domain behavior 변경
- archived Change ownership 또는 전체 Inbox lifecycle 변경
- PR 승인, Ready 전환, merge 또는 review thread 처리

## Acceptance

- known canonical Spec 변경은 해당 Spec target과 직접 연결된 active Change target을 함께 출력한다.
- related active Change가 없거나 archive만 존재하는 Spec은 기존 affected Spec validation을 유지한다.
- 이름이나 directory 상태를 안전하게 판정할 수 없는 OpenSpec path는 `openspec_bulk=true`로 fail-safe하게 넓어진다.
- mixed canonical Spec/active Change 입력은 두 target을 모두 보존하며 중복은 제거한다.
- 기존 F1/F2/F3 fallback, dependency runtime smoke와 46개 classifier regression이 깨지지 않는다.

## Loop Order

1. Research — current PR head와 Inbox review를 대조하고 residual gap을 고정한다.
1. Plan — 최소 변경, acceptance와 non-goal을 고정한다.
1. Work — red regression을 먼저 추가한 뒤 classifier를 보강한다.
1. Review — focused test, runtime smoke, OpenSpec/lock/build와 diff를 재검증한다.

## Validation Commands

```bash
uv run --no-sync pytest tests/test_ci_classifier.py -q -rs
uv run --no-sync pytest tests/dbt/test_analytics_foundation.py tests/orchestration/test_airflow_dag.py -q -rs
npm exec --yes --package @fission-ai/openspec@1.12.0 -- openspec validate --all --strict
uv lock --check
uv build --wheel --out-dir /tmp/pr228-dist
```
