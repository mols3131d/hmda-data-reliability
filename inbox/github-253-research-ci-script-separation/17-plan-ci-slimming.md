---
type: plan
title: "CI Slimming"
description: "PR 253에서 불필요한 CI 실행과 실행용 CLI를 줄이는 작업 범위, 완료 기준과 검증 기록입니다."
---

# CI Slimming

현재 PR의 Python 전환 작업에 이어 CI 실행 비용과 유지보수 표면을 줄인다. 사용자 승인 범위는 앞서 제안한 불필요한 실행 축소와 CI 전용 인터페이스 통합이다. 새 branch나 PR을 만들지 않으며 commit과 push는 이번 작업에 포함하지 않는다.

## Scope

- Wheel 빌드는 패키지 소스, build/dependency 설정, Python 버전과 패키지 README/license 입력 변경에만 선택한다. 테스트나 CI 스크립트만 바뀌면 선택하지 않는다.
- 명시적 lock 검사는 `pyproject.toml`, `uv.lock`, `.python-version` 변경에 선택한다. 나머지 Python 검증의 `uv sync --locked`는 유지한다.
- JSON과 TOML 도구는 각각 필요할 때만 설치한다. TOML 대상이 없는 경우 단순 버전 출력을 제거하고 wrapper 계약 테스트는 유지한다.
- 검사 실행부를 단일 CLI와 검사별 함수로 통합한다. 외부 revision 인자는 제거하되 내부 Git 비교의 실패, 삭제 제외, 특수 파일명 계약은 유지한다.
- 실행 방법과 선택 조건의 canonical 문서를 실제 구현에 맞춘다.

## Preserved Boundary

Prospective merge, 항상 생성되는 required workflow, Inbox 제외, 기존 Markdown 수정 제안과 docs lint, OpenSpec, 테스트와 타입 검사, Tach, 의존성 runtime smoke는 유지한다. 도메인별 영향 매핑과 전체 테스트 선택 정책은 재설계하지 않는다. 기존 선택 누락 문제는 이번 단순화의 해결 결과로 주장하지 않는다.

## Acceptance

- 테스트와 CI 스크립트 단독 변경은 wheel 빌드와 명시적 lock 검사를 선택하지 않는다.
- 패키지 소스와 빌드 입력은 wheel 빌드를, 의존성 입력은 lock 검사와 기존 필수 검증을 선택한다.
- JSON-only/TOML-only 변경은 대응 도구만 설치한다.
- 실행 CLI는 revision 인자를 받지 않으며 잘못된 Git 비교와 외부 도구 실패는 성공으로 바뀌지 않는다.
- 기존 CI 계약 테스트, focused lint/type 검사와 별도 independent review로 현재 변경 상태를 확인한다.
- 원격 Actions 시간 개선은 측정하지 않았다면 수치로 주장하지 않는다.

## Status

2026-10-07 현재 `agent/research-ci-script-separation`, HEAD `fb1dde201ee1729d6277bb5bb5181a1a7c2e8126` 위 미커밋 작업 상태에서 승인된 구현을 완료했다. 실행부 5개를 `scripts/ci/run_checks.py`로 통합해 CI Python 모듈을 8개에서 4개로 줄였다. Canonical 실행 안내는 [Testing Guide](../../docs/development/testing.md#local-ci-steps)에 반영했다. Commit, push와 원격 PR 변경은 수행하지 않았다.

## Validation

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

## Limits and Follow-Ups

- 원격 Actions, 실제 npm 설치와 wheel 빌드를 이번 작업에서 실행하지 않았다. 원격 CI 시간 절감량도 측정하지 않았다. Push 후 원격 검증은 별도 작업이다.
- 수동 분류용 Testing Guide의 `git diff --name-only` 예시는 rename 처리에서 실제 CI와 다를 수 있다. 두 번째 리뷰의 Low/follow_up이며 실제 workflow의 수정된 수집 경로에는 영향이 없다.
- 기존 `FULL_UNIT`의 비-CI TARGETS 보완 누락, logger consumer 매핑, OpenSpec의 `full_type`/`python` 조건 불일치, ASCII 공백·tab target 직렬화 제한은 이번 승인 범위에서 재설계하지 않았다. 새 구현이 이 문제를 해결했다고 주장하지 않는다.
