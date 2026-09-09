# Inbox

`inbox/`는 보고서, 조사, 리뷰, 작업 상태, checkpoint, handoff처럼 **non-canonical working artifact**를 두는 공간이다.

GitHub Issue나 Pull Request와 직접 연결된 작업은 하나의 디렉터리로 묶는다.

```text
inbox/github-230-inbox-github-work-directories/
  00-plan-inbox-directory-policy.md
  01-review-inbox-directory-policy.md
  02-follow-up/
```

같은 디렉터리 안에서는 file과 bundle을 함께 순서대로 두고, 새 항목은 가장 큰 번호 다음으로 이어 쓴다. GitHub work unit에 속하지 않는 작업은 기존처럼 `inbox/YYYY-MM-DD/` 아래에 둔다.

내용은 필요할 때 직접 찾고 확인한다. 이 README는 artifact index나 project status projection으로 갱신하지 않는다.

세부 naming, frontmatter, validation과 lifecycle 규칙은 [`AGENTS.md`](AGENTS.md)를 따른다. 일반 Git/Pull Request workflow는 [`docs/development/vcs-git/`](../docs/development/vcs-git/README.md)를 따른다.
