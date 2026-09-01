---
title: "README Authoring"
description: "`docs/**`의 디렉터리나 문서·파일 묶음에 README가 필요한지 판단하고 entrypoint의 범위, 첫 행동과 navigation을 설계할 때 사용하는 정책입니다."
categories:
  - software-engineering
tags:
  - documentation
  - markdown
  - readme
---

# README Authoring

이 정책에서 `README.md`는 `docs/**` 아래 디렉터리나 문서·파일 묶음의 **진입점**이다. 모든 내용을 담는 설명서가 아니라, 이 범위가 무엇인지 빠르게 이해하고 다음에 무엇을 볼지 결정하게 한다.

디렉터리나 묶음이 있다는 이유만으로 README를 만들지 않는다. 시작점에서 안내해야 할 responsibility가 있을 때만 둔다.

## Responsibility

다음 중 하나 이상이 실제로 필요하면 README를 둘 근거가 된다.

- 이름만으로 목적이나 responsibility boundary를 알기 어렵다.
- 여러 하위 문서·파일 중 무엇을 봐야 할지 먼저 판단해야 한다.
- 이 범위에만 적용되는 유지보수·복구 규칙이 있다.
- 문서나 파일 묶음을 하나의 단위로 이해하기 위한 시작 설명이 필요하다.

README에는 진입에 필요한 내용만 둔다. 자세한 tutorial, 긴 reference, 반복되는 policy와 자동으로 만들 수 있는 단순 파일 목록은 더 적절한 owning source나 generated projection에 맡긴다.

범위에서 계속 필요한 짧은 원칙이나 규칙이지만 독립 문서로 만들 만큼 responsibility가 크지 않다면 README에 간결하게 둘 수 있다. 내용이 커지거나 따로 찾아 유지해야 할 필요가 생기면 별도 문서로 분리한다.

## Authoring Questions

고정된 template을 채우기보다 이 범위에서 실제로 필요한 질문에 답한다.

- 이 범위는 무엇을 맡고 무엇을 위한 것인가?
- 독자는 언제 이 범위를 찾아야 하는가?
- 가장 먼저 무엇을 하거나 어떤 문서를 읽어야 하는가?
- 더 자세한 procedure, reference나 도움말은 어디에 있는가?
- responsibility나 contribution boundary가 불분명하다면 무엇이 이를 소유하는가?

루트 README와 하위 README는 같은 구성을 기계적으로 복제하지 않는다. 각 README는 자신이 대표하는 범위에 필요한 내용만 가진다.

## Recommended Flow

README는 독자의 읽기 순서에 맞춰 **범위 소개 → 첫 행동 → 자세한 정보**로 확장한다.

1. 첫 부분에서 이 범위가 무엇이며 언제 쓰는지 짧게 밝힌다.
1. 행동 전에 꼭 알아야 할 전제, boundary나 선택 조건이 있으면 먼저 둔다.
1. 바로 사용을 시작해야 한다면 가장 짧은 권장 경로를 보여준다.
1. 자세한 절차와 reference는 owning source로 연결하고 README에는 진입에 필요한 내용만 남긴다.
1. 사람이 여러 문서를 골라야 한다면 작은 navigation section을 둘 수 있다.

필요 없는 단계나 section은 만들지 않는다.

## Writing Rules

- 핵심 정보와 중요한 조건을 문단과 section 앞에 둔다.
- 한 문단에는 하나의 핵심을 두고 얕은 heading hierarchy를 사용한다.
- procedure는 가장 권장하는 한 경로부터 보여주고, 대안은 실제 선택을 바꿀 때만 추가한다.
- repository 내부 문서는 clone이나 branch가 달라도 유지되는 상대 경로 link를 우선한다.
- GitHub가 heading 기반 outline을 제공하므로 수동 목차를 기본값으로 두지 않는다.
- badge나 상태 요약은 현재 상태를 정확히 반영하고 판단에 도움이 될 때만 둔다.
- `Welcome`, `Overview` 같은 형식적 서론보다 범위의 핵심을 바로 제시한다.

## Scope Metadata

README frontmatter는 README 파일 자체가 아니라 **대표하는 디렉터리나 문서 묶음의 metadata**를 담는다.

- `description`은 그 범위를 언제 찾아보거나 사용해야 하는지 설명한다.
- `title`은 README라는 파일명이 아니라 그 범위를 사람이 읽을 이름으로 적는다.

상세한 frontmatter 적용과 description 작성 기준은 [Frontmatter](frontmatter.md)를 따른다.

## Quality Gate

README를 추가하거나 크게 수정할 때 확인한다.

- 첫 부분만 읽어도 범위의 목적, 사용 시점과 다음 행동을 판단할 수 있는가?
- 각 section이 독자의 이해·선택·행동을 실제로 바꾸는가?
- 자세한 내용이나 반복 policy가 더 적절한 owning source로 빠졌는가?
- repository 내부 link가 가능한 한 상대 경로인가?
- 하위 파일이 추가되거나 정렬 순서가 바뀌어도 단순 목록 변화 때문에 쉽게 낡지 않는가?
- frontmatter가 README 파일이 아니라 대표 범위를 설명하는가?

## Boundaries

문서 생성·배치의 공통 원칙은 [Documentation Principles](principles.md)가 소유한다. Frontmatter schema는 [`../../frontmatter.json`](../../frontmatter.json), frontmatter 작성 기준은 [Frontmatter](frontmatter.md)가 소유한다.
