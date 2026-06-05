# Architecture Decision Records

중요한 아키텍처 결정만 기록한다. 구현 TODO는 backlog나 코드에 둔다.

## Rules

- ADR 1개는 결정 1개만 다룬다.
- 장기 영향이 있는 기술 선택, 운영 정책, 책임 경계만 기록한다.
- 선택 이유와 트레이드오프를 같이 적는다.
- `deprecated`, `superseded`, `rejected` 상태는 archive 대상이다.

## Files

| File | Description |
|---|---|
| `INDEX.csv` | active ADR index |
| `archive/INDEX.csv` | archived ADR index |
| `TEMPLATE.md` | ADR template |
| `adr-*.md` | ADR document |

## Frontmatter

| Field | Required | Description |
|---|---|---|
| `id` | yes | ADR number |
| `title` | yes | ADR title |
| `status` | yes | lifecycle status |
| `date` | yes | decision date |
| `description` | yes | one-line summary |
| `tags` | no | keywords |
| `class` | yes | must be `adr` |
| `related-files` | no | related document paths |

## Status

| Status | Archived | Description |
|---|---|---|
| `proposed` | no | under review |
| `accepted` | no | chosen, not fully implemented |
| `implemented` | no | implemented and current |
| `deprecated` | yes | no longer recommended |
| `superseded` | yes | replaced by another ADR |
| `rejected` | yes | reviewed but not chosen |

## Index & Archive

- `INDEX.csv`
- `archive/`
- Archive and update index : `scripts/index_docs.py`
