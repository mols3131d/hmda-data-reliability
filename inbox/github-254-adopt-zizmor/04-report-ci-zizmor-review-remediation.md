---
type: report
title: "Zizmor Review Remediation"
description: "PR #254의 tracked-and-ignored 감사 누락과 Inbox 수집 불일치를 수정한 근거, 실제 회귀 검증과 독립 재리뷰 결과를 기록한다."
tags:
  - ci
  - security
  - zizmor
---

# Zizmor Review Remediation

## State Basis

- Date: `2026-10-08`
- Target: `agent/chore/adopt-zizmor`, HEAD `92cd5a3178ed9a3f396e3598cc994af4f1fea5be` 위 미커밋 후속 변경.
- Scope: [F1](https://github.com/mols3131d/hmda-data-reliability/pull/254#discussion_r4216270520)의 tracked-but-ignored 감사 누락과 [F2](https://github.com/mols3131d/hmda-data-reliability/pull/254#discussion_r4216270531)의 mixed Inbox 수집 불일치.
- Authority: 사용자의 리뷰 개선 요청에 따라 입력 선택만 교정한다. [원 계획](01-plan-ci-zizmor-adoption.md)의 directory `.` 입력은 이 후속 수정에서 명시적 tracked 정의 목록으로 대체한다. Exact version, 여섯 CLI flags, offline/blocking, 권한과 의존성 경계는 유지한다.

## Findings and Resolution

| Finding | Evidence | Resolution |
| --- | --- | --- |
| F1: Git ignore에 의해 tracked 정의 누락 | 실제 v1.30.1 directory scan은 ignored unsafe action을 놓쳐 exit 0; 수정 실행부는 같은 파일을 감사해 exit 14 | NUL 구분 `git ls-files -z`로 tracked 정의를 열거하고 명시적 파일 argv로 전달 |
| F2: mixed Inbox 정의 수집 | malformed tracked Inbox를 ignore에서 해제하면 directory scan exit 1; 수정 실행부는 정상 정의만 감사해 exit 0 | 도구 실행 전에 `inbox/` prefix를 제외 |

[실행부](../../scripts/ci/run_checks.py)의 `zizmor` check가 입력을 수집하고 기존 subprocess 실패 전파를 재사용한다. [Workflow](../../.github/workflows/ci-lite.yml)는 이 check를 호출한다. 공백 경로를 NUL/structured argv로 보존하고 `./` 접두사를 사용한다. 빈 입력과 Git 실패를 성공으로 숨기지 않는다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| Pass | Input and failure regression | tracked ignored workflow/root/nested action, 공백 경로, mixed Inbox, untracked 제외, 도구 exit 17, 빈 목록 exit 1, Git 오류 exit 128 |
| Pass | Workflow regression | YAML의 실제 command를 실행해 helper 연결, exact version·flags·입력 argv와 실패 전파 확인 |
| Pass | Actual collection regression | `test_actual_zizmor_collects_ignored_inputs_and_excludes_mixed_inbox`가 실제 v1.30.1로 unsafe ignored action exit 14·finding/path를 확인하고 SHA 수정 후 malformed Inbox를 남긴 상태에서 exit 0 확인. Skip 없이 통과 |
| Pass | Actual root audit | 수정 entrypoint로 현재 repository 감사 exit 0 |
| Pass | CI contract suite | 최종 `tests/scripts/ci` 228개 통과 |
| Pass | Static checks | 변경 Python Ruff lint·format과 `ty check scripts/ci tests/scripts/ci` 통과 |
| Pass | Independent re-review | review-lead의 quality/adversarial 검토 결과 `clear`. 최초 actual-regression acceptance gap을 보강한 뒤 전체 diff 1,364줄과 네 파일을 다시 검토 |
| Pass | Reviewed state identity | 구현 담당자가 최종 review 전후 아래 네 fingerprint 일치 확인 |
| Not Verified | Reviewer-side execution | reviewer는 source와 진단을 독립 확인했으나 pytest·실제 도구·hash를 직접 재실행하지 않음 |
| Not Verified | New revision remote CI | 후속 수정은 아직 commit/push하지 않음 |

실제 도구 회귀는 `UV_OFFLINE=true`로 네트워크 설치를 하지 않고 exact-version 캐시를 사용한다. `uvx` 또는 캐시가 없으면 준비 조건을 명시해 skip하며 다른 실행 실패는 assertion failure다. 이번 실행에서는 skip이 없었다. Audit step 이후 같은 캐시가 있는 CI에서 실행할 수 있다. 실제 fixture는 test-owned이며 repository Inbox의 파일에 의존하지 않는다.

## Reviewed Fingerprints

| File | SHA256 |
| --- | --- |
| [Workflow](../../.github/workflows/ci-lite.yml) | `9b617397c5f1383c65693209a979a557dcd578cb6183bdd3034f2ca2cd7bef3c` |
| [Execution](../../scripts/ci/run_checks.py) | `f3b05209aface322e443f8101d892bc304fefd6ad7cdaa55cb039f8a544eb4f0` |
| [Step tests](../../tests/scripts/ci/test_ci_steps.py) | `c0e56261d70e4c89d1529c486e1b57d1161d7de7c3ac92a45390356d734e117d` |
| [Workflow tests](../../tests/scripts/ci/test_ci_workflow.py) | `78f2577714ae0d515f19221f2d60ec19ad955bb78505cb7b34787c813f7a8b6c` |

## Limits

[이전 리뷰](03-review-ci-zizmor-implementation.md)는 당시 코드에 대한 기록이다. 새로운 actual collector 근거가 F1을 확정하고 F2의 mixed-input 경로를 재현했으므로 이전 no-finding 판정을 현재 수정 전 동작의 안전성 근거로 재사용하지 않는다. 이 기록과 재리뷰가 후속 수정의 근거다.

Commit/push, PR 본문 갱신, remote CI 검증과 reviewer의 수용은 별도 delivery 단계로 남는다. Review thread를 임의로 resolve하거나 Draft·approval·merge 상태를 변경하지 않았다.
