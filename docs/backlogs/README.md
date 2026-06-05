# Backlogs

아직 확정하지 않은 앞으로 할 일을 임시로 적는다.

## Rules

- backlog 1개는 주제 1개만 다룬다.
- 확정 설계나 이슈가 아니라 임시 메모다.
- 세부 작업은 문서 안 체크리스트로 둔다.
- 필요 없어지면 삭제한다.

## Files

| File | Description |
|---|---|
| `INDEX.csv` | index |
| `TEMPLATE.md` | template |
| `*.md` | document |

## Frontmatter

| Field | Required | Description |
|---|---|---|
| `title` | yes | title |
| `description` | yes | one-line summary |
| `tags` | no | keywords |
| `class` | yes | must be `backlog` |

## Index

- `INDEX.csv`.
- update index: `scripts/index_docs.py`
- CSV fields: `title,description`
