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
| `actor` | branch 작업을 책임지고 주도하는 주체를 구분하는 optional namespace |
| `type` | 변경 성격 |
| `topic` | 변경 의도와 행동 |

`actor`는 branch를 생성하거나 명령을 실행한 도구가 아니라 작업을 실질적으로 책임지고 주도하는 주체를 나타낸다. 인간이 Agent를 사용해 작업하더라도 인간이 작업을 주도하면 인간 주도 branch다. 인간은 특별한 구분이 필요하지 않다면 actor를 생략할 수 있고, Agent가 작업을 주도할 때는 `agent`를 사용한다.

```text
feat/add-reliability-profile
mols/feat/add-reliability-profile
agent/docs/clarify-vcs-git-guides
agent/chore/adopt-mols-text-optimizer
```

`type`은 [`.gitmessage`](../../../.gitmessage)의 Conventional Commit type을 사용한다. `topic`은 변경 대상의 이름만 쓰지 않고 변경 의도와 수행할 행동이 드러나도록 소문자 kebab-case로 표현한다.

## Agent Instructions

- 자신이 작업을 주도하는 branch에서는 `agent` actor namespace와 자신의 작업 branch를 사용한다.
- 인간이 주도하는 branch에서는 Agent가 작업에 참여한다는 이유만으로 `agent` namespace를 사용하지 않는다.
- 요청된 변경 목적과 범위만 수정한다.
- `main`, 보호 branch 또는 다른 작업 주체의 branch를 명시적 요청 없이 변경하지 않는다.
- 명시적 요청 없이 force-push, history rewrite 또는 미병합 branch 삭제를 수행하지 않는다.
- 규칙이나 권한이 충돌하면 우회하지 않고 보고한다.

## Related

- [Commits](commit.md): 변경을 commit으로 구성하는 기준
- [Pull Requests](pull-request.md): 변경을 검토와 채택 경계로 전달하는 기준
