# Inbox

`inbox/`는 보고서, 조사, 리뷰, 작업 상태, checkpoint, handoff처럼 **non-canonical working artifact**를 두는 공간이다.

Directory는 현재 artifact의 owning work unit을 기준으로 **GitHub → Branch → Date** 순서로 선택한다.

```text
# GitHub PR 또는 Issue가 소유
inbox/github-230-inbox-github-work-directories/

# PR 없는 change branch가 소유
inbox/2026-09-09-agent-docs-inbox-github-work-directories/

# 둘 다 아님
inbox/2026-09-09/
```

GitHub와 Branch work unit의 top-level file과 bundle은 같은 `NN` sequence를 공유한다. Branch가 Pull Request를 얻으면 기존 branch directory를 `github-<pr-number>-<short-name>`으로 rename하고 artifact와 sequence를 그대로 보존한다.

세부 directory selection, branch date, naming, frontmatter, validation과 lifecycle contract는 [`AGENTS.md`](AGENTS.md)가 소유한다. 내용은 필요할 때 직접 찾고 확인하며, 이 README는 artifact index나 project status projection으로 유지하지 않는다.
