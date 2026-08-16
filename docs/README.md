# Documentation

Project Pivot 문서는 **durable guidance**, **active goal**, **development guide**, **human dashboard**를 구분한다. Normative capability contract는 [`../openspec/specs/`](../openspec/specs/)가 소유한다.

## Core Documents

| Document | Role |
| --- | --- |
| [Vision](vision.md) | 장기 방향과 제품 원칙 |
| [Architecture](ARCHITECTURE.md) | 시스템 흐름과 cross-domain boundary |
| [Domain Guides](domains/OVERVIEW.md) | domain별 책임·비책임과 reading path를 설명하는 human-readable guide |
| [Canonical Capability Specs](../openspec/specs/) | 현재 capability의 normative OpenSpec contract |
| [Active MVP](mvp.md) | 현재 MVP 목표, scope와 acceptance |
| [Development Dashboard](dashboard.md) | 인간 편의용 상태 snapshot; canonical evidence가 아님 |

## Directories

| Directory | Role |
| --- | --- |
| [domains](domains) | 현재 시스템의 domain 구조와 ownership을 설명하는 durable guide |
| [development](development) | phase와 무관한 개발·테스트·VCS 가이드 |
| [references](references) | 외부 규격과 supporting reference |

## Lifecycle

- Current capability의 normative contract는 `openspec/specs/**`에서 관리한다.
- `docs/ARCHITECTURE.md`와 `docs/domains/**`는 구조와 ownership을 설명하지만 OpenSpec Spec을 대체하지 않는다.
- Active phase 문서는 목표와 acceptance만 다루고 현재 구현 상태나 capability contract를 복제하지 않는다.
- Phase가 완료되면 영구 가치가 있는 architecture/domain guidance와 canonical Spec을 owning location에 반영한 뒤 phase 문서를 삭제한다.
- 완료된 phase를 보존하기 위한 `docs/archive/**`는 만들지 않는다. Git history와 Pull Request, OpenSpec archive가 history를 보존한다.
- `dashboard.md`는 별도의 dashboard refresh 작업에서만 갱신한다. Agent는 dashboard를 current state나 validation evidence의 source로 사용하지 않는다.

세부 작성·신뢰 규칙은 [`AGENTS.md`](AGENTS.md)를 따른다.
