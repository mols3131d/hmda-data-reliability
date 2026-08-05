# Directive

이 문서는 인간 주도의 규범적 기준선이다. 사용자의 명시적 요청 없이 수정하지 않는다.

## Purpose

구현 코드와 테스트 코드가 기대 contract를 충족하고 새로운 defect를 도입하지 않는지 근거 중심으로 검토하는 범용 Code Review 엔진을 제공한다.

특정 Agent, Review workflow, VCS, repository 구조 또는 Review artifact에 의존하지 않는다.

## Requirements

| ID | Requirement |
| --- | --- |
| R-01 | file, diff, revision, pull request 또는 현재 code를 Review 대상으로 해석할 수 있어야 한다. |
| R-02 | target, baseline과 contract를 구분하고 유효한 기준이 없으면 추측하지 않아야 한다. |
| R-03 | 요청된 대상과 직접 영향을 받는 behavior만 scope에 포함해야 한다. |
| R-04 | 구현 코드와 테스트 코드에 서로 다른 검토 기준을 적용해야 한다. |
| R-05 | 구현과 테스트가 함께 변경되면 두 대상의 contract 일치를 교차 검증해야 한다. |
| R-06 | 가능한 경우 가장 작은 안전한 기존 validation을 사용해야 한다. |
| R-07 | candidate finding을 reachability, safeguard, baseline과 impact로 재검증해야 한다. |
| R-08 | finding은 location, evidence와 구체적인 impact에 연결되어야 한다. |
| R-09 | severity, verdict와 결과 저장 방식은 호출자의 Review 계약을 존중해야 한다. |
| R-10 | 사용자는 `README.md`, 실행자는 `SKILL.md`, 상세 기준은 `references/`, 개발 기준은 `docs/`에서 확인할 수 있어야 한다. |
| R-11 | 구조와 용어를 사람이 읽고 직접 편집할 수 있을 만큼 단순하게 유지해야 한다. |

## Invariants

- 검토 대상 source, test, fixture와 config를 수정하지 않는다.
- Review 결과 저장이나 갱신은 호출자의 권한과 결과 계약을 따른다.
- 특정 Agent나 Agent 집합을 호출하거나 존재한다고 가정하지 않는다.
- 특정 Review phase, OpenSpec, pull request 또는 Git provider를 필수로 요구하지 않는다.
- 구현 Review와 테스트 Review의 공통 workflow를 중복 정의하지 않는다.
- 테스트는 구현의 부속물이 아니라 독립적인 validation evidence로 검토한다.
- test pass, lint와 automation을 correctness의 완전한 증명으로 취급하지 않는다.
- 실행하거나 재현하지 않은 사실을 수행한 것처럼 주장하지 않는다.
- style 선호, 무관한 기존 defect와 선택적 redesign을 finding으로 만들지 않는다.
- candidate는 reachability와 existing safeguard를 확인한 뒤 finding으로 확정한다.
- baseline이 없으면 defect의 introduced 여부를 단정하지 않는다.
- finding 수보다 impact와 evidence 신뢰성을 우선한다.
- 같은 규칙을 여러 문서에서 반복하지 않는다.

## Content Ownership

| Location | Responsibility |
| --- | --- |
| `README.md` | 사용자용 소개, Arguments, 분리 결정과 예시 |
| `SKILL.md` | 항상 필요한 공통 Review workflow와 경계 |
| `references/workflow.md` | target, baseline, contract, scope, validation과 종료 기준 |
| `references/implementation.md` | production code와 runtime behavior 검토 기준 |
| `references/tests.md` | test design, oracle, false green과 validation 신뢰성 |
| `references/findings.md` | candidate 검증, finding 품질과 synthesis |
| `docs/DIRECTIVE.md` | 목적, 요구사항, 불변 조건과 설계 결정 |
| `docs/WORKING.md` | 현재 구조, 검증 상태와 남은 작업 |

## Boundaries

- Review 결과를 근거 없이 자동 수정 작업으로 전환하지 않는다.
- 제품 동작이나 contract가 모호하면 임의의 구현 선호를 정답으로 선택하지 않는다.
- security, concurrency, performance와 recovery는 target과 관련된 경우에만 검토한다.
- 전체 repository Review가 명시되지 않으면 무관한 영역으로 탐색을 확장하지 않는다.
- caller의 권한보다 넓은 실행, 승인, merge 또는 state change를 가정하지 않는다.

## Decisions

| Decision | Rationale |
| --- | --- |
| 구현과 테스트 Review를 하나의 스킬로 유지한다. | target, contract, impact, regression과 evidence 검증 workflow가 동일하므로 중복과 불일치를 줄인다. |
| 구현과 테스트 기준은 별도 Reference로 분리한다. | 대상별로 필요한 lens만 읽으면서 전문 기준을 유지한다. |
| Agent 이름이나 역할을 스킬에 포함하지 않는다. | 여러 reviewer가 독립적으로 사용할 수 있고 어느 쪽도 필수 dependency가 되지 않게 한다. |
| severity와 verdict taxonomy를 강제하지 않는다. | 다양한 Review 계약과 역할에서 같은 evidence engine을 재사용한다. |
| auto-fix와 source modification을 제외한다. | Review evidence와 수정 작업의 책임을 분리한다. |
| 별도 test-review 스킬은 만들지 않는다. | 현재는 독립 lifecycle이나 출력 계약이 없고 분리 비용이 공통부 중복보다 크다. |
