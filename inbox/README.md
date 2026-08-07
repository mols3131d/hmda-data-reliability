# Inbox

채팅과 탐색 과정에서 생성된 비정규 artifact를 임시로 보관한다.

`inbox/`의 내용은 공식 문서나 프로젝트 지침이 아니다. 가치가 확인된 내용은 적절한 canonical 위치로 재작성하고, 불필요한 내용은 삭제한다.

```text
inbox/
├── AGENTS.md
├── README.md
├── _guidelines/
│   ├── branch.md
│   ├── research.md
│   └── review.md
├── _templates/
│   ├── research.md
│   └── review.md
└── YYYY-MM-DD/
    └── HH-MM-<type>-<domain>-...-<short-title>
```

`AGENTS.md`를 진입점으로 사용하고, 현재 작업에 필요한 guideline, template, skill만 선택적으로 읽는다.

`_guidelines/`와 `_templates/`는 `inbox/` 운영을 위한 내부 자산이다.

모든 inbox artifact는 파일 이름과 frontmatter에 같은 `type`을 사용한다. `research`와 `review`는 자주 쓰이는 type일 뿐 제한된 목록이 아니며, 적절한 type이 없으면 긴 문서는 `report`, 짧은 문서는 `brief`를 사용한다.
