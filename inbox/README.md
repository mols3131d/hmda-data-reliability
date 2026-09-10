# Inbox

`inbox/`는 보고서, 조사, 리뷰, 작업 상태, checkpoint, handoff처럼 **non-canonical working artifact**를 두는 공간이다.

PR이 없는 change branch의 작업은 `inbox/<branch-created-date>-<branch-name-slug>/` 아래에 묶는다. Pull Request가 생성되면 같은 work unit directory를 `inbox/github-<pr-number>-<short-name>/`으로 rename한다. GitHub Issue에 직접 속하지만 change branch가 소유하지 않는 작업도 `inbox/github-<issue-number>-<short-name>/`을 사용할 수 있다. 그 밖의 작업은 `inbox/YYYY-MM-DD/` 아래에 둔다.

```text
inbox/2026-09-09-agent-docs-inbox-github-work-directories/
  00-plan-inbox-directory-policy.md
  01-review-inbox-directory-policy.md
  02-follow-up/

# PR #230 생성 후 동일 work unit
inbox/github-230-inbox-github-work-directories/
```

Branch와 GitHub work unit의 top-level file과 bundle은 같은 sequence를 공유하며, 새 항목은 현재 가장 큰 번호 다음에 추가한다. PR 전환에서는 기존 artifact와 sequence를 그대로 보존한다.

세부 naming, frontmatter, validation, lifecycle contract는 [`AGENTS.md`](AGENTS.md)가 소유한다. 내용은 필요할 때 직접 찾고 확인하며, 이 README는 artifact index나 project status projection으로 유지하지 않는다.
