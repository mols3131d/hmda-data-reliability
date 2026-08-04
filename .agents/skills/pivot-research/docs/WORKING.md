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

콘텐츠 책임의 기준선은 `docs/DIRECTIVE.md`의 **Content Ownership**을 따른다.

## Arguments

현재 지원하는 Argument는 여섯 개다.

- `question`
- `template`
- `scope`
- `exclude`
- `rigor`
- `output`

`template`의 기본값은 `auto`다. 템플릿 저장 경로를 직접 지정할 수도 있다.

## Current Interpretation

```text
Question
→ Template discovery
→ Template and local-instruction interpretation
→ Scope and subquestions
→ Evidence
→ Gaps
→ Synthesis
→ Output
```

- 템플릿 자동 탐색은 프로젝트 설정, 기존 Research Artifact, 예상 보고서 저장 경로와 가까운 템플릿 폴더로 제한한다.
- 템플릿 파일뿐 아니라 템플릿 폴더와 보고서 저장 폴더 주변의 로컬 지침도 확인한다.
- `<...>`, `{...}`, `{{...}}` 플레이스홀더와 주석에 포함된 작성 지침을 해석한다.
- 예시, 실제 출력 문자열과 치환할 플레이스홀더를 문맥으로 구분한다.
- 가까운 후보에서 찾지 못하면 저장소 전체를 검색하지 않고 템플릿 없이 진행한다.
- 발견된 템플릿의 필수 항목과 조사 목표에 관련된 항목을 하위 질문과 범위에 반영한다.
- 템플릿과 로컬 지침은 핵심 질문, 사용자 의도, 근거 기준과 종료 조건을 대체하지 않는다.

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
- 탐색 비용: 템플릿 탐색은 가까운 후보로 제한하고 첫 적절한 후보에서 중단한다.
- 템플릿 충족: 필수·관련 항목은 근거로 채우되 무관한 항목과 추측성 내용은 강제하지 않는다.
- Markdown: 표 안의 값 구분용 `|`는 `\|`로 이스케이프한다.

## Review History

| Loop | Main improvement |
| ---: | --- |
| 1 | 중복 출력 Argument를 제거하고 프로젝트 Artifact 계약에 위임했다. |
| 2 | 최소 충분 조사와 근거 추적성을 추가했다. |
| 3 | 완료 기준을 질문과 사용 목적 중심으로 일반화했다. |
| Refactor | 사용자 문서, 실행 지침, 상세 Reference와 개발 문서를 분리했다. |
| Template | 질문 다음으로 템플릿을 확인하고 기대 내용을 조사 범위에 반영했다. |
| Discovery | `template` Argument와 보고서 저장 경로 주변을 포함한 제한적 자동 탐색을 추가했다. |
| Interpretation | 플레이스홀더, 주석과 폴더별 로컬 지침을 템플릿 계약에 포함했다. |

## Remaining Validation

- 실제 Research 작업에서 자동 탐색이 적절한 템플릿을 낮은 비용으로 찾는지 확인해야 한다.
- 플레이스홀더와 주석을 실제 출력 문자열로 잘못 해석하지 않는지 도그푸딩(Dogfooding)이 필요하다.
- 보고서 저장 경로 주변의 로컬 지침 우선순위가 실제 프로젝트 관례와 맞는지 확인해야 한다.

정적 구조와 문서 간 책임 검증은 완료됐다. 현재 차단 요소(Blocker)는 없다.
