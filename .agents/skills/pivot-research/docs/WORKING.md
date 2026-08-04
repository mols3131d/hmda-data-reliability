# Working

이 문서는 에이전트가 관리하는 현재 작업 기준선이다. 과거 작업 로그가 아니라 현재 구조, 검증 상태와 남은 문제만 유지한다.

## Current State

`pivot-research`는 호출한 메인 Agent가 직접 사용하는 Research 실행 스킬이다.

```text
pivot-research/
├── SKILL.md
└── docs/
    ├── DIRECTIVE.md
    └── WORKING.md
```

스킬 내부에는 별도 template, reference 또는 script를 두지 않는다. 프로젝트에 이미 있는 Research 템플릿과 artifact 규칙은 필요할 때만 선택적으로 사용한다.

## Dependency Model

### Required

저장소 내부의 특정 Agent, Skill, workflow, schema 또는 directory에 대한 필수 의존성은 없다.

### Optional

| Integration | Fallback |
| --- | --- |
| 읽기 전용 저장소 탐색 Specialist | 메인 Agent가 직접 탐색한다. |
| 외부 자료 조사 Specialist | 메인 Agent가 직접 조사한다. |
| 프로젝트 Research 템플릿 | Chat으로 보고하거나, artifact가 필수면 해결 조건과 함께 `blocked`로 보고한다. |
| 프로젝트 artifact 설정 | 기존 artifact와 관례를 탐색한다. 하나로 결정할 수 없으면 임의 생성하지 않는다. |

Specialist는 고정된 이름이 아니라 필요한 능력(Capability)으로 선택한다.

## Current Interpretation

- 메인 Agent가 질문, 범위, 조사, 종합, 상태와 결과를 소유한다.
- Specialist의 반환값은 최종 결론이 아니라 검증할 근거 후보다.
- 간단한 조사는 Chat으로, 다음 단계에 지속적인 전달이 필요하면 artifact로 남긴다.
- 기존 프로젝트 템플릿은 재사용하지만 이 스킬에 복제하지 않는다.
- 특정 OpenSpec 구조가 없어도 Research 자체는 동작한다.
- 요구사항, 설계와 구현의 소유권은 침범하지 않는다.

## Arguments

```yaml
question: auto
scope: auto
exclude: []
rigor: auto
output: auto
research_id: auto
artifact_path: auto
template: auto
```

기본값과 `auto` 해석은 `SKILL.md`의 Arguments 섹션에서 관리한다. 새 argument는 반복되는 실제 사용 사례가 확인된 경우에만 추가한다.

## Validation

### Structure

- Front matter에 기능, 사용 조건과 제외 범위가 포함되어 있다.
- Arguments와 기본값이 `SKILL.md` 상단에 모여 있다.
- 핵심 실행 흐름, 호환성 규칙과 경계를 한 파일에서 확인할 수 있다.
- 인간 기준선과 작업 기준선이 `docs/`로 분리되어 있다.
- 기존 Research 템플릿을 복제하지 않는다.

### Portability

- 특정 Specialist 이름을 직접 요구하지 않는다.
- 특정 Skill 또는 reference 경로를 링크하지 않는다.
- 특정 OpenSpec schema와 artifact directory를 강제하지 않는다.
- 선택적 통합이 없어도 Chat Research는 계속 수행할 수 있다.
- Artifact가 필요하지만 프로젝트 계약을 찾을 수 없으면 임의 형식을 만들지 않는다.

### Quality

- KISS: 현재 필요한 세 파일만 유지한다.
- DRY: 기존 프로젝트 템플릿과 artifact 규칙을 그대로 사용한다.
- 문맥 비용(Context Cost): 현재 조사에 필요한 자산만 읽는다.
- 책임(Ownership): Research 책임과 선택적 Specialist의 역할이 분리되어 있다.
- 가독성: 어려운 핵심 용어는 한국어(영어)로 함께 표기한다.

### Improvement Loop

1. 기존 스킬의 내부 의존성을 검토했다.
2. `pivot-openspec-rpi` 경로와 고정 Agent 이름이 이식성을 낮추는 문제를 확인했다.
3. 고정 경로와 이름을 제거하고 능력 기반 선택과 fallback을 추가했다.
4. 템플릿은 새로 만들지 않고 프로젝트의 기존 템플릿을 재사용하도록 유지했다.
5. Artifact 경로와 schema의 소유권을 활성 프로젝트로 돌렸다.

정적 구조와 의존성 검토는 통과했다.

## Remaining Validation

- 현재 Project Pivot의 기존 Research 템플릿을 `template: auto`로 올바르게 발견하는지 도그푸딩(Dogfooding)이 필요하다.
- Specialist가 있는 환경과 없는 환경에서 같은 핵심 결론을 만드는지 실행 검증이 필요하다.
- `project-pivot.agent.md`가 이 스킬을 선택하되 Research 책임을 계속 직접 소유하는지 확인해야 한다.

현재 차단 요소(Blocker)는 없다.
