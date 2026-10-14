---
type: report
title: "Zizmor Implementation Evidence"
description: "PR #254의 zizmor 구현 범위, 실제 baseline, 회귀 검증과 남은 delivery 검증을 기록한다."
tags:
  - ci
  - security
  - zizmor
---

# Zizmor Implementation Evidence

## State Basis

- Date: `2026-10-08`
- Branch: `agent/chore/adopt-zizmor`
- Base: `4f03e0c317c1698959688afb818c83349060ccfa`
- Starting Head: `c6a681d86a56b009071eb19f0757805a54a94904`
- Implementation State: starting head 위의 미커밋 working tree. 기존 head의 CI 성공은 이 구현의 원격 검증이 아니다.
- Scope: [기존 도입 계획](01-plan-ci-zizmor-adoption.md)의 offline conditional gate. 별도 project dependency, config, exception, permission 또는 token은 추가하지 않는다.

## Current Authority

PR #253은 base와 starting head에 이미 반영됐다. 기존 계획의 Bash classifier와 이전 test 경로는 사용하지 않는다. 변경 경로 선택은 [Python classifier](../../scripts/ci/classify_changes.py), workflow 실행 조건과 command는 [CI Lite](../../.github/workflows/ci-lite.yml), 회귀 계약은 [classifier tests](../../tests/scripts/ci/test_ci_classifier.py)와 [workflow tests](../../tests/scripts/ci/test_ci_workflow.py)가 소유한다.

## Baseline and Decisions

`uvx zizmor@1.30.1 --offline --strict-collection --collect=workflows,actions --persona=regular --no-config --format=github .`를 수정 전 실행했다. GitHub token 환경 변수를 제거했으며 actionable finding은 `unpinned-uses` 두 건이었다. `actions/checkout@v6.0.2`와 `actions/setup-python@v6.2.0`이 대상이다.

두 tag의 현재 원격 SHA를 `git ls-remote`로 확인했다.

| Action | Tag | Verified SHA |
| --- | --- | --- |
| `actions/checkout` | `v6.0.2` | `de0fac2e4500dabe0009e67214ff5f5447ce83dd` |
| `actions/setup-python` | `v6.2.0` | `a309ff8b426b58ec0e2a45f0f869d46889d02405` |

Node 도구 설치는 현재 Python 실행부에 있으므로 이 scan에서 `adhoc-packages` finding이 발생하지 않았다. 따라서 예정된 조건부 inline exception은 추가하지 않았다. 이는 npm 설치 자체의 supply-chain 안전성을 증명하지 않는다.

## Implementation

- Workflow와 root/nested action의 `.yml`/`.yaml` 변경에 `zizmor=true`를 출력한다. 삭제된 경로도 존재 여부와 무관하게 선택하며 기존 Inbox 제외 경계를 유지한다.
- `Set up uv`는 `zizmor`만 선택된 경우에도 실행하고, project dependency sync 조건은 바꾸지 않는다.
- 기존 job에 exact-version offline audit step을 추가했다. Finding, collection parse 오류와 실행 실패를 무시하지 않는다.
- 두 mutable action reference를 확인된 full SHA에 고정하고 기존 `persist-credentials: false`를 유지했다.
- [Development inventory](../../DEVELOPMENT.md)에 실제 도입 도구를 추가했다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| Pass | 수정 전 CI baseline | classifier/workflow 기존 87개 test 통과 |
| Pass | Red regression | 추가한 16개 case가 누락된 selector, audit step과 SHA 계약 때문에 실패 |
| Pass | Green regression | 같은 16개 case 통과, 기존 87개는 이 focused 실행에서 deselected |
| Pass | 실제 offline scan | 수정 후 v1.30.1 exact command 종료 0, finding 없음 |
| Pass | 전체 CI 계약 suite | `uv run --no-sync pytest -q -p no:sugar --tb=short tests/scripts/ci`: 223개 통과 |
| Pass | 변경 영역 정적 검사 | Ruff check와 format check, `ty check scripts/ci tests/scripts/ci` 통과. 초기 format/type 진단을 수정한 뒤 workflow 49개 test 재실행 통과 |
| Pass | 실제 finding negative control | 임시 workflow 복사본의 checkout을 mutable tag로 바꾸자 `unpinned-uses`, exit 14 |
| Pass | 실제 malformed-input negative control | 같은 임시 복사본의 YAML 구문을 깨뜨리자 strict collection 실패, exit 1 |
| Pass | Independent review | 전체 diff를 두 specialist와 review-lead가 확인해 `clear`. [리뷰 기록](03-review-ci-zizmor-implementation.md)의 fingerprint와 현재 코드 일치 |
| Not Verified | 새 구현의 원격 CI | commit/push하지 않아 기존 PR CI를 새 구현 근거로 사용하지 않음 |

## Limits and Next Action

Offline scan은 collected workflow/action 정의에 대한 v1.30.1 regular audit 근거다. Online advisory, third-party action 내부 보안, 일반 application 보안 또는 모든 workflow runtime 경로를 증명하지 않는다.

로컬 검증과 독립 리뷰 뒤에도 remote delivery 검증은 별도다. 명시적 요청 없이 commit/push, Ready 전환, approval 또는 merge하지 않는다.
