---
title: "CI Markdown Validation"
description: "변경 Markdown의 비차단 formatting, docs 전용 차단 lint, Inbox CI 제외와 branch write-back 경계를 판단할 때 사용하는 계약입니다."
categories:
  - software-engineering
tags:
  - ci
  - markdown
---

# CI Markdown Validation

현재 prospective change set에 포함된 `inbox/**` 밖 Markdown에 적용한다. **포맷 수정 제안과 병합을 막는 lint 검사를 분리한다.** 병합 대상 상태는 [Admission Boundary](admission.md)를 따른다.

## Formatting and Lint

| Changed Markdown | Formatting | Lint | Merge Gate |
| --- | --- | --- | --- |
| `docs/**` | `rumdl fmt` | 포맷 수정 후 `rumdl check` | 남은 lint 위반은 병합 차단 |
| `docs/**`와 `inbox/**` 밖 | `rumdl fmt` | `rumdl check` 미실행 | Markdown lint로 병합을 막지 않음 |

포맷 수정은 일회성 CI 작업 공간에서 실행한다. 차이는 비차단 수정 제안으로 제공하며 **branch에 반영(write-back)하지 않는다.**

Frontmatter나 생성 상태의 일관성처럼 표현 형식과 별개의 계약은 `inbox/**` 밖에서 결정론적 validator로 독립 검증할 수 있다.

## Inbox Exclusion

**`inbox/**` 전체를 CI 검증에서 제외한다.** 포맷 수정, lint, frontmatter, artifact 이름과 bundle root도 검증하지 않는다. 내용, 이름과 metadata 규칙은 [Inbox 지침](../../../inbox/AGENTS.md)으로 유지하되 병합 조건으로 삼지 않는다.

Workflow 생성은 [Admission Boundary](admission.md)를 따른다.

- **Inbox만 변경:** 검증 단계를 선택하지 않는다.
- **다른 경로도 변경:** 다른 경로에 필요한 검증만 수행한다.

구현은 [`run_checks.py`](../../../scripts/ci/run_checks.py)의 `markdown` 검사, 로컬 실행과 현재 결과 제공 방식은 [Testing Guide](../testing.md#local-ci-steps)에서 확인한다.
