---
type: review
title: "Reliability Architecture Review for Multi-Agent Development"
description: "PR #284의 구조 개편을 개발 에이전트의 독립 변경·병렬 협업·공유 계약·통합 검증 관점에서 평가하고 필요한 보완과 실증 공백을 구분한다."
tags:
  - architecture
  - multi-agent-development
  - reliability
  - refactoring
---

# Reliability Architecture Review for Multi-Agent Development

> [!IMPORTANT]
> **Assessment: `changes_required`.** 책임 분리·공개 계약·조합 진입점은 개선됐지만, 여러 개발 에이전트가 같은 계약을 발견하고 독립 변경을 안전하게 통합하는 목표는 아직 완료되지 않았다. 정본 안내 이전, provider 입력 projection의 단일 소유, 조사·Recovery 조합의 교차 입력 검증을 보완해야 한다. 실제 병렬 개발의 비용·재작업 감소는 아직 입증하지 않았다. 기존 구조를 유지한 최소 보완을 우선 권고한다.

- **Target:** [PR #284](https://github.com/mols3131d/hmda-data-reliability/pull/284)의 Reliability·Reliability AI·Runtime AI 구조 개편과 관련 계약·소비자·테스트.
- **Revision:** 2026-11-07, head `1b0bd473e1f0e6c8318974e4b150aeb50968c959`, base `57cd2bd49aa380273f677719c6b2aa68f49641ee`. 미추적 05 보고서는 현황 참고 자료이며 구현 판정의 정본이 아니다.
- **Scope:** 개발 에이전트의 변경 국소성, 공유 의미의 소유권, 조합 책임, 통합 검증과 탐색 비용. 제품의 멀티에이전트 실행 기능·모델 품질·전체 correctness 재감사·성능 실험은 이번 평가 대상이 아니다. 변경 권한은 06 작성에 한정하며 제품 코드·계획·기존 보고서는 수정하지 않는다.

## Findings

| ID | Severity | Finding | Action |
| --- | --- | --- | --- |
| F1 | Major | 현재 API와 정본 안내·Spec·Prompt 경로가 달라 작업자가 같은 변경 계약을 재구성하기 어렵다. | 기존 전환 계획 안에서 실제 실행 계약·공개 진입점·guide·인접 검증을 일치시킨다. |
| F2 | Major | bounded context projection이 존재하지만 실제 Evidence 도구가 원본 payload를 별도로 전달한다. | provider 입력 의미를 기존 projection owner로 모으고 실제 tool 메시지까지 연결해 검증한다. |
| F3 | Major | 조사와 Recovery 각각의 유효성이 둘을 조합한 사건·대상 일치를 보장하지 않는다. | 기존 execution 진입점에서 교차 입력 preflight를 소유하고 충돌 시 실행 차단을 검증한다. |

F1~F3은 모두 기존 PR 목표와 [Migration Tasks](../../openspec/changes/reliability-agentic-review-enable-bounded-tools/tasks.md) 안의 미완료 접점이다. Caller는 `current_required`로 분류한다. 이는 해당 구현을 이번 문서 작업에서 수정하라는 권한이 아니다. 선택적 추가 모듈 분리와 개발 생산성 실험은 아래에서 별도로 구분한다.

## Goal Clarification

PR의 목적에는 동등하게 구분해야 할 두 축이 있다.

| Goal | Intended Result | Evidence Needed |
| --- | --- | --- |
| 제품 기능 | 제한된 실제 도구 조사·위임 실행·근거 보고를 제공하면서 결정론적 신뢰성과 외부 승인 경계를 유지한다. | 실행·실패 회귀, 실제 provider·도구 연동, 제품 모델 평가. |
| 개발 아키텍처 | 여러 코딩 에이전트가 올바른 책임 안에서 변경을 완결하고, 공동 수정·재탐색·조정을 줄이며, 합친 뒤에도 계약과 불변식을 유지한다. | 대표 변경의 수정 범위·공유 계약·조합 검증과 실제 협업의 통합 정확성·재작업·비용 근거. |

[05 Progress Report](05-report-reliability-agentic-progress-and-remaining-work.md)는 첫 번째 축을 중심으로 목표를 설명했다. 두 번째 축은 부수적인 운영 편의가 아니라 [01 Plan의 변경 경계·병렬 작업·완료 기준](01-plan-reliability-agentic-complete-refactor.md)에 이미 포함된 목적이다. 이번 사용자 확인은 그 중요성을 명확히 한 것으로 해석한다.

제품에서 복수 Investigator·Supervisor를 동시에 실행하는 기능을 의무화하지 않는다는 판단과, **여러 개발 에이전트가 함께 고치기 좋은 구조를 만들어야 한다는 목표는 서로 모순되지 않는다.** `TaskEnvelope`, `recipient="supervisor"` 또는 제품 도구 호출의 존재만으로 개발 아키텍처 목표를 달성했다고 볼 수 없다. 앞으로 목적을 요약할 때 두 축을 명시해야 하며, 이번 작업에서는 사용자 변경이 있는 05를 그대로 보존했다.

## Review Basis

사용자가 지정한 [Software Architecture for Multi-Agent Development](https://github.com/mols3131d/mols-agent-assets/blob/main/catalog/patterns/software-engineering/multi-agent-development-architecture.md)를 직접 확인했다. 조회 페이지에 표시된 해당 파일의 마지막 변경은 [33199765](https://github.com/mols3131d/mols-agent-assets/commit/33199765f2c988f17acef2226818a170d4237158)이며, 원문을 정본 정책으로 자동 편입하거나 복제하지 않고 이번 평가의 설계 기준으로 사용한다.

| Criterion | Question Applied Here |
| --- | --- |
| 독립 변경 완결성 | 대표 변경을 한 owner의 구현·공개 접점·가까운 테스트로 닫을 수 있는가? |
| 공유 의미의 소유권 | Evidence·결과·오류·상태·쓰기 권한을 한 곳에서 결정하고 다른 구현은 소비하는가? |
| 조합 책임과 검증 | 개별 모듈의 성공과 실제 연결된 사용 사례의 성공을 구별하는 진입점·검증이 있는가? |
| 의존성의 정직한 분류 | 독립·생산자–소비자·결합 변경을 구별하고 계약 결정이 필요한 작업을 무리하게 병렬화하지 않는가? |
| 탐색성과 총 변경 비용 | 공개 API에서 계약·검증까지 찾기 쉬우며 구조 추가 비용보다 공동 수정·통합 재작업 감소가 큰가? |

폴더·agent·테스트 개수, 파일 충돌이 없다는 사실과 개별 green 결과는 이 기준의 대체 지표가 아니다. Branch·worktree·메시지 전달·agent 실행 순서·CI runner 운영은 별도 workflow 책임이며, 이 보고서는 새 orchestrator를 요구하지 않는다.

## Improvements Already Achieved

| Area | Observed Improvement | Limit of the Claim |
| --- | --- | --- |
| 결정론적 책임 | assessment와 remediation으로 탐지·평가와 승인 복구의 변경 이유를 구별하고 공개 export를 제공한다. 고정 workflow를 함수 조합으로 단순화했다. | 책임과 연결 테스트가 있어 단순 폴더 이동만은 아니다. 다만 원래도 독립적이던 코드의 이동 자체를 병렬 생산성 향상으로 계산하지 않는다. |
| Runtime 분리 | provider-neutral tool-call 계약·SDK 매핑을 Runtime이 소유하고 조사 정책은 AI 도메인에 둔다. | wire 계약이 바뀌는 동안 producer와 investigation consumer는 독립 작업이 아니다. |
| 조합 진입점 | `investigate_incident`와 `execute_delegated_task`가 조사·도구·Recovery·보고의 조합 위치를 드러낸다. | 조합 함수의 존재만으로 교차 입력 불변식이 완성되지는 않는다. F3이 그 사례다. |
| 대체 가능한 조회 | [ToolRegistry의 callback](../../src/hmda_reliability/reliability_ai/investigation/tools.py#L112)과 registry 주입이 이미 있다. 별도 조회 구현을 테스트에 연결할 수 있다. | 기본 도구 추가는 정의·인자·dispatch·권한·loop 계약을 함께 검토해야 한다. 모든 도구 개발이 자동으로 독립적이지는 않다. |
| 가까운 검증 | [lifecycle 연결](../../tests/data_operations/test_incident_lifecycle.py#L58), [실제 registry를 연결한 조사 loop](../../tests/reliability_ai/test_investigation_agent.py#L52), [SDK wire](../../tests/runtime_ai/test_provider_tools.py#L45) 테스트가 있다. | 통합 테스트가 전혀 없다는 주장은 부정확하다. 해당 테스트가 보장하지 않는 연결 불변식은 별도로 확인해야 한다. |
| 역의존 방어 | [Tach](../../tach.toml)는 Reliability의 AI 역의존과 Runtime의 도메인 의존을 금지한다. | 현재 선언은 상위 domain 단위다. 하위 폴더별 소유권·오류 의미·데이터 조합까지 증명하지 않으며, 그 자체로 하위 rule 추가가 필수라는 뜻도 아니다. |

**구조적 평가는 긍정적인 부분 개선이다.** 여러 변경의 책임과 연결 위치를 식별하기 쉬워졌지만, 소유 경계가 모든 실제 실행 경로에서 일관되게 소비되는 단계까지 완료되지는 않았다.

## Details

### F1: Contract Discovery and Migration

#### F1 Locations

- [DEVELOPMENT](https://github.com/mols3131d/hmda-data-reliability/blob/1b0bd473e1f0e6c8318974e4b150aeb50968c959/DEVELOPMENT.md#L65), [Architecture](https://github.com/mols3131d/hmda-data-reliability/blob/1b0bd473e1f0e6c8318974e4b150aeb50968c959/docs/ARCHITECTURE.md#L72), [Review AI guide](https://github.com/mols3131d/hmda-data-reliability/blob/1b0bd473e1f0e6c8318974e4b150aeb50968c959/docs/domains/review-ai.md#L35).
- [현재 공개 API](../../src/hmda_reliability/reliability_ai/__init__.py#L23), [public surface 테스트](../../tests/reliability_ai/test_public_surface.py#L47).
- [현재 canonical Spec](https://github.com/mols3131d/hmda-data-reliability/blob/1b0bd473e1f0e6c8318974e4b150aeb50968c959/openspec/specs/reliability-agentic-review/spec.md#L177), [조사 system prompt](../../src/hmda_reliability/reliability_ai/investigation/service.py#L37).

#### F1 Evidence

Guide와 개발·아키텍처 문서는 제거된 `review_ai` 및 고정 staged review를 현재 경로로 설명하고 canonical Spec에는 `no tools` 계약이 남아 있다. 실제 API는 `reliability_ai`의 investigation/execution이며 public surface 테스트는 옛 패키지 부재를 요구한다. 조사 실행은 이전 안내의 native Prompt 공통 경로가 아니라 inline system 지침을 사용한다. Active delta와 이전 계획은 있으나 동기화·연결은 미완료다.

#### F1 Impact

개발 에이전트 A가 정본 guide로 평가·Prompt consumer를 작성하고 B가 현재 API를 확장하면 서로 다른 실행·결과 계약을 구현할 수 있다. 이는 문서 표현의 선호가 아니라 **어떤 접점을 안정된 전제로 삼을지 매번 재조사해야 하는 비용과 의미적 통합 위험**이다.

#### F1 Action

`Scope relation: acceptance_gap` · `Disposition: current_required`. 기존 Task 3·7에서 실행 계약과 native Prompt 경로를 검증한 뒤 Spec·Purpose·guide·CLI·인접 테스트를 함께 이전한다. 기존 entrypoint와 타입으로 충분하면 새 index나 별도 agent 문서를 추가하지 않는다. 옛 패키지 wrapper 복원이나 과거 실행 기록 재작성도 요구하지 않는다.

### F2: One Owner for Provider Input Meaning

#### F2 Locations

- [입력 allowlist와 projection](../../src/hmda_reliability/reliability_ai/context.py#L31), [canonical 입력 함수](../../src/hmda_reliability/reliability_ai/prompt/__init__.py#L47).
- [snapshot catalog 구성](../../src/hmda_reliability/reliability_ai/investigation/tools.py#L212), [Evidence payload 반환](../../src/hmda_reliability/reliability_ai/investigation/tools.py#L285).
- [tool 결과의 provider 전달](../../src/hmda_reliability/reliability_ai/investigation/service.py#L303), [기존 context 테스트](../../tests/reliability_ai/test_context.py#L104).

#### F2 Evidence

`build_bounded_review_context`는 source별 허용 필드·크기·출처 의미를 소유한다. 반면 기본 registry는 snapshot의 전체 Evidence를 catalog에 보관하고 `get_incident_evidence`가 `evidence.payload`를 그대로 반환하며, service는 그 결과를 tool 메시지로 전달한다. Snapshot 복사·인자 검증·권한·byte 한도는 있지만 공통 projection을 소비하지 않는 이 경로를 대신 막지는 않는다.

#### F2 Impact

A가 입력 projection을 수정해도 B가 담당하는 실제 도구 응답의 의미는 함께 바뀌지 않는다. 두 모듈을 별도로 테스트하고 합쳐도 provider가 받는 자료의 의미가 달라질 수 있다. 따라서 **공유 정책이 두 경로로 분산된 상태를 독립 구현 가능성으로 계산할 수 없다.**

#### F2 Action

`Scope relation: contract_dependency / acceptance_gap` · `Disposition: current_required`. Task 1·4에서 provider 전달 자료의 의미를 기존 projection owner로 모으고 tool source·snapshot/current provenance를 보존한다. 기존 조사 loop 테스트에서 실제 provider 메시지에 비허용 필드·개인 경로가 없는지도 확인한다. 이 목적만으로 generic plugin 시스템·새 DI 계층·중복 정책 모델을 만들 필요는 없다.

### F3: Composition Invariants at the Execution Boundary

#### F3 Locations

- [위임 execution 분기](../../src/hmda_reliability/reliability_ai/execution/service.py#L105), [두 번째 복구 요청 선택](../../src/hmda_reliability/reliability_ai/execution/service.py#L175), [조사 기반 보고 참조](../../src/hmda_reliability/reliability_ai/execution/service.py#L280).
- [하위 승인 guard](../../src/hmda_reliability/reliability/remediation/recovery/executor.py#L330), [wrapper 보고 테스트](../../tests/reliability_ai/test_execution_service.py#L148).

#### F3 Evidence

Wrapper는 Task action·connection을 확인하고 caller의 approved request를 하위 executor로 전달한다. 두 요청을 함께 주면 `if/elif`로 하나를 선택하며, 조사 incident·target·partition·snapshot refs와 요청 사이의 일치를 선행 검증하지 않는다. 하위 guard는 approval과 proposal의 exact binding을 검증하지만 조사 입력을 받지 않으므로 이 관계를 검증할 수 없다. 이번 검토에서는 실제 DB 실행으로 재현하지 않고 공개 입력·분기·guard 범위를 정적으로 확인했다.

#### F3 Impact

개별적으로 유효한 조사 A와 승인 요청 B를 결합해 B를 실행하면서 A의 조사·근거를 보고할 수 있는 구조다. 이는 **각 모듈의 로컬 성공과 조합 성공을 구별해야 하는 사례**이며, 무승인 mutation 우회가 입증됐다는 뜻은 아니다. Recovery 결과·오류 의미와 보고 의미를 서로 독립적으로 바꿔도 된다는 근거로 사용할 수 없다.

#### F3 Action

`Scope relation: explicit_target / acceptance_gap` · `Disposition: current_required`. Task 2에서 기존 execution 진입점이 교차 입력 preflight를 소유하고 불일치·복수 요청 시 executor 미호출을 검증한다. 기존 domain 결과와 실제 연결되는 보고 불변식도 확인한다. 하위 Recovery를 AI에 의존시키거나 승인 의미를 wrapper에 복제하지 않는다. 전체 백필 로직을 새 조합 계층으로 옮기는 것도 필요조건이 아니다.

## Parallel Change Assessment

다음은 코드의 책임·계약을 대조한 **설계상 변경 시나리오**다. 실제 병렬 에이전트 작업을 수행하거나 속도 향상을 측정한 결과가 아니다.

| Paired Changes | Relationship | Local Ownership and Verification | Parallel Condition |
| --- | --- | --- | --- |
| Remediation 초안의 권고 계산과 provider transport 오류 보완 | 독립 후보 | [초안 workflow](../../src/hmda_reliability/reliability/remediation/workflow.py)와 [초안 테스트](../../tests/reliability/test_remediation_draft.py); [provider](../../src/hmda_reliability/runtime_ai/provider.py)와 [provider 테스트](../../tests/runtime_ai/test_provider.py). | 공개 I/O·오류 계약을 유지하는 내부 변경이면 서로의 결정을 기다리지 않고 진행할 수 있다. |
| ToolCall wire 계약과 investigation consumer 확장 | 생산자–소비자 | [Runtime 계약](../../src/hmda_reliability/runtime_ai/contracts.py), wire 테스트; investigation service와 loop 테스트. | call ID·arguments·오류 의미를 먼저 합의한다. 호환 확장이 아니면 한 변경으로 이전하거나 순차 처리한다. |
| Recovery 결과·mutation state와 ReportEnvelope 해석 변경 | 결합 | Recovery executor·result와 [승인 검증 테스트](../../tests/reliability/test_approval_backfill_validation.py); execution service와 wrapper 테스트. | authoritative 결과 의미를 한 owner가 정하고 실제 연결 검증을 수행한다. 두 테스트 집합의 개별 green만으로는 통합 완료가 아니다. |
| Profile 조회와 dbt impact 조회 보완 | 조건부 독립 | 기존 registry의 서로 다른 handler와 [도구 테스트](../../tests/reliability_ai/test_investigation_tools.py). | 공통 projection·도구 schema·권한 계약을 먼저 고정하고 handler 내부로 끝나는 변경만 병렬 후보로 둔다. 등록·dispatch까지 동시 변경하면 결합 작업이다. |

이는 파일을 agent별로 배분한 목록이 아니다. 공유 의미가 바뀌면 같은 변경 쌍의 분류도 달라진다. 병렬화할 수 없는 결정을 숨기는 것보다 좁은 순차 작업으로 명시하는 편이 이 목적에 부합한다.

## Improvement Options and Priority

| Option | Benefit and Cost | Recommendation |
| --- | --- | --- |
| A. 현 상태 유지 | 추가 이전 비용은 없지만 F1~F3의 계약 탐색·공유 정책·조합 공백이 남는다. | 현재 PR 목표의 완료안으로는 부족하다. |
| B. 기존 책임 안의 최소 보완 | 기존 공개 API·projection·registry callback·execution 진입점과 가까운 테스트를 유지하면서 확인된 접점을 닫는다. 새 consumer 이전 비용을 제한할 수 있다. | 우선 선택한다. 기존 Task 1~4·7과 직접 연결된다. |
| C. 책임 경계의 추가 재설계 | 도구·prompt·저장·관측을 더 나누면 반복 충돌을 줄일 가능성은 있지만 export·상태 의미·consumer·검증 이전 비용이 든다. | 실제 공동 수정·재작업이 집중되는 증거가 있을 때만 B와 비교한다. 현재 필수로 확정할 근거는 없다. |

우선순위는 **공유 의미와 조합을 먼저 안정화한 뒤 그 계약을 소비하는 내부 구현을 병렬화**하는 것이다. F2의 projection과 F3의 입력 일치 기준을 먼저 정하고, F1의 정본 안내·실행 이전은 해당 계약과 함께 갱신한다. Task 7 마지막에만 문서를 손보거나 최종 통합 때 처음 연결하는 방식은 피한다.

현재 evidence만으로 `ToolRegistry`의 공유 파일, service 크기, 하위 Tach rule 부재를 새 결함으로 선언하지 않는다. 추가 분할은 `follow_up`으로 비교할 수 있으며, 광범위 계층·프레임워크·분산 구조 도입은 별도의 `scope_decision`이 필요하다. Agent 수에 맞는 모듈 수, 이벤트 버스, 마이크로서비스, 새 공통 계약 package, mandatory contract-test 인프라는 권고하지 않는다.

## Collaboration Evidence Still Needed

01 Plan과 기존 Task 7에는 개발 에이전트의 독립 변경·계약 충돌·통합 오류·재작업 증거를 남기는 목표가 있지만, 현재까지 동일 조건에서 이를 비교한 결과는 확인하지 못했다. 앞선 결함 수정의 반복 리뷰는 재작업 기록으로 참고할 수 있어도, **아키텍처 변경이 재작업을 줄이거나 늘렸다는 인과적 증거는 아니다.**

목적 달성을 설명할 다음 증거는 실제 대표 변경을 통해 남길 수 있다. 신규 benchmark 플랫폼이나 고정 A/B 절차가 필요한 것은 아니다.

| Evidence | Record in the Existing Work |
| --- | --- |
| 독립 완료 | 각 변경이 읽고 수정한 owner·공유 파일·계약과 로컬 검증 결과. 다른 작업의 미결정에 의존했다면 그 사실. |
| 의존성 충족 | 생산자와 소비자가 합의한 공개 I/O·오류·상태 의미, 호환 여부와 실제 합친 동작. |
| 통합 정확성 | 단위 성공과 별개로 연결된 성공·실패·재검증·보고 불변식이 유지되는지. |
| 재작업과 조정 | 계약 오해·중복 정책·공동 수정·통합 오류로 다시 고친 범위와 원인. 텍스트 충돌과 의미적 충돌을 구분한다. |
| 총 변경 비용 | 가능하면 같은 작업 조건의 탐색·조정·통합·재작업 시간을 포함해 비교한다. Agent 모델·도구·task가 달랐다면 구조 효과와 분리한다. |

이 증거 확보는 원래 개발 아키텍처 목표의 완료 확인이다. 다만 이번 리뷰가 결과를 수행한 것은 아니며, 숫자 목표나 특정 실험 설계를 새 acceptance로 추가하지 않는다. 제품 모델의 Langfuse 점수·live 도구 성공률과 개발 에이전트의 협업 효과는 서로 다른 평가다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| Pass | 사용자 reference 직접 확인 | 지정된 개인 repository의 문서와 표시된 마지막 파일 commit을 조회하고 변경 책임·공유 의미·통합·비용 기준을 추출했다. |
| Pass | 상태와 정적 근거 확인 | Caller는 head·base 기준을 고정하고 주요 projection·도구 전달·execution·guide·Tach·계획을 대조했다. 구현은 수정하지 않았다. |
| Pass | 독립 두 관점 검토 | 별도 Verifier·Challenger가 독립 문맥에서 정적으로 검토하고 Root가 후보를 통합했다. Caller는 3건의 사실·기존 safeguard·scope를 확인해 수용했다. 두 관점이 runtime을 재현한 것은 아니다. |
| Not Verified | 이번 평가의 제품 실행·Tach·type·pytest 재실행 | 수행하지 않았다. 05가 기록한 485개 선택 테스트·33개 Spec 검사·CI 성공은 과거 상태의 보조 근거이며 협업 효과의 증명이 아니다. |
| Not Verified | 실제 개발 에이전트의 병렬 비교 | 동일 조건의 총 비용·독립 완료·계약 충돌·통합 재작업 감소를 측정하지 않았다. 구조상 가능성과 실측 성과를 구분했다. |

## Risks and Limits

이번 판정은 해당 architecture goal의 보완사항을 정리한 것이며 PR 전체의 새 correctness 승인이나 GitHub review submission이 아니다. F1~F3은 04의 F1~F6 closure를 번복한 것이 아니라 다른 평가 축에서 남은 전환·조합 acceptance를 확인한 것이다.

05는 전체 현황, 본 문서는 개발 에이전트 협업 관점의 평가, OpenSpec Change는 구현 계획을 소유한다. 이번 작업은 06만 추가하며 정본 계약·코드·기존 문서·PR 상태·Git history를 변경하지 않는다. 이후 source나 공유 계약을 수정하면 해당 근거와 분류를 다시 확인해야 한다.
