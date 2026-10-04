---
title: "CI Markdown Validation"
description: "변경 Markdown의 비차단 formatting, docs 전용 차단 lint와 branch write-back 경계를 판단할 때 사용하는 계약입니다."
categories:
  - software-engineering
tags:
  - ci
  - markdown
---

# CI Markdown Validation

현재 prospective change set에 포함된 Markdown에 적용한다. **Formatting과 merge-blocking lint를 분리한다.** 병합 대상 상태는 [Admission Boundary](admission.md)를 따른다.

## Formatting and Lint

- 현재 prospective change set에 포함된 모든 Markdown은 CI의 disposable workspace에서 `rumdl fmt`를 실행한다. Formatting 차이는 수정 제안으로 제공하되 병합을 막지 않으며 branch에 write-back하지 않는다.
- `docs/**`의 변경된 Markdown만 formatting 이후 `rumdl check`를 실행한다. 이 범위에서 formatter 이후에도 남는 lint 위반은 병합을 막는다.
- `docs/**` 밖의 Markdown에는 `rumdl check`를 실행하지 않으며 Markdown lint 자체를 merge admission 조건으로 사용하지 않는다.
- Frontmatter, artifact naming, generated-state consistency처럼 Markdown 표현 형식과 별개의 repository contract가 있으면 해당 deterministic validator가 독립적으로 검증할 수 있다.

Inbox에 추가로 적용되는 artifact 계약은 [Inbox Validation](inbox-validation.md)을 따른다.

실행 구현은 [`markdown.sh`](../../../scripts/ci/markdown.sh), local 실행과 현재 결과 제공 방식은 [Testing Guide](../testing.md#local-ci-steps)에서 확인한다.
