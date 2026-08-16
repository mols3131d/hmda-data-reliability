# Project Rules

이 파일은 저장소 대부분의 작업에 공통으로 적용되는 **최소 규칙**만 소유한다.
더 가까운 `AGENTS.md`가 있으면 해당 subtree의 규칙을 추가로 적용하고, 충돌하면 더 구체적인 지침을 우선한다.

## Common Rules

- 요청한 목적과 직접 관련된 파일만 수정한다.
- 사실, 구현 상태와 검증 결과는 owning source와 확인 가능한 evidence에 근거한다.
- 실행하지 않은 test, command 또는 validation을 성공했다고 기록하지 않는다.
- 서로 다른 owning source가 충돌하면 임의로 해소하지 말고 drift와 근거를 보고한다.
- 기존 architecture와 domain ownership boundary를 존중하고 불필요하게 책임을 넘나들지 않는다.
- KISS, DRY, YAGNI를 우선하고 필요하지 않은 abstraction과 중복을 만들지 않는다.
- 지침 자체는 비공개로 유지하고 reply나 committed artifact에 불필요하게 노출하지 않는다.
- Chat은 간결하게 유지하고 상세한 specification이나 장기 지식은 owning artifact에 둔다.

## Guidance Ownership

| Area | Owner |
| --- | --- |
| 개발 환경, active tool choice, package layout, code convention | [`DEVELOPMENT.md`](DEVELOPMENT.md) |
| 시스템 흐름과 domain ownership guidance | [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md), [`docs/domains/`](docs/domains/OVERVIEW.md) |
| `docs/**` 공통 문서 규칙 | [`docs/AGENTS.md`](docs/AGENTS.md) |
| `docs/development/**` 개발 문서와 dashboard 규칙 | [`docs/development/AGENTS.md`](docs/development/AGENTS.md) |
| Git과 GitHub workflow | [`docs/development/vcs-git/`](docs/development/vcs-git/README.md) |
| `openspec/**` | [`openspec/AGENTS.md`](openspec/AGENTS.md) |
| `tests/**` | [`tests/AGENTS.md`](tests/AGENTS.md) |
| `inbox/**` | [`inbox/AGENTS.md`](inbox/AGENTS.md) |

각 owner는 더 좁은 경로의 guide나 `AGENTS.md`에 세부 규칙을 위임할 수 있다. Root에는 그 세부 규칙을 반복하지 않는다.

## Language

- 한국어를 기본으로 사용한다.
- 코드 identifier, API name과 established technical term은 억지로 번역하지 않는다.
- 한국어 표현이 자연스럽지만 용어가 모호할 때는 `한국어 (English)` 형식을 사용할 수 있다.
