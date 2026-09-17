---
type: report
title: "PR #241 Review Findings and Next Actions"
description: "PR #241에 대한 독립 코드 검토 결과와 병합 전후 권장 후속 작업을 제안합니다."
tags:
  - python
  - tooling
  - architecture
  - review
---

# PR #241 Review Findings and Next Actions

## Overview

PR #241([`chore: adopt Tach dependency boundaries`](https://github.com/mols3131d/hmda-data-reliability/pull/241))에 대한 원격 브랜치 동기화 및 독립 코드 검토(review-lead)를 수행했습니다.

Tach 0.35.1을 활용한 Python 의존성 경계([tach.toml](../../tach.toml)) 설정, 기존 AST 가드([tests/review_ai/test_dependency_boundaries.py](../../tests/review_ai/test_dependency_boundaries.py))와의 상호보완적 검증 분리, CI 워크플로 및 문서화 전반이 체계적으로 구현되어 있습니다.

본 보고서에서는 코드 검토에서 도출된 4건의 세부 이슈(Medium 2건, Low 2건)와 Rulesync 갱신 상태를 정리하고, PR의 안전한 병합과 향후 품질 유지를 위해 제안하는 구체적인 작업 단계를 정의합니다.

---

## Review Findings Summary

| ID | 중요도 | 내용 | 대상 위치 | 권장 조치 |
| --- | --- | --- | --- | --- |
| **F1** | 🟡 Medium | `test_tach.py`의 ambient `PATH` 의존성 | [tests/scripts/test_tach.py](../../tests/scripts/test_tach.py#L28) | `subprocess.run` 호출을 `sys.executable` 인터프리터 바인딩으로 통일 |
| **F2** | 🟡 Medium | `classify_changes.sh`의 `tach` 트리거 패턴에 AST 가드 테스트 누락 | [.github/workflows/classify_changes.sh](../../.github/workflows/classify_changes.sh#L301)<br>[tests/scripts/test_ci_classifier.py](../../tests/scripts/test_ci_classifier.py#L70-L86) | 트리거 패턴에 [tests/review_ai/test_dependency_boundaries.py](../../tests/review_ai/test_dependency_boundaries.py) 추가 및 분류기 회귀 테스트 반영 |
| **F3** | 🔵 Low | `ci-lite.yml`의 경계 검사 스크립트 셸 옵션 일관성 | [.github/workflows/ci-lite.yml](../../.github/workflows/ci-lite.yml#L182-L186) | 멀티라인 스크립트 선두에 `set -euo pipefail` 추가 |
| **F4** | 🔵 Low | `test_tach_config.py`의 모듈 디렉터리 필터 방어성 | [tests/scripts/test_tach_config.py](../../tests/scripts/test_tach_config.py#L26) | `__init__.py` 유무와 무관하게 서브디렉터리를 감지하도록 필터 완화 검토 |

### Finding Details

#### 🟡 Medium — F1 · `test_tach.py`의 `tach` subprocess 호출 인터프리터 바인딩 미보장

- **현황**: [tests/scripts/test_tach.py](../../tests/scripts/test_tach.py#L28)의 `check()` 함수에서 `subprocess.run(["tach", "check"], ...)`를 직접 호출하고 있습니다. 반면 [tests/scripts/test_tach_config.py](../../tests/scripts/test_tach_config.py#L65-L71)에서는 `subprocess.run([sys.executable, "-m", "tach", "check"], ...)`를 사용하여 현재 실행 중인 가상환경 Python 인터프리터를 안정적으로 바인딩합니다.
- **영향**: 개발자 IDE 내장 테스트 러너나 가상환경이 활성화되지 않은 셸 환경에서 실행할 경우, `PATH`에 `tach` CLI 바이너리가 없어 `FileNotFoundError`로 테스트가 오탐 실패할 위험이 있습니다.
- **조치**: `check()` 함수의 실행 명령을 `[sys.executable, "-m", "tach", "check"]`로 수정합니다.

#### 🟡 Medium — F2 · `classify_changes.sh`의 `tach` 선택자에 `test_dependency_boundaries.py` 누락

- **현황**: [.github/workflows/ci-lite.yml](../../.github/workflows/ci-lite.yml#L182-L186)의 `Check Python dependency boundaries` 단계는 `tach check`와 함께 세 개의 테스트 파일([tests/scripts/test_tach.py](../../tests/scripts/test_tach.py), [tests/scripts/test_tach_config.py](../../tests/scripts/test_tach_config.py), [tests/review_ai/test_dependency_boundaries.py](../../tests/review_ai/test_dependency_boundaries.py))을 단일 의존성 경계 검증 단계로 일괄 실행합니다. 하지만 [.github/workflows/classify_changes.sh](../../.github/workflows/classify_changes.sh#L301)의 `tach=true` 케이스에는 `tests/scripts/test_tach*.py`만 등록되어 있습니다.
- **영향**: AST 의존성 가드인 [tests/review_ai/test_dependency_boundaries.py](../../tests/review_ai/test_dependency_boundaries.py)만 단독 수정된 PR의 경우 `tach=false`로 판정되어 통합 의존성 경계 단계가 건너뛰어집니다.
- **조치**: [.github/workflows/classify_changes.sh](../../.github/workflows/classify_changes.sh#L301) 패턴에 `tests/review_ai/test_dependency_boundaries.py`를 추가하고, [tests/scripts/test_ci_classifier.py](../../tests/scripts/test_ci_classifier.py)의 `test_architecture_changes_prepare_and_run_boundary_check` 테스트 케이스에 해당 경로를 반영합니다.

#### 🔵 Low — F3 · `ci-lite.yml` 셸 옵션 컨벤션 일치

- **현황**: [.github/workflows/ci-lite.yml](../../.github/workflows/ci-lite.yml) 내의 다른 멀티라인 bash 단계들은 선두에 `set -euo pipefail`을 선언하고 있으나, 신규 추가된 `Check Python dependency boundaries` 단계에는 생략되어 있습니다.
- **영향**: 현재는 2개의 순차 명령어로 동작하지만 향후 파이프라인 확장 시 실패 감지 일관성이 저하될 수 있습니다.
- **조치**: 스크립트 블록 첫 줄에 `set -euo pipefail`을 추가합니다.

#### 🔵 Low — F4 · `test_tach_config.py`의 모듈 탐색 방어성

- **현황**: [tests/scripts/test_tach_config.py](../../tests/scripts/test_tach_config.py#L26)의 `expected_modules` 추출식이 `if path.is_dir() and (path / "__init__.py").is_file()`로 선언되어 있습니다.
- **영향**: `src/hmda_reliability` 아래에 실수로 `__init__.py`가 누락된 신규 서브패키지가 추가될 경우 테스트 검출을 우회하고 상위 루트 모듈로 묵시적 편입될 수 있습니다.
- **조치**: `path.is_dir() and not path.name.startswith((".", "_"))` 조건을 적용하여 모든 서브패키지 디렉터리가 [tach.toml](../../tach.toml) 모듈 목록과 동기화되도록 강제하는 방안을 검토합니다.

---

## Tooling & Rulesync Status

- **Rulesync Lockfile Update**: `scripts/agent_assets.py update`를 실행하여 최근 추가된 `mols-tach` 및 `mols-agent-asset-find` 스킬의 최신 무결성 해시(integrity hash)를 [rulesync.lock](../../rulesync.lock)에 정상 반영했습니다.
- **Validation**: `scripts/rulesync.py validate` 검증을 통과하여 프로젝션 드리프트가 없음을 확인했습니다.

---

## Proposed Next Actions

### Phase 1: PR #241 병합 전 즉각 반영 작업 (Required for Merge)

- [x] **Task 1.1 (`F1` 해결)**: [tests/scripts/test_tach.py](../../tests/scripts/test_tach.py)에서 `check()` 함수를 `[sys.executable, "-m", "tach", "check"]`로 변경.
- [x] **Task 1.2 (`F2` 해결)**:
  - [.github/workflows/classify_changes.sh](../../.github/workflows/classify_changes.sh#L301) 패턴에 `tests/review_ai/test_dependency_boundaries.py` 추가.
  - [tests/scripts/test_ci_classifier.py](../../tests/scripts/test_ci_classifier.py)에 해당 경로 단독 변경 시 `tach=true` 검증 케이스 추가.
- [x] **Task 1.3 (`F3` 해결)**: [.github/workflows/ci-lite.yml](../../.github/workflows/ci-lite.yml#L182-L186) 단계에 `set -euo pipefail` 추가.
- [x] **Task 1.4 (Rulesync 동기화)**: 갱신된 [rulesync.lock](../../rulesync.lock)을 PR 변경 내역에 포함.

### Phase 2: 로컬 전체 검증 및 PR 갱신 (Verification & PR Update)

- [x] **Task 2.1 (로컬 검증 실행)**:
  - `uv run --no-sync tach check`
  - `uv run pytest tests/scripts/test_tach.py tests/scripts/test_tach_config.py tests/review_ai/test_dependency_boundaries.py tests/scripts/test_ci_classifier.py`
  - `uv run ruff check .` && `uv run ruff format --check .`
  - `uv run rumdl check docs/`
  - `uv run python scripts/tombi.py lint .`
  - `uv run ty check`
- [ ] **Task 2.2 (커밋 및 푸시)**: 원격 `chore/adopt-tach-dependency-boundaries`에 변경 사항 커밋 및 푸시.
- [ ] **Task 2.3 (CI Lite 통과 확인 및 Draft 해제)**: GitHub Actions CI Lite 통과 확인 후 Draft 상태를 Ready for Review로 전환.

### Phase 3: 후속 모니터링 및 확장 과제 (Post-Merge / Future Architecture)

- [x] **Task 3.1 (`F4` 해결)**: [tests/scripts/test_tach_config.py](../../tests/scripts/test_tach_config.py) 모듈 디렉터리 필터 방어성 보완(`path.is_dir() and not path.name.startswith((".", "_"))`).
- [ ] **Task 3.2 (전이적 의존성 모니터링)**: `shared`나 루트 유틸 모듈을 통한 AI 모듈 간접 노출(Proxy Re-export) 여부를 모니터링하고, 향후 필요 시 `exact = true` 기반의 전체 허용 목록(`depends_on`) 도입 검토.
