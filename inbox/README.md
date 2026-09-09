# Inbox

`inbox/`는 보고서, 조사, 리뷰, 작업 상태, checkpoint, handoff처럼 **non-canonical working artifact**를 두는 공간이다.

GitHub Issue나 Pull Request와 직접 연결된 작업은 `inbox/github-<number>-<short-name>/` 아래에 묶는다. 그 밖의 작업은 `inbox/YYYY-MM-DD/` 아래에 둔다.

```text
inbox/github-230-inbox-github-work-directories/
  00-plan-inbox-directory-policy.md
  01-review-inbox-directory-policy.md
  02-follow-up/
```

GitHub work unit 안의 top-level file과 bundle은 같은 sequence를 공유하며, 새 항목은 현재 가장 큰 번호 다음에 추가한다.

세부 naming, frontmatter, validation, lifecycle contract는 [`AGENTS.md`](AGENTS.md)가 소유한다. 내용은 필요할 때 직접 찾고 확인하며, 이 README는 artifact index나 project status projection으로 유지하지 않는다.
