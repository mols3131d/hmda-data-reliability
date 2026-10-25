---
type: report
title: Shared Pre-Push Git Environment Hazard
description: PR 272의 hook 오염 경고 후 PR 271의 branch·index 점검과 임시 실행 환경 격리 및 PR 277 수정 인계 근거를 기록합니다.
---

# Shared Pre-Push Git Environment Hazard

**Owner for permanent remediation: #277.** Shared pre-push pytest가 Git 로컬 환경변수를 상속하면 임시 Git fixture의 `cwd`만으로 저장소가 격리되지 않습니다. 이 PR은 공유 hook·설정·타 도메인 테스트를 수정하지 않았습니다.

## Observed State And Containment

- **Sibling report:** 사용자가 PR #272의 hook 실행 중 `GIT_DIR`·`GIT_INDEX_FILE` 상속으로 fixture의 `base`/`test change` commit이 sibling의 실제 branch/index를 바꿨으며, sibling private state를 `a85cac28`에 복구했다고 알렸습니다. 이 PR에서 그 오염이나 복구를 재현·검증했다고 주장하지 않습니다.
- **PR #271 action:** 진행 중인 `git push origin HEAD:agent/test/audit-data-platform-design`의 process tree만 중단했습니다. 이 push는 exit `143`으로 종료됐고 원격 head는 여전히 `f1cf36e5baf74f356333c7a7ff70240287e27c55`였습니다.
- **Integrity:** 중단 직후 local HEAD는 알려진 검증 commit `8bf4e6b095aac7377ac0b22052711c96d929f926`이었고, `git diff --cached --exit-code 8bf4e6b0` 및 같은 commit과 tests/design의 working-tree 비교가 모두 empty였습니다. Reflog에도 fixture commit이 없었습니다. 허용된 Inbox 작업만 남아 있어 branch/index 복구를 수행하지 않았습니다.
- **Validation meaning:** 중단된 broad hook 실행은 성공 근거로 세지 않습니다. 기존 final domain 43개와 독립 리뷰의 테스트 코드·검증 기반은 그대로 보존됐습니다.

## Source Evidence

| Location | Observed mechanism |
| --- | --- |
| [lefthook.yml](../../lefthook.yml#L37) | `pytest-affected`가 `uv run --no-sync pytest --testmon --testmon-forceselect`를 환경 정리 없이 실행하며 특정 domain으로 제한하지 않음 |
| [CI repo fixture](../../tests/scripts/ci/conftest.py#L22) | `init/config/commit`으로 임시 저장소를 준비 |
| [Git helper](../../tests/scripts/ci/helpers.py#L44)와 [commit_change](../../tests/scripts/ci/helpers.py#L50) | `subprocess.run`에 `cwd`만 전달하며 parent 환경을 상속; `add -A`·`commit`도 수행 |
| [EDA clean-head test](../../tests/hmda_data/eda/test_eda_evidence.py#L77)와 [dirty-tree test](../../tests/hmda_data/eda/test_eda_evidence.py#L112) | 별도 `env` 없이 Git 초기화·stage·commit을 수행하는 추가 경로 |
| [기존 환경 격리 선례](../../tests/scripts/test_clean.py#L41) | 테스트 안에서 Git 환경을 정리하는 방어가 이미 존재 |

정적 조사는 관련 파일을 읽기만 했습니다. 외부 override를 실제 사용자 저장소에 주입한 상태로 위 위험 fixture를 실행하지 않았습니다.

## Temporary Retry Boundary

Repository와 Git config를 바꾸지 않고 repository 밖의 임시 `uv` wrapper를 준비했습니다. Wrapper는 `uv run --no-sync pytest`에 대해서만 아래 순서로 실행 환경을 정리합니다. 다른 hook 명령은 기존 tool로 전달합니다.

1. `git rev-parse --local-env-vars`로 제거할 이름을 읽습니다. 명령이 실패하면 pytest를 시작하지 않습니다.
1. 복사한 child 환경에서 반환된 이름을 모두 제거합니다. 몇몇 변수를 고정 열거해 나머지를 누락하지 않습니다.
1. 원래 절대 경로의 `uv`를 같은 인자로 실행합니다. Git hook 자체와 검증 명령은 유지합니다.

Synthetic probe에서는 `GIT_DIR`, `GIT_WORK_TREE`, `GIT_INDEX_FILE`, `GIT_COMMON_DIR`를 실제 parent context로 설정한 wrapper를 실행했습니다. Probe는 **변수가 모두 제거됐음을 먼저 assertion한 뒤** `tmp_path`에만 저장소를 만들고 `init/config/add/commit`을 수행했습니다. **1 passed in 0.15s**, parent HEAD/index는 여전히 `8bf4e6b0`과 일치했습니다. 임시 `/dev/null` pytest config의 cache 위치에 대한 warning 1건이 있었으며 Git 격리 assertion과 fixture는 통과했습니다.

이 wrapper는 이번 delivery의 임시 실행 경계입니다. 별도 세션은 이전 `/tmp` 경로가 남아 있다고 가정하지 말고 같은 원칙으로 준비·검증해야 합니다. 영구 hook 수정이 적용되기 전에는 원래 broad pre-push를 같은 환경으로 재실행하지 않습니다.

## PR 277 Handoff

공유 hook이 pytest를 시작하는 child 경계에서 Git 로컬 환경을 제거하도록 수정하고, 합성 parent 저장소의 override를 상속받은 child fixture가 parent HEAD/index/refs를 바꾸지 않는 회귀 검증을 추가하는 것이 권장 조치입니다. Hook의 정상 repository 조회에 필요한 환경과 pytest child 환경을 구분해야 합니다. 실제 사용자 저장소를 오염시키는 재현은 사용하지 않습니다.

영구 수정·공유 회귀 테스트와 admission 판단은 #277 소유입니다. 이 도메인 PR에서 해결했다고 닫지 않습니다. 안전한 retry와 remote CI의 최종 결과는 [통합 보고서](05-report-current-audit.md)가 소유합니다.
