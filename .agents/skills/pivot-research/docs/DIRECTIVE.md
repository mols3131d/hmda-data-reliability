# Directive

이 문서는 인간 주도의 규범적 기준선이다. 사용자의 명시적 요청 없이 수정하지 않는다.

## Purpose

Project Pivot의 메인 agent가 Research를 직접 수행하여 현재 상태, 불확실성, 영향 범위와 검증 가능한 근거를 확보하도록 한다.

Research는 다음 OpenSpec 또는 구현 판단을 지원하지만, 최종 요구사항·설계·구현을 대신 소유하지 않는다.

## Requirements

| ID | Requirement |
| --- | --- |
| R-01 | 메인 agent가 Research 질문, 종합, status와 artifact를 소유해야 한다. |
| R-02 | 기존 repository 근거를 먼저 재사용하고 부족한 부분만 조사해야 한다. |
| R-03 | 사실, 관찰, 보조 근거와 가정을 구분해야 한다. |
| R-04 | 코드베이스 및 웹 specialist는 제한된 근거 질문에만 사용할 수 있어야 한다. |
| R-05 | OpenSpec이 목표, 범위, 영향과 검증을 정의할 수 있는지로 완료를 판단해야 한다. |
| R-06 | RPI Research artifact가 필요하면 기존 `pivot-openspec-rpi` 계약을 따라야 한다. |
| R-07 | Arguments와 자동 해석 규칙이 문서 상단에서 쉽게 확인되어야 한다. |
| R-08 | 인간이 직접 읽고 수정할 수 있도록 구조와 용어를 단순하게 유지해야 한다. |

## Invariants

| ID | Invariant |
| --- | --- |
| I-01 | Research 단계의 최종 책임은 `project-pivot` 메인 agent에 있다. |
| I-02 | `explorer`와 `web-researcher`는 phase owner가 아니라 specialist 또는 도구다. |
| I-03 | Review 팀 외에 별도의 phase agent 팀을 만들지 않는다. |
| I-04 | 강한 기존 근거가 있으면 같은 사실을 반복 조사하지 않는다. |
| I-05 | private reasoning이나 chat transcript를 durable evidence로 저장하지 않는다. |
| I-06 | Research는 OpenSpec의 schema, lifecycle, command 또는 gate를 변경하지 않는다. |
| I-07 | 임시 Research의 보관과 Git 추적 전환에는 사용자 승인이 필요하다. |
| I-08 | 불필요한 reference, script, template 또는 argument를 추가하지 않는다. |

## Allowed Scope

| Area | Allowed |
| --- | --- |
| Repository | 관련 문서, 코드, 설정, 테스트, 실행 결과와 history 조사 |
| External | 현재 환경에 적용 가능한 공식 문서와 1차 자료 조사 |
| Delegation | 하나의 제한된 근거 질문을 specialist에 위임 |
| Execution | 안전한 read-only 재현과 검증 |
| Artifact | 기존 RPI 계약에 따른 Research bundle 생성·갱신 |

## Boundaries

| Boundary | Rule |
| --- | --- |
| OpenSpec ownership | proposal, requirement, design, task를 Research가 확정하지 않는다. |
| Implementation | 코드·테스트·설정을 구현 목적으로 변경하지 않는다. |
| Scope | 인접 개선을 현재 조사에 자동 포함하지 않는다. |
| Evidence | locator 또는 관찰 결과가 없는 주장을 사실로 기록하지 않는다. |
| Human choice | 제품 동작, 아키텍처, 비용이나 위험이 실질적으로 달라지는 선택은 사용자에게 돌린다. |

## Adopted Decisions

| Decision | Rationale |
| --- | --- |
| 메인 agent가 Research를 직접 수행한다. | 사용자의 코파일럿이 전체 맥락과 최종 판단을 유지해야 한다. |
| specialist는 제한된 질문에만 사용한다. | 메인 context 비용을 줄이면서 책임 분산을 방지한다. |
| Arguments를 `SKILL.md` 상단에 둔다. | 사용자가 편집기에서 동작을 빠르게 이해하고 조정할 수 있다. |
| 기존 RPI artifact 계약과 템플릿을 재사용한다. | 중복 규칙과 두 개의 Source of Truth를 만들지 않는다. |
| 별도 script와 reference를 만들지 않는다. | 현재 동작은 명확한 지침만으로 충분하며 초기 구조를 가볍게 유지할 수 있다. |
