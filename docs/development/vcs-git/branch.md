---
title: "Branches"
description: "하나의 변경 목적을 격리하고 검토 가능한 단위로 전달하기 위한 branch 생성, naming, reuse와 agent 제약을 정의합니다."
categories:
  - software-engineering
tags:
  - git
  - github
---

# Branches

브랜치는 하나의 변경 목적을 격리하고 검토 가능한 단위로 전달한다. Research, Plan, Implementation, Review는 branch 구조가 아니라 artifact와 commit으로 구분한다.

## Application

인간은 변경의 맥락과 위험에 따라 이 기준을 유연하게 적용할 수 있다. Agent는 `Agent Instructions` section의 제약을 따른다.

Repository protection, security policy와 권한은 항상 우선한다.

## Change Unit

하나의 branch는 함께 검토하고 병합하며 되돌릴 수 있는 하나의 변경 목적을 가진다.

같은 목적의 spec, 문서, test와 구현은 같은 branch에서 함께 변경할 수 있다. 독립적으로 검토하거나 되돌릴 새 목적은 별도의 branch와 Pull Request로 분리한다.

## Base And Reuse

작업 branch는 원칙적으로 원격 저장소의 현재 `main` head에서 생성한다. 별도의 기준 branch가 지정되면 해당 branch를 사용한다.

기존 branch는 동일 작업의 후속 수정일 때만 재사용한다.

## Naming

```text
[<actor>/]<type>/<topic>
```

| Part | Meaning |
| --- | --- |
| `actor` | 작업 주체를 구분하는 optional namespace |
| `type` | 변경 성격 |
| `topic` | 변경 목적 |

Agent는 actor namespace로 `agent`를 사용한다. 인간은 특별한 구분이 필요하지 않다면 actor를 생략할 수 있다.

```text
feat/reliability-profile
mols/feat/reliability-profile
agent/docs/vcs-git-guides
agent/feat/review-engine
```

`type`은 [`.gitmessage`](../../../.gitmessage)의 Conventional Commit type을 사용한다. `topic`은 변경 목적을 소문자 kebab-case로 표현한다.

## Inbox Delivery

`inbox/` 전용 dedicated branch delivery 예외는 [Inbox Branch Delivery](../../../inbox/_guidelines/branch.md)를 따른다. 그 밖의 branch 작업에는 이 문서의 일반 기준을 적용한다.

## Agent Instructions

- `agent` actor namespace와 자신의 작업 branch를 사용한다.
- 요청된 변경 목적과 범위만 수정한다.
- `main`, 보호 branch 또는 다른 작업 주체의 branch를 명시적 요청 없이 변경하지 않는다.
- [Inbox Branch Delivery](../../../inbox/_guidelines/branch.md)의 조건을 충족하는 경우에만 dedicated `inbox` branch direct push 예외를 사용한다.
- 명시적 요청 없이 force-push, history rewrite 또는 미병합 branch 삭제를 수행하지 않는다.
- 규칙이나 권한이 충돌하면 우회하지 않고 보고한다.

## Related

- [Commits](commit.md): 변경을 commit으로 구성하는 기준
- [Pull Requests](pull-request.md): 변경을 검토와 채택 경계로 전달하는 기준
- [Inbox Branch Delivery](../../../inbox/_guidelines/branch.md): `inbox/` 전용 branch delivery 예외
