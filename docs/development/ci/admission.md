---
title: "CI Admission Boundary"
description: "main 대상 PR의 필수 검증, prospective merge와 required workflow 생성 조건을 판단할 때 사용하는 병합 계약입니다."
categories:
  - software-engineering
tags:
  - ci
  - github-actions
---

# CI Admission Boundary

`main` 대상 PR의 필수 검증과 검증 대상 상태를 정의한다. 목적과 판단 원칙은 [Continuous Integration](README.md)을 따른다.

## Requirements

- 통합 경계는 `main`이다.
- `main`에 부적합한 문제는 병합 전에 차단할 수 있어야 한다.
- 비용만으로 필수 검증을 post-merge로 미루지 않는다.
- 검증 대상은 **PR head 단독이 아니라 `main`과 합쳐질 상태(prospective merge)**다.
- `main` 대상 PR에는 **required workflow를 항상 생성한다.** 불필요한 검사는 workflow 내부에서 생략한다.

검증 선택과 영향 범위가 불확실할 때의 처리는 [Change Impact](change-impact.md#selection-and-failure)를 따른다.

> [!IMPORTANT]
> Workflow 생성이나 검증 선택기(selector) 실행만으로 필수 검증이 완료됐다고 보지 않는다.

정확한 trigger와 step 조건은 [workflow](../../../.github/workflows/ci-lite.yml), 현재 실행 동작은 [Testing Guide](../testing.md#pull-request-ci)에서 확인한다.
