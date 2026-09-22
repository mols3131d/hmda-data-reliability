# Inbox

`inbox/`는 보고서, 조사, 리뷰, 작업 상태, checkpoint, handoff처럼 **non-canonical working artifact**를 두는 공간이다.

## Choose A Container

Artifact는 실제 owning work unit을 기준으로 **GitHub → Branch → Date** 순서로 둔다.

- GitHub Pull Request 또는 Issue가 소유하면 `inbox/github-<number>-<short-name>/`
- GitHub work unit이 없고 change branch가 소유하면 `inbox/<branch-created-date>-<branch-name-slug>/`
- 둘 다 아니면 `inbox/YYYY-MM-DD/`

각 container root에는 필요할 때 overview, navigation 또는 artifact index용 `README.md`를 둘 수 있다. 이 README는 working artifact가 아니므로 artifact naming과 frontmatter 규칙을 적용하지 않는다.

Directory ownership, branch→PR 전환, sequence, naming, frontmatter, validation과 lifecycle의 상세 contract는 [`AGENTS.md`](AGENTS.md)가 소유한다.
