# Reviews

`reviews/`는 repository 변경과 artifact에 대한 독립적인 검토 기록을 저장한다.

구현에 한정하지 않으며 코드, 테스트, 문서, architecture, workflow와 process를 검토할 수 있다.

```text
reviews/
├── AGENTS.md
├── README.md
├── <target>-<review-topic>.md
└── <target>-<review-topic>-02.md
```

OpenSpec의 구현 전 계획 검토는 각 Change의 `plan-review.md`에 둔다.

Review의 결론은 대상 artifact에 반영한다. Review 자체는 요구사항, 설계 또는 구현의 canonical source가 아니다.

세부 운영 규칙은 [`AGENTS.md`](AGENTS.md)를 따른다.
