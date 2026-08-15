# Requirements

| ID | Requirement |
| --- | --- |
| R-001 | 이 schema는 OpenSpec Change의 계획 lifecycle과 artifact dependency를 정의해야 한다. |
| R-002 | Apply는 Tasks를 직접 dependency로 사용해야 한다. |
| R-003 | Specs는 관찰 가능하고 검증 가능한 행동 계약을 표현해야 한다. |
| R-004 | Tasks는 독립적으로 검증 가능한 구현 결과를 파싱 가능한 최상위 Markdown 체크박스로 표현해야 한다. |
| R-005 | `tasks_total`과 `tasks_completed`는 Tasks 체크박스에서 계산하는 파생값으로 유지해야 한다. |
| R-006 | artifact의 `type`은 `openspec-spec-driven-tdd-<artifact-type>` 형식을 사용해야 한다. |
| R-007 | Tags는 `tag`와 제한된 `prefix:tag`를 허용하며 prefix는 `domain`, `subdomain`, `capability`만 사용할 수 있어야 한다. |
| R-008 | Schema의 Apply 지침은 특정 언어, 테스트 도구, 명령 또는 저장소 구조를 요구하지 않아야 한다. |
| R-009 | 프로젝트별 실행 지침은 `openspec/config.yaml`에서 제공할 수 있어야 한다. |
| R-010 | Schema 개발 문서는 `docs/`, 장기 보존할 개발 의도는 `docs/baseline/`에 위치해야 한다. |

# Decisions

| ID | Decision | Rationale |
| --- | --- | --- |
| D-001 | Workflow는 `Proposal → Specs → Design → Tasks → Apply` 순서를 사용한다. | 계획 artifact가 변경 의도, 행동 계약, 기술적 접근과 구현 작업을 직접 소유하며 별도 review state artifact를 두지 않는다. |
| D-004 | 별도 Test Design artifact를 기본 workflow에 두지 않는다. | Specs, Design, Tasks와 실제 테스트 코드가 기본 검증 책임을 충분히 분담한다. |
| D-005 | Tags는 단일 frontmatter 필드로 유지하고 namespaced tags를 허용한다. | 유연성을 유지하면서 선택적인 구조화 파싱을 지원한다. |
| D-006 | Capability identifier의 canonical source는 `specs/<capability>/spec.md` 경로다. | Proposal 선언과 tags 사이의 충돌을 판정할 기준이 필요하다. |
| D-007 | 모든 Markdown heading을 parser API로 고정하지 않는다. | 인간 가독성과 문서 편집 유연성을 보존한다. |
| D-008 | 행동 변경은 test-first feedback loop를 사용하되 TDD phase를 별도 task로 요구하지 않는다. | TDD의 feedback 가치는 유지하면서 progress와 planning overhead를 줄인다. |
| D-011 | 현재 범위의 feedback은 가장 작은 owning task와 직접 영향받는 planning artifact만 수정한다. | Review remediation workstream과 전체 planning 재순회를 방지한다. |

# Invariants

| ID | Invariant |
| --- | --- |
| I-001 | Proposal, Specs, Design과 Tasks의 책임은 하나의 artifact로 합쳐지지 않는다. |
| I-002 | Schema는 review 결과나 review process state를 별도 artifact로 소유하지 않는다. |
| I-003 | Tasks 진행률의 source of truth는 frontmatter가 아니라 본문의 체크박스다. |
| I-004 | Tags는 workflow gate, artifact dependency 또는 소유권 결정에 사용하지 않는다. |
| I-005 | Schema template은 runtime artifact indexing과 Tasks 집계 대상이 아니다. |
| I-006 | Project-specific command와 tool 선택을 schema baseline에 고정하지 않는다. |
| I-007 | Review, self-review와 RED/GREEN/REFACTOR 같은 process phase는 Tasks 진행률로 추적하지 않는다. |

# Allowed Changes

| Area | Allowed Change |
| --- | --- |
| Templates | parser contract과 artifact 책임을 보존하는 가독성 개선 |
| Instructions | 중복 제거, 표현 개선과 모호성 축소 |
| Documentation | 근거 보강, 예제와 검증 방법 추가 |
| Tags | 허용 prefix를 유지하는 validation 강화 |
| Apply | 범용성과 TDD compatibility를 높이는 최소화 |
| Workflow | Proposal, Specs, Design과 Tasks의 책임을 보존하는 비파괴적 확장 |

# Change Record

## Remove Plan Review Artifact

| Item | Record |
| --- | --- |
| Changed baseline | R-002 수정, R-011과 R-012 제거; D-001 수정, D-002·D-003·D-009·D-010 제거; I-001과 I-002 수정, I-007 제거 |
| Problem | Plan Review는 planning content를 소유하지 않고 review process state만 별도 artifact로 유지해 artifact 책임과 Apply dependency를 불필요하게 늘렸다. |
| Compatibility | 새 Change는 `plan-review.md`를 생성하거나 요구하지 않으며 Apply는 Tasks에 직접 의존한다. 기존 archived `plan-review.md`는 역사 기록으로 유지하고 migration하지 않는다. |
| Rejected alternatives | 축소된 review artifact 유지와 review 상태를 다른 planning artifact에 이동하는 방식은 동일한 process state 책임을 계속 OpenSpec에 남기므로 기각한다. |
| Synchronized changes | `schema.yaml`, schema README, `docs/architecture.md`, baseline과 `templates/plan-review.md`를 함께 갱신한다. |

## Simplify Task And Feedback Contract

| Item | Record |
| --- | --- |
| Changed baseline | R-004와 D-008 수정, D-011과 I-007 추가 |
| Problem | TDD phase와 self-review가 top-level task로 표현되고 review feedback이 remediation workstream으로 누적되면 실제 구현 결과보다 progress item이 빠르게 증가하고 feedback이 다시 review를 만드는 재귀가 발생한다. |
| Compatibility | Artifact DAG, parser syntax와 counter field는 유지한다. 기존 active/archive Tasks는 migration하지 않으며 새로 생성하거나 의미 있게 수정하는 Tasks부터 outcome 중심 형식을 적용한다. Schema version은 유지한다. |
| Rejected alternatives | Review 횟수 제한이나 최대 loop 수만 추가하면 원인인 progress modeling과 feedback ownership은 남는다. 별도 review artifact 복원도 process state를 다시 schema에 넣으므로 기각한다. |
| Synchronized changes | `schema.yaml`, schema README, `templates/proposal.md`, `templates/design.md`, `templates/tasks.md`, `docs/architecture.md`와 baseline을 함께 갱신한다. |

# Change Control

Baseline을 변경하려면 다음을 모두 기록한다.

1. 변경하려는 Requirement, Decision 또는 Invariant ID
1. 기존 규칙이 해결하지 못하는 구체적인 문제
1. 호환성 영향과 migration 방법
1. 대안과 기각 이유
1. Schema, template, validator와 문서에 필요한 동시 변경

단순한 문구 개선은 baseline 변경이 아니다. 의미, 책임 경계, parser contract 또는 workflow gate가 바뀌는 경우에만 baseline을 수정한다.
