# Working

이 문서는 현재 작업 기준선이다. 과거 작업 로그가 아니라 현재 구조, 검증 상태와 남은 문제만 유지한다.

## Current State

`pivot-research`는 명세, 구현 또는 기술 판단 전에 근거를 수집하고 정리하는 Research 스킬이다.

```text
pivot-research/
├── README.md
├── SKILL.md
├── docs/
│   ├── DIRECTIVE.md
│   └── WORKING.md
└── references/
    ├── evidence.md
    ├── output.md
    └── workflow.md
```

프로젝트별 Research 템플릿, 저장 위치, 수명주기와 상태 규칙은 복제하지 않는다.

## Content Ownership

| Location | Current content |
| --- | --- |
| `README.md` | 사용자용 개요, Arguments, 예시와 출력 설명 |
| `SKILL.md` | Arguments, 5단계 핵심 흐름, 참조 선택, 완료와 경계 |
| `references/workflow.md` | 상세 조사 흐름, 엄밀도와 종료 기준 |
| `references/evidence.md` | 근거 분류, 품질, 충돌과 추적성 |
| `references/output.md` | 완료 상태, Chat·Artifact와 이식성 |
| `docs/DIRECTIVE.md` | 목적, 요구사항, 불변 조건과 설계 결정 |
| `docs/WORKING.md` | 현재 구조, 검증 결과와 남은 작업 |

## Arguments

현재 지원하는 Argument는 다섯 개다.

- `question`
- `scope`
- `exclude`
- `rigor`
- `output`

출력 경로, Research ID와 템플릿은 프로젝트의 기존 Artifact 계약이 소유한다.

## Validation

### Structure

- `SKILL.md`에서 사용자 설명과 상세 실행 규칙을 분리했다.
- 각 Reference는 하나의 판단 영역만 소유한다.
- `README.md`, `SKILL.md`, `references/`, `docs/`의 책임이 겹치지 않는다.
- 프로젝트 템플릿, 저장 경로, front matter와 상태 규칙을 중복 정의하지 않는다.

### Quality

- KISS: 실행 진입 문서는 짧고 단일 흐름으로 읽힌다.
- DRY: 상세 규칙은 하나의 Reference에서만 관리한다.
- 점진적 공개(Progressive Disclosure): 현재 판단에 필요한 Reference만 읽는다.
- 이식성(Portability): 특정 workflow, schema 또는 directory 없이 Chat Research가 가능하다.
- 추적성(Traceability): 중요한 결론은 재확인 가능한 근거 위치와 연결한다.
- 조사 비용: 답이나 불확실성을 바꾸지 않는 추가 조사는 중단한다.

## Review History

| Loop | Main improvement |
| ---: | --- |
| 1 | 중복 출력 Argument를 제거하고 프로젝트 Artifact 계약에 위임했다. |
| 2 | 최소 충분 조사와 근거 추적성을 추가했다. |
| 3 | 완료 기준을 질문과 사용 목적 중심으로 일반화했다. |
| Refactor | 사용자 문서, 실행 지침, 상세 Reference와 개발 문서를 분리했다. |

## Remaining Validation

- 실제 Research 작업으로 Reference 선택이 과도하거나 부족하지 않은지 확인해야 한다.
- `output: auto`와 엄밀도 자동 선택을 도그푸딩(Dogfooding)해야 한다.
- 프로젝트의 기존 템플릿과 Artifact 계약을 올바르게 발견하는지 실행 검증이 필요하다.

정적 구조와 문서 간 책임 검증은 완료됐다. 현재 차단 요소(Blocker)는 없다.
