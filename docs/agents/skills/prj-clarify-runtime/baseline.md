# Clarify Runtime Baseline

이 문서는 `prj-clarify-runtime`의 유지보수 기준선이다. Runtime 실행 절차를 정의하지 않고, 후속 변경에서도 보존해야 할 목적과 불변조건만 소유한다. 일상적인 구현이나 문구 정리로 이 기준을 바꾸지 않으며, 의미를 바꿀 때는 의도된 설계 변경으로 다룬다.

## Purpose

기능이나 domain behavior를 바꾸지 않고 runtime 이해 부채를 줄인다.

Runtime 이해 부채는 실행 후 중요한 경로, 결정, 상태 변화, 외부 action 또는 실패 원인을 existing evidence만으로 신뢰할 수 있게 복원하기 어려운 상태다. Evidence가 부족할 때뿐 아니라 중복되거나 noisy하고, 서로 연결되지 않거나, 잘못된 책임 경계에 있을 때도 발생한다.

목표는 evidence를 늘리는 것이 아니라 필요한 실행 의미를 적절한 책임 경계에서 최소하고 명확하게 보존해 복원 가능성을 높이는 것이다.

## Protected Invariants

| Invariant | Rationale |
| --- | --- |
| **Behavior-preserving** — domain behavior와 기존 caller/consumer contract를 보존한다. | 이해 개선과 동작 변경을 분리해야 변경 이유와 검증 범위가 명확하다. |
| **Problem-bounded** — 한 번에 하나의 주된 복원 문제에 집중한다. | 변경 범위를 실제 이해 비용에 연결하고 일반적인 정리나 과잉 관찰로의 확장을 막는다. |
| **Existing-evidence-first** — 복원 문제를 해결하는 가장 작은 변경을 선택하고 새 evidence보다 기존 evidence의 재사용·정리·재배치를 우선한다. | 새로운 관찰 수단 자체가 추가 이해 부채를 만들 수 있다. |
| **Evidence-neutral** — runtime clarification을 logging이나 특정 observability 수단과 동일시하지 않는다. | 핵심은 도구의 종류가 아니라 실행 의미를 복원할 evidence의 품질과 소유권이다. |
| **Ownership-aligned** — evidence의 의미는 그 사실이나 결정을 소유하는 책임 경계에 둔다. | 같은 의미가 여러 경계에 분산되면 해석, 중복과 변경 비용이 커진다. |
| **Evidence, not contract** — runtime evidence는 실행을 설명하되 requirement, domain policy 또는 canonical contract를 대신 정의하지 않는다. | 관찰 결과가 요구사항이나 정책의 우회적인 정의가 되는 것을 막는다. |
| **Data-minimal** — 민감 정보와 복원 문제에 필요하지 않은 데이터를 evidence에 포함하지 않는다. | 이해 가능성을 높이지 않는 데이터는 노출과 운영 비용만 늘린다. |
| **Scope-disciplined** — 주된 문제가 runtime 이해 부채가 아니면 이 Skill의 범위를 넓히지 않고 해당 책임으로 넘긴다. | Skill이 debugging, monitoring, architecture 또는 다른 책임을 흡수하는 것을 막는다. |
| **Stop-when-clear** — 선택한 복원 문제가 해소되면 추가 evidence나 정리를 위해 scope를 확대하지 않는다. | 더 많은 evidence가 항상 더 나은 runtime 이해를 만들지는 않는다. |

구현 방식과 문서 표현은 바뀔 수 있지만, 위 불변조건은 `prj-clarify-runtime`의 책임이 의도적으로 변경되지 않는 한 유지한다.
