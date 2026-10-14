---
type: plan
title: "CI Slimming"
description: "PR 253에서 불필요한 CI 실행과 실행용 CLI를 줄이는 작업 범위, 완료 기준과 검증 기록입니다."
---

# CI Slimming

현재 PR의 Python 전환 작업에 이어 CI 실행과 유지보수 표면을 줄인다. 첫 단계는 불필요한 실행 축소와 CI 전용 인터페이스 통합이며, 후속 사용자 요청으로 분류 정책 자체의 단순화도 승인됐다. 새 branch나 PR을 만들지 않는다. 첫 단계는 별도 commit/push 요청으로 `3af2688`에 반영됐고, 후속 단순화는 아직 미커밋 상태다.

## Scope

- Wheel 빌드는 패키지 소스, build/dependency 설정, Python 버전과 패키지 README/license 입력 변경에만 선택한다. 테스트나 CI 스크립트만 바뀌면 선택하지 않는다.
- 명시적 lock 검사는 `pyproject.toml`, `uv.lock`, `.python-version` 변경에 선택한다. 나머지 Python 검증의 `uv sync --locked`는 유지한다.
- JSON과 TOML 도구는 각각 필요할 때만 설치한다. TOML 대상이 없는 경우 단순 버전 출력을 제거하고 wrapper 계약 테스트는 유지한다.
- 검사 실행부를 단일 CLI와 검사별 함수로 통합한다. 외부 revision 인자는 제거하되 내부 Git 비교의 실패, 삭제 제외, 특수 파일명 계약은 유지한다.
- 실행 방법과 선택 조건의 canonical 문서를 실제 구현에 맞춘다.

## Preserved Boundary

Prospective merge, 항상 생성되는 required workflow, Inbox 제외, 기존 Markdown 수정 제안과 docs lint, OpenSpec, 테스트와 타입 검사, Tach, 의존성 runtime 검증은 유지한다. 첫 단계에서는 도메인별 영향 매핑과 전체 테스트 정책을 제외했지만 후속 요청은 이 정책의 단순화를 포함한다.

## Acceptance

- 테스트와 CI 스크립트 단독 변경은 wheel 빌드와 명시적 lock 검사를 선택하지 않는다.
- 패키지 소스와 빌드 입력은 wheel 빌드를, 의존성 입력은 lock 검사와 기존 필수 검증을 선택한다.
- JSON-only/TOML-only 변경은 대응 도구만 설치한다.
- 실행 CLI는 revision 인자를 받지 않으며 잘못된 Git 비교와 외부 도구 실패는 성공으로 바뀌지 않는다.
- 기존 CI 계약 테스트, focused lint/type 검사와 별도 independent review로 현재 변경 상태를 확인한다.
- 원격 Actions 시간 개선은 측정하지 않았다면 수치로 주장하지 않는다.

## Initial Implementation

2026-10-07 `agent/research-ci-script-separation`, HEAD `fb1dde201ee1729d6277bb5bb5181a1a7c2e8126` 위에서 첫 구현을 완료했다. 실행부 5개를 `scripts/ci/run_checks.py`로 통합해 CI Python 모듈을 8개에서 4개로 줄였다. Canonical 실행 안내는 [Testing Guide](../../docs/development/testing.md#local-ci-steps)에 반영했다. 이후 사용자 요청으로 commit `3af2688ef5abd5effbf40705a5a54b132fef4124`를 생성하고 기존 PR branch에 push했다.

## Initial Validation

| Check | Result | Boundary |
| --- | --- | --- |
| `pytest tests/scripts/ci` | 201 passed, 24.27s | 실제 Git·CLI·workflow 계약과 통제된 외부 도구 argv 검증 |
| Ruff check / format | Pass, 13 files | CI 모듈과 대응 테스트 |
| ty check | Pass | CI 모듈과 대응 테스트 |
| rumdl check | Pass, 4 files | 변경된 canonical 문서 3개와 이 artifact |
| Native Inbox validator | Pass | 이 artifact의 naming·metadata |
| `git diff --check` | Pass | tracked diff 공백 오류 |
| `review-lead` | clear | quality·adversarial 독립 검토, 현재 CI 변경 범위 |

첫 독립 리뷰는 rename된 build 입력의 이전 경로 누락을 High/current_required로 확인했다. Git 수집에 `--no-renames`를 적용하고 실제 `README.md → PROJECT.md` rename commit을 workflow 분류 명령에 전달하는 회귀 테스트로 수정했다. 수정 후 전체 CI 계약 테스트와 정적 검사를 재실행하고 새 독립 리뷰에서 clear를 받았다. 리뷰어는 명령 실행 도구 제한으로 제공된 실행 결과를 독립 재실행하지 않았으며 코드·테스트·baseline을 대조했다.

## Classifier Simplification

후속 요청의 목표는 줄 수 압축이 아니라 수동 규칙과 상태 조합 제거다. Baseline은 `3af2688`이며 다음 정책으로 변경했다.

- 수동 domain reverse-consumer 표와 개별 script-test 매핑을 제거한다. 소스·의존성·dbt·domain 실행 script와 불명확한 변경은 전체 non-resource suite를 선택한다.
- 일반 script는 `tests/scripts`, CI 변경은 `tests/scripts/ci`, domain test 변경은 해당 directory를 선택한다. 삭제·rename도 남은 directory 계약을 유지하고 directory가 없으면 전체 검사로 넓힌다.
- `full_unit`, `ci_targets`와 unit 뒤 non-unit 보완을 제거한다. 전체 또는 선택 범위 모두 `unit`, `component`, `integration`을 유지한다.
- 의존성의 전체 suite에 dbt·Airflow smoke가 포함되므로 `runtime_smoke` output과 별도 workflow 단계를 제거한다.
- 전체 type 검사 선택 시 Python 실행 selector도 활성화해 OpenSpec fallback의 두 값이 어긋나지 않게 한다.

이 정책은 수동 dependency 지식과 선택 누락 위험을 줄이는 대신 소스 변경의 실행 범위를 넓힌다. CI 실행 시간 단축은 목표 또는 확인된 결과로 주장하지 않는다. 후속 검증은 아래와 같으며 독립 리뷰 결과는 별도 완료 응답에서 전달한다.

| Check | Result | Boundary |
| --- | --- | --- |
| `pytest tests/scripts/ci` | 203 passed, 17.93s | Git·CLI·분류·workflow 계약; 삭제·공백 fallback 수정 후 재실행 |
| Full non-resource pytest, `-n 4` | 880 passed, 1 skipped, 278.53s | 로컬 전체 suite; CI의 `-n auto` worker 수와 다름 |
| Ruff check / format | Pass, 13 files | CI 모듈과 대응 테스트 |
| Full `ty check --exclude inbox/**` | Pass | project-wide type 검사 |
| rumdl check | Pass, 3 files | 이번 후속 변경 문서 |
| Native Inbox validator / `git diff --check` | Pass | naming·metadata·diff 공백 |

분류기는 baseline 271줄에서 180줄로 줄었다. 첫 후속 독립 리뷰는 CI test directory 전체 소멸 시 fallback 누락을 current_required로 확인했다. 존재 확인과 전체 검사 fallback을 추가하고 CI·일반 domain directory 소멸 회귀 2개를 추가했다. 재검토는 ASCII 공백·tab을 포함한 신규 test directory가 target 전달에서 분리되는 회귀를 확인했다. 해당 directory를 전체 검사로 넓히고 classifier→runner 경계 테스트 2개를 추가했다. 각각 focused 3개와 최종 CI 계약 203개 및 정적 검사는 통과했다. 전체 runtime 결과는 마지막 두 fallback 수정 이전 상태의 실행이며, 해당 수정 뒤 전체 runtime을 다시 실행하지 않았다. 리뷰어의 Git 실행 제한은 HEAD 대상 파일의 읽기 전용 snapshot을 제공해 baseline 대조 근거로 보완했다.

## Hardcoding Removal

추가 사용자 요청으로 앞선 단순화에 남아 있던 이름 기반 실행 영향 추정을 제거했다. 기존 미커밋 상태를 baseline으로 보존하고 다음 변경을 적용했다.

- `scripts/run_*.py`와 logger 이름 예외를 제거하고 CI 밖 Python script는 모두 전체 non-resource suite와 전체 type 검사로 통일한다.
- Canonical Spec의 capability→test directory·file 매핑을 삭제한다. 모든 Canonical Spec이 전체 검사를 선택하지만 대상 Spec·연관 active Change·archive 구조 검증 선택은 유지한다. 유효한 신규 capability라는 이유만으로 bulk 구조 검증을 강제하지 않는다.
- 의존성 입력 목록은 `DEPENDENCY_INPUTS` 한곳에서 정의하고 Python·lock·build·Tach·전체 검사 선택에서 재사용한다.
- 새 script와 실제 신규 capability directory의 classifier→runner 계약 테스트를 추가한다. 최종 CI suite 207 passed, 21.28s; CI 모듈·테스트 13개 파일의 Ruff check/format와 focused ty, 변경 문서 3개의 rumdl과 `git diff --check`도 통과했다. 이번 단계에서 전체 domain runtime은 재실행하지 않았다. 독립 리뷰 결과는 완료 응답에서 전달한다.

일반 script와 Canonical Spec의 검사 범위는 앞선 정책보다 넓어진다. 버전 고정·Inbox 제외·docs lint 등 명시적인 저장소 정책은 유지하고, 이름 매핑을 별도 설정 파일로 옮기거나 generic rule engine을 추가하지 않는다.

## Limits and Follow-Ups

- 원격 Actions, 실제 npm 설치와 wheel 빌드를 이번 작업에서 실행하지 않았다. 원격 CI 시간 변화도 측정하지 않았다.
- 로컬 전체 suite는 4분 38초였지만 원격의 환경 설치·검사까지 합친 10분 timeout 충족은 미확인이다.
- 수동 분류용 Testing Guide의 `git diff --name-only` 예시는 rename 처리에서 실제 CI와 다를 수 있다. 두 번째 리뷰의 Low/follow_up이며 실제 workflow의 수정된 수집 경로에는 영향이 없다.
- 첫 단계에서 남겼던 `FULL_UNIT`의 비-CI target 보완 누락과 logger consumer 매핑은 후속 전체 검사 정책으로 제거하고 OpenSpec fallback의 Python selector도 맞췄다. ASCII 공백·tab target 직렬화 제한은 남아 있지만 classifier의 동적 directory는 전체 검사로 전환해 해당 제한을 전달하지 않는다.
