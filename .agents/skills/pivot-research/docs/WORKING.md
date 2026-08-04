# Working

이 문서는 현재 작업 기준선이다. 과거 작업 로그가 아니라 현재 구조, 검증 상태와 남은 문제만 유지한다.

## Current State

`pivot-research`는 명세, 구현 또는 기술 판단 전에 근거를 수집하고 정리하는 Research 실행 스킬이다.

```text
pivot-research/
├── SKILL.md
└── docs/
    ├── DIRECTIVE.md
    └── WORKING.md
```

Research 산출물(Artifact)의 저장 위치, 수명주기와 템플릿은 프로젝트의 기존 규칙을 따른다. 별도 reference, template, script는 없다.

## Arguments

현재 지원하는 argument는 다음 다섯 개다.

- `question`
- `scope`
- `exclude`
- `rigor`
- `output`

출력 경로, Research ID와 템플릿은 별도 argument로 제어하지 않는다. 프로젝트의 기존 artifact 계약과 템플릿이 해당 내용을 소유한다.

## Current Interpretation

- 하나의 핵심 목표와 필요한 하위 질문을 기준으로 조사한다.
- 기존 근거를 먼저 재사용하고 부족한 부분만 확인한다.
- 기존 Research 템플릿과 artifact 계약을 복제하지 않는다.
- 특정 workflow, schema 또는 directory를 필수 의존성으로 두지 않는다.
- 요구사항, 설계와 구현을 Research 결과로 확정하지 않는다.

## Validation

### Structure

- Arguments와 `auto` 해석이 `SKILL.md` 상단에 모여 있다.
- 핵심 흐름과 경계가 한 파일에서 확인된다.
- 인간 기준선과 현재 작업 기준선이 `docs/`로 분리되어 있다.
- 템플릿, 저장 경로와 상태 규칙을 중복 정의하지 않는다.

### Quality

- KISS: 세 파일만 사용한다.
- DRY: 프로젝트별 템플릿과 artifact 계약은 프로젝트가 소유한다.
- 이식성(Portability): 특정 workflow, schema 또는 directory가 없어도 Chat Research가 가능하다.
- 가독성: 핵심 용어는 한국어(영어)로 함께 표기한다.

## Review Loops

### Loop 1

- 일반 리뷰: 출력 관련 argument가 겹치고 `DIRECTIVE.md`의 규칙이 반복됨을 확인했다.
- 적대적 리뷰: 고정 경로를 제거하면서 오히려 `artifact_path`, `template`, `research_id`라는 새 설정 부담을 만든 점을 지적했다.
- 종합 검토: 프로젝트의 기존 템플릿과 artifact 계약이 해당 값을 소유하는 편이 더 단순하고 이식 가능하다고 판단했다.
- 작업: argument를 다섯 개로 줄이고, 핵심 질문에 필요한 하위 질문을 허용하며, 반복 규칙을 축약했다.

## Remaining Validation

- 2회차에서 과도한 절차와 모호한 `auto` 규칙을 검토한다.
- 3회차에서 실제 이식 실패 상황과 결과 품질 저하 가능성을 검토한다.

현재 차단 요소(Blocker)는 없다.
