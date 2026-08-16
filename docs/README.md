# Documentation

Project Pivot 문서는 **durable guidance**, **active goal**, **development guide**, **human dashboard**를 구분한다. Normative capability contract는 [`../openspec/specs/`](../openspec/specs/)가 소유한다.

## Core Documents

| Document | Role |
| --- | --- |
| [Vision](vision.md) | 장기 방향과 제품 원칙 |
| [Architecture](ARCHITECTURE.md) | 시스템 흐름과 cross-domain boundary guidance |
| [Domain Guides](domains/OVERVIEW.md) | domain별 책임·비책임과 reading path를 설명하는 human-readable guide |
| [Canonical Capability Specs](../openspec/specs/) | 현재 capability의 normative OpenSpec contract |
| [Active MVP](mvp.md) | 현재 MVP 목표, scope와 acceptance |
| [Development Dashboard](development/dashboard.md) | 인간 편의용 개발 상태 snapshot; canonical evidence가 아님 |

## Directories

| Directory | Role |
| --- | --- |
| [domains](domains) | 현재 시스템의 domain 구조와 ownership을 설명하는 durable guide |
| [development](development) | 개발·테스트·VCS 가이드와 human-only development dashboard |
| [references](references) | 외부 규격과 supporting reference |

## Rules And Ownership

- `docs/**`의 작성, trust boundary, dashboard policy와 phase lifecycle은 [`AGENTS.md`](AGENTS.md)가 소유한다.
- OpenSpec의 canonical/change workflow는 [`../openspec/AGENTS.md`](../openspec/AGENTS.md)가 소유한다.

이 README는 문서 navigation을 설명하며 위 규칙을 복제하지 않는다.
