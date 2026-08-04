# Directive

이 문서는 인간 주도의 규범적 기준선이다. 사용자의 명시적 요청 없이 수정하지 않는다.

## Purpose

호출한 메인 Agent가 Research를 직접 수행하여 현재 상태, 불확실성, 영향 범위와 검증 가능한 근거를 확보하도록 한다.

Research는 다음 명세, 구현 또는 기술 판단을 지원하지만 최종 요구사항·설계·구현을 대신 소유하지 않는다.

## Requirements

| ID | Requirement |
| --- | --- |
| R-01 | 메인 Agent가 Research 질문, 종합, 상태와 결과를 소유해야 한다. |
| R-02 | 기존 근거를 먼저 재사용하고 부족한 부분만 조사해야 한다. |
| R-03 | 권위 근거, 관찰 근거, 보조 근거와 가정을 구분해야 한다. |
| R-04 | 전문 보조 Agent는 이름이 아니라 필요한 능력(Capability)을 기준으로 선택해야 한다. |
| R-05 | 전문 보조 Agent가 없어도 메인 Agent가 Research를 계속 수행할 수 있어야 한다. |
| R-06 | 프로젝트에 기존 Research 템플릿이 있으면 복제하지 않고 재사용해야 한다. |
| R-07 | 저장 위치, front matter, 상태와 보관 규칙은 활성 프로젝트의 계약을 따라야 한다. |
| R-08 | 특정 workflow, schema, directory 또는 Agent 이름을 필수 의존성으로 만들지 않아야 한다. |
| R-09 | Arguments와 자동 해석 규칙이 `SKILL.md` 상단에서 쉽게 확인되어야 한다. |
| R-10 | 인간이 직접 읽고 수정할 수 있도록 구조와 용어를 단순하게 유지해야 한다. |

## Invariants

| ID | Invariant |
| --- | --- |
| I-01 | Research 단계의 최종 책임은 호출한 메인 Agent에 있다. |
| I-02 | 전문 보조 Agent는 단계 소유자가 아니라 선택적 Specialist 또는 도구다. |
| I-03 | 내부 Agent·Skill·template 경로가 없어도 Chat Research는 동작해야 한다. |
| I-04 | 강한 기존 근거가 있으면 같은 사실을 반복 조사하지 않는다. |
| I-05 | 비공개 추론이나 chat transcript를 지속 가능한 근거로 저장하지 않는다. |
| I-06 | Research는 외부 workflow의 schema, lifecycle, command 또는 gate를 변경하지 않는다. |
| I-07 | 기존 템플릿을 이 스킬 내부에 복제하지 않는다. |
| I-08 | Artifact 형식이나 경로를 근거 없이 새로 만들지 않는다. |
| I-09 | 불필요한 reference, script, template 또는 argument를 추가하지 않는다. |

## Allowed Scope

| Area | Allowed |
| --- | --- |
| Repository | 관련 문서, 코드, 설정, 테스트, 실행 결과와 history 조사 |
| External | 현재 환경에 적용 가능한 공식 문서와 1차 자료 조사 |
| Delegation | 사용할 수 있는 Specialist에 하나의 제한된 근거 질문 위임 |
| Execution | 안전한 읽기 전용(Read-only) 재현과 검증 |
| Artifact | 활성 프로젝트의 기존 규칙과 템플릿에 따른 결과 생성·갱신 |

## Boundaries

| Boundary | Rule |
| --- | --- |
| Decision ownership | 요구사항, 설계와 구현 계획을 Research가 확정하지 않는다. |
| Implementation | 코드·테스트·설정을 구현 목적으로 변경하지 않는다. |
| Scope | 인접 개선을 현재 조사에 자동 포함하지 않는다. |
| Evidence | 근거 위치 또는 관찰 결과가 없는 주장을 사실로 기록하지 않는다. |
| Human choice | 제품 동작, 아키텍처, 비용이나 위험이 실질적으로 달라지는 선택은 사용자에게 돌린다. |
| Portability | 특정 프로젝트 자산이 없다는 이유만으로 전체 Research를 실패시키지 않는다. |

## Adopted Decisions

| Decision | Rationale |
| --- | --- |
| 메인 Agent가 Research를 직접 수행한다. | 사용자의 코파일럿이 전체 맥락과 최종 판단을 유지해야 한다. |
| Specialist는 능력 기반으로 선택한다. | Agent 이름 변경과 다른 프로젝트 이식에 견딜 수 있다. |
| 내부 필수 의존성을 두지 않는다. | 다른 workflow나 자산 변경이 Research 자체를 깨뜨리지 않는다. |
| 기존 프로젝트 템플릿만 선택적으로 사용한다. | 중복을 피하면서 프로젝트별 출력 형식을 존중한다. |
| Artifact 경로와 schema를 프로젝트가 소유한다. | 스킬이 특정 OpenSpec 또는 directory 구조에 묶이지 않는다. |
| Arguments를 `SKILL.md` 상단에 둔다. | 사용자가 편집기에서 동작을 빠르게 이해하고 조정할 수 있다. |
| 별도 script와 reference를 만들지 않는다. | 현재 동작은 명확한 지침만으로 충분하며 구조를 가볍게 유지할 수 있다. |
