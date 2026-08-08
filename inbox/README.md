# Inbox

채팅과 탐색 과정에서 생성된 비정규 artifact를 보관한다.

날짜 디렉터리와 `archive/`의 artifact는 branch와 관계없이 canonical project context가 아니다. Routine artifact는 전용 `inbox` branch에서 생성하고, 현재 또는 후속 작업에 계속 유용한 artifact는 일반 Pull Request를 통해 `main:/inbox/**`에 선택적으로 유지할 수 있다.

| Location | Role |
| --- | --- |
| `inbox` branch | artifact 생성·검토·숙성 공간 |
| `main:/inbox/**` | 작업에 유지할 가치가 확인된 non-canonical 근거 |
| owning artifact | canonical contract와 최종 결정 |

```text
inbox/
├── AGENTS.md
├── README.md
├── _guidelines/
│   ├── research.md
│   └── review.md
├── _templates/
│   ├── research.md
│   └── review.md
└── YYYY-MM-DD/
    └── HH-MM-<type>-<domain>-...-<short-title>
```

`AGENTS.md`를 진입점으로 사용하고, 현재 작업에 필요한 guideline, template, skill만 선택적으로 읽는다.

`AGENTS.md`, `_guidelines/`, `_templates/`는 `inbox/` 운영을 위한 내부 자산이다.

전용 `inbox` branch의 direct push, `main` 동기화와 artifact 승격은 [`docs/development/vcs-git/branch.md`](../docs/development/vcs-git/branch.md#inbox-branch)를 따른다.

모든 inbox artifact는 파일 이름과 frontmatter에 같은 `type`을 사용한다. `research`와 `review`는 자주 쓰이는 type일 뿐 제한된 목록이 아니며, 적절한 type이 없으면 긴 문서는 `report`, 짧은 문서는 `brief`를 사용한다.

Promoted artifact도 non-canonical이다. Canonical contract나 결정으로 채택된 내용은 해당 owning artifact에 자족적으로 반영한다.
