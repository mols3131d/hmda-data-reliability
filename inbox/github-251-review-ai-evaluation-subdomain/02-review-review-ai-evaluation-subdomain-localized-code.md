---
type: review
title: Review AI Evaluation Subdomain Code Review
description: PR #251 작업 트리의 독스트링과 DEBUG 로그 변경을 설명 정확성과 실행 가시성 관점에서 검토한다.
---

# Review AI Evaluation Subdomain Code Review

> [!IMPORTANT]
> **Revise** — 독스트링 두 곳이 실제 리비전 판정과 공개 API 범위를 다르게 설명한다. 설명을 현재 동작과 export 목록에 맞춰야 한다.

- **Target** — [PR #251의 현재 작업 트리](https://github.com/mols3131d/hmda-data-reliability/pull/251)에서 수정된 Python 파일 5개
- **Revision** — `HEAD d11fc9da9b126aa1be9af599a9113070e4c0e55a`; 해당 파일들의 미커밋 diff SHA-256 `6a0154f18ab76fc3bec3a3c4634c1c7b63e1d37c4b060fbd610e7fc133fc6b12`
- **Scope** — 독스트링·주석의 동작 설명, 선택적 Langfuse 예외 경계의 DEBUG 로그

## Findings

| ID | Severity | Finding | Action |
| --- | --- | --- | --- |
| F1 | 🟡 Minor | `_project_revision`은 작업 폴더 전체가 깨끗해야 한다고 설명하지만, 실제 검사는 추적 중인 파일만 대상으로 한다. | 추적 파일만 검사하고 미추적 파일은 무시한다고 설명한다. |
| F2 | 🟡 Minor | `evaluation` 공개 모듈은 평가 기준표와 비교 모델만 공개한다고 설명하지만, 함수와 digest helper도 내보낸다. | 독스트링을 실제 공개 목록에 맞춘다. |

## Details

### F1 · 자동 리비전 조건 설명이 실제 검사 범위보다 넓음

🟡 Minor

#### Locations

- [`scripts/run_agentic_review_live.py`](../../scripts/run_agentic_review_live.py)
  - `_project_revision` 독스트링, 242행
  - `_current_git_revision`, 249행 이후
- [`docs/development/testing.md`](../../docs/development/testing.md)
  - 자동 리비전의 기존 조건 설명

#### Evidence

`_project_revision()`은 `auto`일 때 `_current_git_revision()`을 호출한다. 그 함수는 `git status --porcelain --untracked-files=no`로 작업 상태를 확인하므로 추적 중인 파일의 변경만 거부하고 미추적 파일은 무시한다. 독스트링의 “작업 폴더가 깨끗한 경우”는 이 범위를 넘어선다. Testing Guide는 추적 중인 작업 트리가 깨끗해야 한다고 더 정확히 적고 있다.

#### Impact

독자는 미추적 파일도 자동 리비전 계산을 막는다고 오해하거나, 자동 리비전이 실제로 포함하는 상태 범위를 잘못 이해할 수 있다.

#### Action

독스트링을 추적 중인 파일에 변경이 없는 조건으로 좁혀 현재 동작과 맞춘다.

### F2 · 공개 평가 API 설명이 실제 export 목록을 빠뜨림

🟡 Minor

#### Locations

- [`src/hmda_reliability/review_ai/evaluation/__init__.py`](../../src/hmda_reliability/review_ai/evaluation/__init__.py)
  - 독스트링 3행
  - `__all__`, 22–34행

#### Evidence

독스트링은 평가 기준표와 비교 모델만 공개한다고 하지만, `__all__`은 `compare_review_value`, `render_review_value_comparison_markdown`, `review_output_digest`와 평가·점수 열거형 및 모델도 공개한다.

#### Impact

하위 모듈의 공개 경계를 설명하는 독스트링이 일부 API를 누락해 사용자가 가져올 수 있는 평가·비교 기능을 놓칠 수 있다.

#### Action

기준표와 모델뿐 아니라 비교 함수, 요약 렌더러, digest 함수도 포함하는 공개 표면이라고 설명한다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | Ruff 검사와 서식 확인 | 변경된 Python 파일 5개 모두 통과했다. |
| ✅ Pass | `git diff --check` | 공백 오류 없이 통과했다. |
| ⚪ Not Verified | 테스트와 단독 CLI 로그 출력 | 실행하지 않았다. |

## Risks and Limits

- DEBUG 로그는 예외 종류만 기록한다. 단독 CLI 진입점은 로깅 수준을 설정하지 않으므로 기본 설정에서는 로그가 표시되지 않는다. 외부 호출자가 DEBUG 로깅을 설정한 경로는 검증하지 않았다.
