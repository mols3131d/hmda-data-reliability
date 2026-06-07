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

| Field | Type | Required | Description |
|---|---|---|---|
| `title` | `string` | yes | title |
| `description` | `string` | yes | one-line summary |
| `tags` | `list of strings` | no | keywords |
| `class` | `string` | yes | must be `backlog` |

## Index

- `INDEX.csv`.
- update index: `scripts/index_docs.py`
- CSV fields: `title,description`

## LifeCycle

1. **Copy Template**: `TEMPLATE.md`를 복사하여 새로운 `*.md` 파일 생성.
2. **Draft**: 필수 Frontmatter 및 Todo 목록 작성.
3. **Review & Edit & Decide**: 백로그 요구사항 검토 및 수정, 최종 구현 여부와 우선순위 결정.
4. **To OpenSpec**: 구현 확정 시 `openspec/` 스펙 문서 대상으로 이관.
5. **Archive**: 스펙 이관 후 파일을 아카이브 폴더로 이동.
6. **Delete**: 완료되거나 불필요해진 파일 삭제 후 인덱싱 동기화.
