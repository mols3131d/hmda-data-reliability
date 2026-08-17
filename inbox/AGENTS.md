# Inbox

`inbox/`는 investigation, review, discussion, briefing과 decision support 과정에서 생성되는 working non-canonical artifact를 보관한다.

Routine artifact의 owning location은 dedicated `inbox` branch다. `main`에는 routine artifact를 복제하지 않는다.

`AGENTS.md`, `README.md`, `_guidelines/`, `_templates/`는 inbox 운영 자산이며 routine artifact가 아니다.

## Workflow

1. Artifact의 primary purpose와 type을 정한다.
1. 필요한 경우 해당 type guideline만 읽는다.
1. `inbox` branch의 현재 날짜 디렉터리에 artifact를 작성한다.
1. Branch·push·formatting·sync 규칙은 [Inbox Branch](_guidelines/branch.md)를 따른다.

## Artifact Contract

Artifact type은 open-ended다. 명확한 purpose-based lowercase kebab-case type을 사용한다. 적절한 type이 없으면 긴 문서는 `report`, 짧은 문서는 `brief`를 사용한다.

Filename과 frontmatter에는 같은 type을 사용한다.

```yaml
---
type: <artifact-type>
title: <title>
description: <description>
tags: [] # Optional
---
```

`type`은 required다. 다른 field는 식별이나 retrieval에 도움이 될 때만 추가한다.

## Paths

```text
inbox/YYYY-MM-DD/HH-MM-<type>-<domain>[-<subdomain>][-<capability>]-<short-title>[-<extensions>].md
inbox/YYYY-MM-DD/HH-MM-<type>-<domain>[-<subdomain>][-<capability>]-<short-title>[-<extensions>]/*
```

- Date와 time은 `Asia/Seoul` 기준으로 정한다.
- Lowercase kebab-case를 사용한다.
- `type`, `domain`, `short-title`은 required다.
- Optional component는 identification이나 indexing에 실제 도움이 될 때만 추가한다.

## Routing

| Type | Guideline |
| --- | --- |
| `research` | [Research](_guidelines/research.md) |
| `review` | [Review](_guidelines/review.md) |
| `discuss` | [Discuss](_guidelines/discuss.md) |

그 밖의 type은 이 common contract를 따른다. 반복적으로 별도 contract가 필요한 type에만 guideline을 추가한다.

## Writing

- Human readability와 낮은 interpretation cost를 우선한다.
- Material한 경우 verified fact, inference, assumption, unresolved uncertainty를 구분한다.
- Structure나 visual은 comprehension을 개선할 때만 사용한다.
- Secret, full generated output, large log는 저장하지 않는다.

## Discovery

- Routine artifact는 `inbox` branch의 date directory와 filename으로 후보를 찾고, 필요한 파일의 frontmatter/content를 직접 확인한다.
- Repository search는 `inbox` branch를 대상으로 검색할 수 있을 때만 보조적으로 사용하며, 그렇지 않은 search miss를 artifact 부재로 해석하지 않는다.
- `README.md`는 static human entrypoint이며 artifact index나 status projection이 아니다. Routine artifact 추가 시 갱신하지 않는다.
- Artifact 내용이 판단에 필요하면 `inbox` branch의 원본을 직접 연다. Filename이나 directory listing만으로 상태를 추론하지 않는다.

## Lifecycle

- Routine artifact와 archive는 branch와 관계없이 non-canonical이다.
- 새 routine artifact는 `inbox` branch에만 보관하며 `main:/inbox/YYYY-MM-DD/**`나 `main:/inbox/archive/**`로 promotion하지 않는다.
- 장기적으로 유지할 결정이나 계약은 해당 canonical owner에 필요한 내용을 다시 작성한다.
- Inbox artifact는 evidence나 작업 기록으로 남을 수 있지만 canonical owner를 대신하지 않는다.
- `inbox` branch에 date directory가 8개가 되면 oldest routine artifact를 `inbox/archive/**`로 이동한다. Link rewrite가 별도 가치를 만들지 않으면 수행하지 않는다.
- 기존 `main:/inbox/YYYY-MM-DD/**`와 `main:/inbox/archive/**`는 legacy promoted artifact다. 새 artifact를 추가하지 않으며 별도 cleanup에서 정리한다.
- Owning workflow의 artifact가 이미 있으면 competing authority를 inbox에 만들지 않는다.
- Humans may delete inbox or archived content at their discretion.
