# Working

이 문서는 에이전트가 관리하는 현재 작업 기준선이다. 과거 작업 로그가 아니라 현재 구조, 검증 상태와 남은 문제만 유지한다.

## Current State

`pivot-research`는 Project Pivot 메인 agent가 직접 사용하는 Research 실행 스킬이다.

```text
pivot-research/
├── SKILL.md
└── docs/
    ├── DIRECTIVE.md
    └── WORKING.md
```

Research 산출물(Artifact)의 저장, 수명주기와 템플릿은 기존 `pivot-openspec-rpi` 자산을 재사용한다. 별도 reference, template, script는 현재 필요하지 않다.

## Current Interpretation

- 메인 agent가 질문, 범위, 조사, 종합, 상태(Status)와 artifact를 소유한다.
- `explorer`는 저장소 탐색, `web-researcher`는 외부 근거 조사에만 제한적으로 사용한다.
- 전문 보조 Agent(Specialist)의 반환값은 최종 결론이 아니라 검증할 근거 후보다.
- 간단한 조사는 chat으로, 다음 단계에 전달할 가치가 있으면 Research artifact로 남긴다.
- OpenSpec과 구현의 소유권은 침범하지 않는다.

## Arguments

현재 지원하는 argument는 다음 여섯 개다.

- `question`
- `scope`
- `exclude`
- `rigor`
- `research_id`
- `output`

기본값은 `SKILL.md` 상단 YAML 블록에서 관리한다. 새 argument는 반복되는 실제 사용 사례가 확인된 경우에만 추가한다.

## Validation

### Structure

- frontmatter에 이름, 기능, trigger와 제외 범위가 포함되어 있다.
- Arguments와 `auto` 해석이 `SKILL.md` 상단에 모여 있다.
- 핵심 실행 흐름과 경계가 한 파일에서 확인된다.
- 인간 기준선과 작업 기준선이 `docs/`로 분리되어 있다.
- 기존 RPI artifact 규칙과 템플릿을 복제하지 않는다.

### Quality

- KISS: 현재 필요한 세 파일만 사용한다.
- DRY: 저장 경로와 수명주기는 `pivot-openspec-rpi`가 계속 소유한다.
- 문맥 비용(Context Cost): artifact 생성이 필요할 때만 RPI reference와 template을 읽는다.
- 책임(Ownership): Research 책임과 specialist 역할이 분리되어 있다.
- 가독성: 어려운 핵심 용어는 한국어(영어)로 함께 표기한다.

### Improvement Loop

1. 초기 구조와 책임 경계를 검토했다.
2. 영어 중심 용어가 인간 가독성을 낮추는 문제를 확인했다.
3. 한국어(영어) 표기, 엄밀도(Rigor) 설명과 argument 사용 예를 추가했다.
4. 기존 RPI 경로와 링크가 존재하는지 다시 확인했다.

정적 구조와 파일 간 계약 검증은 통과했다.

## Remaining Validation

- 실제 OpenSpec change 준비 과정에서 한 차례 도그푸딩(Dogfooding)이 필요하다.
- `project-pivot.agent.md`가 이 스킬을 올바르게 선택하고 specialist를 제한적으로 호출하는지 실행 검증이 필요하다.

현재 차단 요소(Blocker)는 없다.
