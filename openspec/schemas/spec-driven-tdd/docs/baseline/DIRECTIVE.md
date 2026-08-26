# Requirements

| ID | Requirement |
| --- | --- |
| R-001 | 이 schema는 OpenSpec Change의 계획 lifecycle과 artifact dependency를 정의해야 한다. |
| R-002 | Apply는 Tasks를 직접 dependency로 사용해야 한다. |
| R-003 | Specs는 관찰 가능하고 검증 가능한 행동 계약을 표현해야 한다. |
| R-004 | Tasks는 독립적으로 검증 가능한 구현 결과에만 파싱 가능한 최상위 Markdown 체크박스를 사용해야 한다. |
| R-005 | `tasks_total`과 `tasks_completed`는 Tasks의 파싱 대상 최상위 체크박스에서 구조적으로 계산하는 파생값으로 유지해야 한다. |
| R-006 | artifact의 `type`은 `openspec-spec-driven-tdd-<artifact-type>` 형식을 사용해야 한다. |
| R-007 | Tags는 optional `tag`와 제한된 `prefix:tag`를 허용하며 prefix는 `domain`, `subdomain`, `capability`만 사용할 수 있어야 한다. |
| R-008 | Schema의 Apply 지침은 특정 언어, 테스트 도구, 명령 또는 저장소 구조를 요구하지 않아야 한다. |
| R-009 | 프로젝트별 실행 지침은 `openspec/config.yaml`에서 제공할 수 있어야 한다. |
| R-010 | Schema 개발 문서는 `docs/`, 장기 보존할 개발 의도는 `docs/baseline/`에 위치해야 한다. |
| R-013 | Spec-level behavior가 없는 Change는 OpenSpec change metadata의 `skip_specs: true`를 사용해 delta Spec 없이 진행할 수 있어야 한다. |
| R-014 | Design은 Proposal과 Specs가 소유하지 않는 non-obvious technical delta만 기록해야 한다. |

# Decisions

| ID | Decision | Rationale |
| --- | --- | --- |
| D-001 | Workflow는 `Proposal → Specs → Design → Tasks → Apply` 순서를 사용한다. | 계획 artifact가 변경 의도, 행동 계약, 기술적 접근과 구현 작업을 직접 소유하며 별도 review state artifact를 두지 않는다. |
| D-004 | 별도 Test Design artifact를 기본 workflow에 두지 않는다. | Specs, Design, Tasks와 실제 테스트 코드가 기본 검증 책임을 충분히 분담한다. |
| D-005 | Tags는 optional metadata로 단일 frontmatter 필드에만 표현한다. | 검색·분류를 허용하면서 planning artifact 사이의 불필요한 metadata 복제를 피한다. |
| D-006 | Capability identifier의 canonical source는 `specs/<capability>/spec.md` 경로다. | Proposal 선언과 tags 사이의 충돌을 판정할 기준이 필요하다. |
| D-007 | 모든 Markdown heading을 parser API로 고정하지 않는다. | 인간 가독성과 문서 편집 유연성을 보존한다. |
| D-008 | 행동 변경은 test-first feedback loop를 사용하되 TDD phase를 별도 task로 요구하지 않는다. | TDD의 feedback 가치는 유지하면서 progress와 planning overhead를 줄인다. |
| D-011 | 현재 범위의 feedback은 기존 owning task를 수정하거나 누락된 최소 implementation task를 추가하고, planning 수정은 owning artifact와 직접 영향받는 downstream에 한정한다. | Review remediation workstream과 전체 planning 재순회를 방지하면서 실제 누락 작업은 숨기지 않는다. |
| D-012 | Spec-free Change는 `skip_specs: true`를 사용하고 placeholder Capability나 Requirement를 만들지 않는다. | OpenSpec이 제공하는 zero-delta contract를 사용해 구현 변경을 행동 계약으로 오분류하는 drift를 방지한다. |
| D-013 | Design은 standalone change summary가 아니라 prerequisite artifact에서 결정되지 않는 technical delta 문서로 유지한다. | Proposal·Specs의 반복 소유를 줄이고 Design이 실제 구현 판단만 추가하도록 한다. |

# Invariants

| ID | Invariant |
| --- | --- |
| I-001 | Proposal, Specs, Design과 Tasks의 책임은 하나의 artifact로 합쳐지지 않는다. |
| I-002 | Schema는 review 결과나 review process state를 별도 artifact로 소유하지 않는다. |
| I-003 | Tasks 진행률의 source of truth는 frontmatter가 아니라 본문의 파싱 대상 체크박스다. |
| I-004 | Tags는 workflow gate, artifact dependency 또는 소유권 결정에 사용하지 않는다. |
| I-005 | Schema template은 runtime artifact indexing과 Tasks 집계 대상이 아니다. |
| I-006 | Project-specific command와 tool 선택을 schema baseline에 고정하지 않는다. |
| I-008 | Review, self-review, TDD phase와 다른 process/gate state는 Tasks의 최상위 체크박스로 표현하지 않는다. |
| I-009 | `skip_specs: true`인 Change는 delta Spec을 생성하지 않으며 spec-level behavior 변화가 생기면 marker를 제거하고 Specs를 작성한다. |
| I-010 | Design은 Why, scope, impact, Capability, Requirement, Scenario, acceptance 또는 unchanged behavior를 다시 소유하지 않으며, 새 observable behavior가 발견되면 Specs로 되돌린다. |

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
| Changed baseline | R-004, R-005, R-007과 D-005, D-008 수정; D-011과 I-008 추가 |
| Problem | TDD phase와 self-review를 top-level task로 표현하고 review feedback을 remediation workstream으로 누적하면 실제 구현 결과보다 progress item이 증가한다. Parser는 checkbox 의미를 구분하지 않으므로 semantic exclusion을 parser 동작처럼 설명할 수도 없다. 반복 tags와 planning boilerplate도 별도 drift surface를 만든다. |
| Compatibility | Artifact DAG, checkbox parser syntax와 counter field는 유지한다. Tags field도 계속 허용한다. 기존 active/archive artifact는 migration하지 않으며 새로 생성하거나 의미 있게 수정하는 artifact부터 최소 형식을 적용한다. Schema version은 유지한다. |
| Rejected alternatives | Review 횟수 제한이나 최대 loop 수만 추가하면 원인인 progress modeling과 feedback ownership은 남는다. 별도 review artifact 복원도 process state를 다시 schema에 넣으므로 기각한다. |
| Synchronized changes | `schema.yaml`, schema README, `templates/proposal.md`, `templates/spec.md`, `templates/design.md`, `templates/tasks.md`, `docs/architecture.md`와 baseline을 함께 갱신한다. |

## Support Spec-Free Changes

| Item | Record |
| --- | --- |
| Changed baseline | R-013, D-012와 I-009 추가 |
| Problem | Spec-level behavior가 없는 refactor를 OpenSpec Change로 다룰 때 zero-delta 경로가 schema에 드러나지 않아 내부 구현 구조를 새 Capability와 Requirement로 오분류한 사례가 있었다. |
| Compatibility | Behavior-changing Change의 Proposal → Specs → Design → Tasks 흐름은 유지한다. Spec-free Change는 OpenSpec change metadata의 `skip_specs: true`를 사용하며 기존 archive는 migration하지 않는다. Schema version과 artifact DAG는 유지한다. |
| Rejected alternatives | Validation을 만족시키기 위한 placeholder Capability/Requirement 생성과 별도 no-spec artifact 추가는 잘못된 canonical contract 또는 불필요한 workflow surface를 만들므로 기각한다. |
| Synchronized changes | `schema.yaml`, schema README, `templates/proposal.md`, `docs/architecture.md`와 baseline을 함께 갱신한다. |

## Constrain Design Ownership

| Item | Record |
| --- | --- |
| Changed baseline | R-014, D-013과 I-010 추가 |
| Problem | Design이 prerequisite인 Proposal과 Specs의 동기, scope, behavior와 acceptance를 다시 서술하면서 같은 판단을 여러 artifact가 소유하고 downstream drift surface가 커졌다. |
| Compatibility | Design artifact와 workflow dependency는 유지한다. 새 Design과 의미 있게 수정하는 Design부터 technical delta만 기록하며 기존 archive는 migration하지 않는다. Schema version과 parser contract는 유지한다. |
| Rejected alternatives | Design 제거 또는 optional artifact화는 현재 workflow dependency를 바꾸는 비용이 크고, 중복의 직접 원인은 artifact 존재가 아니라 Design의 과도한 소유권이므로 채택하지 않는다. |
| Synchronized changes | `schema.yaml`, schema README, `templates/design.md`, `docs/architecture.md`와 baseline을 함께 갱신한다. |

# Change Control

Baseline을 변경하려면 다음을 모두 기록한다.

1. 변경하려는 Requirement, Decision 또는 Invariant ID
1. 기존 규칙이 해결하지 못하는 구체적인 문제
1. 호환성 영향과 migration 방법
1. 대안과 기각 이유
1. Schema, template, validator와 문서에 필요한 동시 변경

단순한 문구 개선은 baseline 변경이 아니다. 의미, 책임 경계, parser contract 또는 workflow gate가 바뀌는 경우에만 baseline을 수정한다.
