---
type: plan
title: "Project Skill Context Harness Optimization"
description: "7개 프로젝트 스킬의 컨텍스트 주입과 문서 라우팅을 보존하면서 과잉 지시와 중복된 책임을 최적화하고 검증한다."
---

# Project Skill Context Harness Optimization

> [!IMPORTANT]
> **PR #298 완료 목표는 하네스 최적화 구현과 검증이다.** 이 번들은 초기 검토·인계를 준비한 상태이며 실제 스킬 수정과 최적화 검증은 **아직 미완료**다. 준비 완료를 PR 완료로 취급하지 않는다.

## Goal

현재 모델 역량과 프로젝트 하네스에 맞춰 다음 7개 스킬의 **실효성, 선택 정확성, 컨텍스트 로딩 효율, 책임 경계**를 개선한다. 컨텍스트를 Skill로 주입하고 canonical 문서를 필요한 때에 라우팅하는 것은 유지할 핵심 설계다. 스킬 수나 문자 수 자체를 줄이는 것이 목표가 아니다.

**보존:** Skill 기반 컨텍스트 주입, 문서·Rule·reference의 조건부 라우팅, Progressive Disclosure, 프로젝트 고유 계약, scope·권한·안전 경계.

**최적화 후보:** 일반적 모델 추론으로 충분한 세부 절차, 다른 정본의 장문 재진술, 실제 효용 없는 인수·출력 계약, 중복 reviewer/loop 제어, 부적절한 무조건 로딩.

## Scope and Ownership

대상은 아래 7개 Skill, 실제로 관련된 reference와 라우팅·하네스 연결 지점이다. 변경에 필요하면 `.agents/route/`, `CHATBOT.md`, Inbox guideline 및 정본 문서의 **직접 영향받는 부분만** 조정할 수 있다. Generated index는 owner가 정한 동기화 방식으로 갱신하며 외부 tool의 managed state를 수동으로 고치지 않는다. 제품 기능, 데이터 파이프라인과 무관한 코드·테스트 변경은 범위 밖이다.

각 디렉터리의 `README.md`는 개별 작업 단위다. 현재 판단은 **`main` `fe67f9eb6b76f4f4f3215c355dbdff91f689b7f7` 정적 검토에서 시작한 가설**이므로, 로컬 작업에서 source와 route index를 다시 확인한다.

| Skill | Optimization focus |
| --- | --- |
| [Development Context](prj-load-context-development/README.md) | 개발 문서 주입과 독립 리뷰 정책의 책임 분리 |
| [Review Context](prj-load-context-review/README.md) | reviewer gate 보존 및 중복 orchestration 제거 |
| [Research Workspace](prj-research-workspace/README.md) | 템플릿·근거 라우팅 보존 및 범용 절차 축소 |
| [Code Review](prj-review-code/README.md) | 구현·테스트 리뷰 컨텍스트의 고유 책임 정리 |
| [Spec-Driven TDD RPI](prj-spec-driven-tdd-rpi/README.md) | OpenSpec 전용 controller의 필요한 delta만 유지 |
| [Testing Context](prj-testing-context/README.md) | 테스트 목적별 최소 문서 선택 검증 |
| [Git/GitHub Context](prj-vcs-git-github/README.md) | 작업별 VCS 정책 라우팅 유지·정확화 |

## Execution

1. 현재 PR head에서 각 Skill 원문·reference·route index·관련 canonical owner를 확인한다. 일반 모델 지시와 프로젝트 고유 context delivery의 차이를 근거로 판정한다.
2. 개별 스킬에서 **정상 선택과 near-miss** 시나리오를 확보하고 현재 로딩·행동·경계를 기록한다. 중복·비용의 가설이 실제로 타당한지 검증한다.
3. 각 스킬의 필요 변경을 최소 범위로 구현한다. 대체 경로가 실제 작동하는지 확인하기 전에는 조건부 context router를 삭제하거나 기능을 합치지 않는다. 정당한 유지 결정도 근거로 기록한다.
4. 로딩된 문서, routing 선택, project-specific contract, 권한·scope 경계가 변경 전후 유지되거나 개선되는지 검증한다. 관련 native lint/check/test를 실행하고 미실행 항목을 구분한다.
5. PR 설명과 각 작업 기록에 변경 결과, 검증, 남은 위험과 후속 사항을 반영한다. 리뷰 의견은 근거를 재검토해 채택·기각하며 불필요한 scope 확장을 금한다.

## Completion Criteria

이 PR은 **다음 조건을 모두 충족할 때에만** 완료로 판단한다.

- 7개 Skill마다 실제 효용과 중복을 검토하고, 필요한 수정·통합·삭제 또는 근거 있는 무변경 결정을 완료한다.
- 필요한 변경은 실제 source·reference·route linkage에 반영한다. 더 이상 필요 없는 분기·중복 절차는 제거하되 스킬 주입·문서 라우팅 기능을 유지한다.
- 대표 요청과 near-miss에서 Skill 선택과 필요 문서 로딩을 확인하고, 핵심 계약·안전 경계가 회귀하지 않았다는 검증 근거를 남긴다.
- 변경된 저장소 파일에 적용되는 Markdown·asset·routing·CI 검사를 수행하고 실패/미검증과 제한을 기록한다.
- PR diff와 구현 변경의 적합성을 재검토한다. 검토 번들 작성, static review 또는 CI pass만으로 완료를 선언하지 않는다.

## Handoff

로컬 작업 에이전트는 각 하위 디렉터리를 작업 단위로 사용해 **검토 → 최소 변경 → 직접 검증**을 진행한다. 검토 후보를 자동 수용하지 않는다. 모델 역량 향상을 이유로 실제 도움이 되는 Skill 기반 context injection 및 routing을 제거하지 않는다. 작업을 마친 스킬별로 선택 근거, 변경 사항, 검증 결과를 같은 파일에 갱신한다.

## References

- [Repository instructions](../../../AGENTS.md) · [Chatbot entrypoint](../../../CHATBOT.md) · [Routing entrypoint](../../../.agents/route/ROUTE.md)
- [Skill discovery index](../../../.agents/route/skills.jsonl) · [OpenSpec implementation schema](../../../openspec/schemas/spec-driven-tdd/schema.yaml)
- [Inbox ownership](../../AGENTS.md)
