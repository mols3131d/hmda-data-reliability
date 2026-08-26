---
title: "Commits"
description: "하나의 논리적 변경을 review 가능한 history로 기록하기 위한 commit 단위, staging과 history 관리 기준을 정의합니다."
categories:
  - software-engineering
tags:
  - git
---

# Commits

Commit은 하나의 논리적 변경을 기록하고 review 가능한 history를 만든다.

Commit message의 형식, type, 길이와 언어는 [`.gitmessage`](../../../.gitmessage)를 canonical source로 사용한다.

## Change Unit

하나의 commit은 하나의 논리적 변경을 표현한다.

같은 목적의 spec, 문서, test와 구현은 함께 포함할 수 있다. File이나 요청 단위로 기계적으로 나누지 않으며, 관련 없는 변경은 포함하지 않는다.

## Staging

변경은 논리적 변경 단위로 stage한다. 같은 목적의 변경은 함께 포함하고, 다른 목적의 변경은 별도 commit으로 분리한다.

## History

Review가 시작된 공개 history는 인간의 명시적 요청 없이 rewrite하지 않는다. History를 단순하게 유지할 필요가 있으면 merge 시 squash를 사용할 수 있다.

## Agent Instructions

- 사용자가 만든 관련 없는 변경을 commit하거나 되돌리지 않는다.
- 명시적 요청 없이 amend, rebase, reset 또는 force-push로 공개 history를 변경하지 않는다.

## Related

- [Branches](branch.md): commit이 속하는 변경 목적과 branch 기준
- [Pull Requests](pull-request.md): validation과 review 결과를 전달하는 기준
