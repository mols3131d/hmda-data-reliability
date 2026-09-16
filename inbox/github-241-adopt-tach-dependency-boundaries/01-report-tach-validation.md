---
type: report
title: "Tach Implementation and Validation Report"
description: "PR #241에서 이 세션이 수행한 구현, 동시 변경 통합, revision별 검증과 전달 결과를 정리합니다."
tags:
  - python
  - tooling
  - architecture
---

# Tach Implementation and Validation Report

## Result

PR #241 인계 작업의 구현, 검증, push와 PR 본문 갱신을 완료했다. 최종 구현 revision은 `2143b8ffdc9dddaf074be77799629a20d88e3f5f`이며 해당 revision의 [CI Lite](https://github.com/mols3131d/hmda-data-reliability/actions/runs/35090673498)가 통과했다.

이 기록은 2026-09-16에 확인한 결과다. [PR #241](https://github.com/mols3131d/hmda-data-reliability/pull/241)은 확인 당시 Open/Draft이며 승인·merge는 수행하지 않았다.

## Scope And Ownership

- 인계 기준: [기존 계획](00-plan-tooling-tach-dependency-boundaries.md)의 Local Agent Handoff.
- Owning branch: `chore/adopt-tach-dependency-boundaries`.
- 작업 worktree: `/home/mols3131d/orca/workspaces/hmda-data-reliability/chore-adopt-tach-dependency-boundaries`.
- 요청을 받은 MVP 검증 workspace에는 구현을 넣지 않고, 인계에서 지정한 PR 전용 worktree에서 작업했다.
- 이 문서는 작업·검증 기록이다. 운영 기준은 [Tach guide](../../docs/development/tooling/tach.md), executable rule은 `tach.toml`이 소유한다.

## Work Performed

| Area | Work |
| --- | --- |
| Dependency | Tach 0.35.1을 dev dependency로 추가하고 `uv`로 lockfile을 생성했다. 기존 package version은 유지했다. |
| Coverage | Package root와 top-level package를 검사 대상으로 구성하고 `root_module = "forbid"`, `exclude = []`, `respect_gitignore = false`로 암묵적 검사 누락을 제한했다. |
| Policy | Reliability와 Runtime AI의 네 금지 import 방향만 투영했다. Tach는 runtime import를, 기존 AST guard는 `TYPE_CHECKING`을 포함한 source import를 검사한다. |
| CI | Source/config/dependency 변경에서 Tach 검사를 선택하고, `tach.toml` 단독 변경도 Python/uv setup과 locked sync를 거치게 했다. Boundary step에 실제 CLI negative-path 검사와 AST guard를 연결했다. |
| Regression | 실제 workflow의 setup/check 조건을 읽는 classifier 회귀 검증과 임시 source copy에서 실행하는 Tach 테스트를 추가했다. |
| Integration fix | Archive된 실제 OpenSpec Change를 active로 가정하던 기존 classifier test 3개를 temporary active Change fixture로 바꿨다. |
| Documentation | `DEVELOPMENT.md`, testing/Tach guide를 구현에 맞추고 generator로 docs index를 갱신했다. |
| Delivery | 최신 `main`과 동시 원격 구현을 통합하고 push했다. PR 본문에 실제 검증과 최종 CI 링크를 반영했다. |

## Commit Evidence

| Commit | Ownership | Meaning |
| --- | --- | --- |
| `961bcc2` | This session | Tach 구현, CI/test/documentation과 초기 검증 기록 |
| `eb1d6cd` | This session | 최신 `main` 반영 |
| `36b2e10` | Concurrent remote work | 다른 세션이 같은 PR에 push한 Tach 구현; 이 세션의 단독 작업으로 계산하지 않음 |
| `2143b8f` | This session | 동시 원격 구현 보존, 충돌 해결과 검증 보완 통합 |

## Decisions

- `src` source root, package root module과 현재 10개 top-level package를 선언했다. `root_module = "forbid"`, 빈 exclude, Git ignore 미적용으로 source 누락을 제한한다.
- `cannot_depend_on`만 사용한다. Full import allowlist와 global no-cycle policy는 도입하지 않았다.
- `tach` CI selector는 Tach configuration 단독 변경에서도 Python/uv setup, locked sync와 boundary 검증을 실행한다. Local hook은 변경하지 않았다.
- `uv add --dev 'tach>=0.35.1'`로 lockfile을 생성했다. 기존 package version은 변경하지 않고 Tach와 필요한 dependency만 추가했다.
- Docs index generator가 기존 ai-agent README metadata의 `Subagent` 항목 누락도 함께 교정했다.

## Final Validation

`2143b8f` 기준 결과다. CI는 PR head와 base를 결합한 prospective merge를 검사했다.

| Surface | Check | Result |
| --- | --- | --- |
| Local | Classifier + 두 Tach test module + 기존 AST guard | 78 passed |
| Local | 통합 후 pre-push affected tests | 69 passed |
| Local | Tach, Ruff, `ty check`, docs index, Markdown, Inbox validation | Pass |
| CI | Tach + 두 Tach test module + AST guard | 11 passed |
| CI | Selected unit suite | 304 passed |
| CI | dbt/Airflow dependency runtime smoke | 5 passed |
| CI | Dependency lock/sync, wheel build, Python, TOML, Markdown, Inbox | Pass |

Local focused suite, push hook과 CI에는 겹치는 테스트가 있으므로 수를 합산하지 않는다. 이 revision에서 전체 suite를 다시 실행했다고 주장하지 않으며 전체 suite 근거는 아래 통합 전 결과와 구분한다.

## Earlier Validation

Local environment: CPython 3.13.13, uv 0.12.5, Tach 0.35.1. 아래 결과는 동시 원격 구현 통합 전 `eb1d6cd`까지의 작업에서 실행했다.

| Check | Result |
| --- | --- |
| `uv run --no-sync tach check` | Pass |
| `tests/scripts/test_ci_classifier.py` | 62 passed |
| `tests/scripts/test_tach.py`, `tests/review_ai/test_dependency_boundaries.py` | 9 passed |
| `uv run --no-sync pytest -q -p no:sugar --tb=short -n 4 -m 'unit and not memory and not stress'` | 299 passed |
| `tests/dbt/test_analytics_foundation.py`, `tests/orchestration/test_airflow_dag.py` | 5 passed |
| `uv lock --check`, wheel build, `ty check` | Pass |
| Changed Python Ruff check and format check | Pass |
| Changed TOML Tombi format and lint | Pass |
| Changed Markdown rumdl check and docs index check | Pass |
| Push hook affected suite | 625 passed, 1 skipped |

Negative-path regression은 source copy를 temporary project에 만들고 실제 Tach CLI를 실행한다. `reliability`에서 `review_ai/runtime_ai`로, `runtime_ai`에서 `review_ai/reliability`로의 runtime import는 각각 nonzero exit와 해당 import diagnostic을 확인한다. Type-only import, 허용된 advisory/root import는 통과하고 implicit root 참조는 실패한다.

## Integration Finding

PR #242의 OpenSpec archive 이후 기존 classifier test 3개가 실제 `orchestration-quality-gate`를 active로 가정해 실패함을 재현했다. Active pairing 검증에 temporary directory fixture를 사용해 production classifier와 기대 계약은 유지하고 archive lifecycle 의존을 제거했다.

Push hook 실행 중 같은 작업의 remote commit `36b2e10`이 추가되어 첫 push가 거부됐다. Force-push 없이 remote를 merge했다. Remote의 `tach` selector, explicit module 목록과 `test_tach_config.py`를 보존하고 이번 작업의 workflow gating regression, 네 금지 방향/coverage 검사, 문서와 fixture 수정을 통합했다.

초기 local selector 이름 `architecture`는 통합 과정에서 remote의 `tach`로 통일했다. 최종 설정은 full allowlist를 두지 않고 global cycle prohibition도 활성화하지 않는다.

Remote 단독 revision `36b2e10`의 CI는 `pyproject.toml` formatting에서 실패했다. 통합 revision은 repository Tombi formatting을 적용한 상태로 같은 단계를 통과했다.

## Boundary

Application source, architecture contract와 approval/recovery authority는 변경하지 않았다. Full dependency allowlist, global no-cycle policy, Tach pytest selection과 새 local hook도 도입하지 않았다.

구현·검증 범위의 미해결 blocker는 없다. 다음 단계는 Draft PR의 인간 검토다. Ready 전환, 승인과 merge는 별도 결정으로 남겼다.
