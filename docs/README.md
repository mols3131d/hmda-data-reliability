---
title: "Documentation"
description: "프로젝트의 장기 방향, architecture와 domain guidance, active MVP, development guides와 references를 연결하는 docs directory의 entrypoint입니다."
categories:
  - data-engineering
  - software-engineering
  - ai-engineering
tags:
  - markdown
  - openspec
---

# Documentation

`docs/`는 장기 지침, 현재 목표, 개발 가이드와 인간 편의용 projection을 구분한다. 현재 capability의 normative contract는 [`../openspec/specs/`](../openspec/specs/)가 소유한다.

## Core Documents

| Document | Role |
| --- | --- |
| [Vision](VISION.md) | 장기 방향, 제품 철학과 불변 원칙 |
| [Architecture](ARCHITECTURE.md) | 시스템 흐름과 cross-domain boundary guidance |
| [Domain Guides](domains/OVERVIEW.md) | domain별 책임·비책임과 reading path를 설명하는 guide |
| [Canonical Capability Specs](../openspec/specs/) | 현재 capability의 normative OpenSpec contract |
| [Active MVP](mvp.md) | 현재 MVP 목표, scope와 acceptance |

## Development

| Document | Role |
| --- | --- |
| [Development Guides](development/README.md) | 개발·테스트·VCS 작업의 진입점 |
| [Agent Instructions](development/agent-instructions.md) | `AGENTS.md`, Rulesync Rule, `SKILL.md`의 scope와 관리 기준 |
| [References](references) | 외부 규격과 supporting reference |

## Human Projection

[Development Dashboard](development/dashboard.md)는 사람이 개발 상태를 빠르게 보기 위한 snapshot이다. Canonical contract, current implementation 또는 validation evidence를 대신하지 않는다.

## Rules And Ownership

- `docs/**`의 작성, trust boundary, dashboard policy와 phase lifecycle은 [`AGENTS.md`](AGENTS.md)가 소유한다.
- OpenSpec의 canonical/change workflow는 [`../openspec/AGENTS.md`](../openspec/AGENTS.md)가 소유한다.

이 README는 navigation만 설명하며 owning rule을 복제하지 않는다.
