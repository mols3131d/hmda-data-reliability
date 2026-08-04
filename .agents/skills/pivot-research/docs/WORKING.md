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

Research 산출물(Artifact)의 저장 위치, 수명주기와 템플릿은 활성 프로젝트의 기존 규칙을 따른다. 별도 reference, template, script는 현재 필요하지 않다.

## Current Interpretation

- 하나의 질문과 제한된 범위를 기준으로 조사한다.
- 기존 근거를 먼저 재사용하고 부족한 부분만 확인한다.
- 간단한 조사는 chat으로, 다음 작업에 지속적으로 전달할 가치가 있으면 Research artifact로 남긴다.
- 기존 Research 템플릿이 있으면 복제하지 않고 사용한다.
- 요구사항, 설계와 구현의 소유권은 침범하지 않는다.
- 특정 workflow, schema 또는 directory를 필수 의존성으로 두지 않는다.

## Arguments

현재 지원하는 argument는 다음 여덟 개다.

- `question`
- `scope`
- `exclude`
- `rigor`
- `output`
- `research_id`
- `artifact_path`
- `template`

기본값은 `SKILL.md` 상단 YAML 블록에서 관리한다. 새 argument는 반복되는 실제 사용 사례가 확인된 경우에만 추가한다.

## Validation

### Structure

- frontmatter에 기능, 사용 조건과 제외 범위가 포함되어 있다.
- Arguments와 `auto` 해석이 `SKILL.md` 상단에 모여 있다.
- 핵심 실행 흐름과 경계가 한 파일에서 확인된다.
- 인간 기준선과 현재 작업 기준선이 `docs/`로 분리되어 있다.
- 기존 Research 템플릿과 프로젝트 artifact 규칙을 복제하지 않는다.

### Quality

- KISS: 현재 필요한 세 파일만 사용한다.
- DRY: 프로젝트별 저장 위치와 템플릿은 해당 프로젝트가 계속 소유한다.
- 이식성(Portability): 특정 workflow, schema 또는 directory가 없어도 Chat Research를 수행할 수 있다.
- 호환성(Compatibility): 기존 템플릿과 artifact 규칙을 발견하면 그대로 따른다.
- 가독성: 어려운 핵심 용어는 한국어(영어)로 함께 표기한다.

### Improvement Loop

1. 초기 구조와 Research 경계를 검토했다.
2. 특정 RPI 경로와 내부 자산에 대한 결합도(Coupling)를 제거했다.
3. 템플릿과 저장 위치를 argument 및 프로젝트 규칙으로 해석하도록 수정했다.
4. Research 절차, 근거 분류, 완료 기준과 출력 계약만 남겼다.

정적 구조와 문서 간 계약 검증은 통과했다.

## Remaining Validation

- 실제 Research 작업에서 `template: auto`와 `artifact_path: auto`의 탐색 결과를 확인해야 한다.
- `lite`, `standard`, `strict`가 실제 조사 비용과 위험에 맞게 선택되는지 도그푸딩(Dogfooding)이 필요하다.

현재 차단 요소(Blocker)는 없다.
