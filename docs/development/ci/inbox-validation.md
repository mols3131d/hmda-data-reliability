---
title: "CI Inbox Validation"
description: "현재 변경된 Inbox artifact의 metadata·이름 검증 범위와 과거 artifact·무관한 테스트의 제외 조건을 판단할 때 사용하는 계약입니다."
categories:
  - software-engineering
tags:
  - ci
  - inbox
---

# CI Inbox Validation

Inbox 전체를 매 PR마다 다시 검사하지 않는다. **현재 prospective change set에 포함된 Inbox artifact만** 현재 변경으로 취급한다.

## Changed Artifact Boundary

- 현재 변경된 일반 Inbox Markdown은 [Markdown Validation](markdown-validation.md)의 non-blocking formatting만 적용하고, common artifact root의 required frontmatter·이름 정합성처럼 명시적인 Inbox contract만 별도로 검증한다.
- Standalone artifact와 변경된 bundle에서 도달 가능한 `README.md` root는 `type`, `title`, `description`과 artifact name의 `type` 정합성을 확인한다.
- 현재 변경에 포함되지 않은 과거·완료·보관 artifact는 scan, reformat, migration 또는 재검증하지 않는다.
- 일반 Inbox artifact 변경만으로 unrelated source test나 platform-specific runtime 검증을 실행하지 않는다.
- `inbox/AGENTS.md`, `inbox/_guidelines/**`, `inbox/_templates/**`도 Markdown lint 자체로 병합을 막지 않는다. 해당 path가 소유하는 별도 deterministic contract가 있으면 그 검증은 유지한다.

예를 들어 기존 bundle의 하위 문서만 바뀌어도 도달 가능한 root의 명시적인 artifact 계약을 확인한다. 그 변경을 이유로 다른 과거 bundle까지 검사하지 않는다.

Inbox 자체의 내용과 lifecycle은 [`inbox/AGENTS.md`](../../../inbox/AGENTS.md)가 소유한다. Artifact root 검증은 [`validate_inbox_artifacts.py`](../../../scripts/validate_inbox_artifacts.py), CI 연결은 [workflow](../../../.github/workflows/ci-lite.yml)에서 확인한다.
