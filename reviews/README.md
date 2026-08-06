# Reviews

`reviews/`는 repository 변경과 artifact에 대한 독립적인 검토를 위한 임시 공간이다.

구현에 한정하지 않으며 code, tests, documentation, architecture, workflow, process와 이들 사이의 일관성을 검토할 수 있다.

```text
reviews/
├── AGENTS.md
├── README.md
├── templates/
│   └── review.md
├── <target>-<review-topic>.md
├── <target>-<review-topic>-02.md
└── archive/
    └── <same-file-name>.md
```

새 Review는 [`templates/review.md`](templates/review.md)를 기준으로 작성한다.

OpenSpec의 구현 전 계획 검토는 각 Change의 `plan-review.md`에 둔다.

Review는 handoff 후 삭제한다.

장기 보관 가치가 있으면 상위 Agent가 archive를 제안하고, 인간이 명시적으로 승인한 경우에만 `archive/`로 이동한다.

Archive는 단순 보관이며 canonical decision, 현재 유효성 또는 승인 상태를 의미하지 않는다.

세부 운영 규칙은 [`AGENTS.md`](AGENTS.md)를 따른다.
