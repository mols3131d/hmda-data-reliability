# Research

`research/`는 계획과 의사결정을 위한 임시 조사 공간이다.

```text
research/
├── AGENTS.md
├── README.md
├── <domain>-<topic>.md
├── <domain>-<subdomain>-<topic>.md
├── <domain>-<subdomain>-<topic>-02.md
└── archive/
    └── <same-file-name>.md
```

새 Research는 [`inbox/templates/research.md`](../inbox/templates/research.md)를 기준으로 작성한다.

Research는 사용 후 삭제한다.

장기 보관 가치가 있으면 상위 Agent가 archive를 제안하고, 인간이 명시적으로 승인한 경우에만 `archive/`로 이동한다.

Archive는 단순 보관이며 공식 결정이나 현재 유효성을 의미하지 않는다.

세부 운영 규칙은 [`AGENTS.md`](AGENTS.md)를 따른다.
