# Inbox

채팅, 조사, 검토와 의사결정 지원 과정에서 생성되는 비정규 artifact의 임시 workspace다.

```text
inbox/
├── AGENTS.md
├── README.md
├── guidelines/
│   ├── research.md
│   └── review.md
├── YYYY-MM-DD/
│   └── HH-MM-<name>.md
└── archive/
```

`AGENTS.md`가 agent의 진입점이며, `guidelines/`는 필요한 유형만 선택적으로 읽는 reference다.

`research`와 `review`는 자주 쓰이는 유형일 뿐 허용 목록이 아니다. 문서의 성격과 목적이 명확하면 그 목적에 맞는 type을 사용한다. 더 명확한 type이 없으면 긴 문서는 `report`, 짧은 문서는 `briefing`으로 기록한다.

`inbox/`는 canonical source가 아니다. 가치가 확인된 내용은 적절한 소유 artifact로 재작성하고, 불필요한 내용은 삭제한다.
