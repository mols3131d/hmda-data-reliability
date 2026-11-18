---
type: plan
title: "Reliability Agentic Continuation Plan"
description: "05 현황과 06 아키텍처 평가를 바탕으로 기존 7개 OpenSpec 과제의 작업 순서, 책임 소유권, 병렬화 조건과 완료 근거를 보강하는 안을 정리한다."
tags:
  - reliability
  - architecture
  - multi-agent-development
  - evaluation
---

# Reliability Agentic Continuation Plan

## Summary

**공유 계약과 조합 불변식을 먼저 안정화하고, 공통 실행·관측·실험을 연결한 뒤 실제 평가와 최종 통합을 완료한다.** 제품의 제한된 조사·위임 기능과 개발 에이전트의 독립 변경·정확한 통합을 동등한 목표로 유지한다. 기존 책임 안의 최소 보완을 우선하며 새 프레임워크나 대규모 모듈 재설계를 선행 조건으로 삼지 않는다.

이 문서는 [05 Progress Report](05-report-reliability-agentic-progress-and-remaining-work.md)와 [06 Architecture Review](06-review-reliability-multi-agent-development-architecture.md)를 바탕으로 한 **비정본 후속 계획안**이다. 사용자 요청에 따라 앞서 제안한 내용을 Inbox에 정리하며, OpenSpec 변경안의 승인이나 구현 착수를 대신하지 않는다.

- **Work unit:** PR #284, branch `agent/refactor/evolve-reliability-agentic-architecture`.
- **Evidence basis:** 2026-11-07 확인한 head `1b0bd473e1f0e6c8318974e4b150aeb50968c959`, base `57cd2bd49aa380273f677719c6b2aa68f49641ee` 및 05·06의 제한된 검증 근거.
- **Planning owner:** 기존 Change `reliability-agentic-review-enable-bounded-tools`의 [Proposal](../../openspec/changes/reliability-agentic-review-enable-bounded-tools/proposal.md), [Design](../../openspec/changes/reliability-agentic-review-enable-bounded-tools/design.md), [Tasks](../../openspec/changes/reliability-agentic-review-enable-bounded-tools/tasks.md). 확인 시 구현 과제는 0/7이며 선행 코드의 존재와 acceptance 완료는 구분한다.
- **Current action:** 이 문서만 추가한다. 05·06, OpenSpec, 제품 코드·테스트, 원격 평가 자산과 PR 상태는 변경하지 않는다.

## Goals and Boundaries

| Goal | Intended Result | Completion Evidence |
| --- | --- | --- |
| 제품 기능 | 결정론적 Reliability와 외부 승인 경계를 유지하면서 제한된 실제 조회·동적 조사·위임 실행·근거 보고를 제공한다. | 성공·실패 회귀, 실제 provider·도구 연결, 근거 보존, 실제 모델 비교와 별도의 사람 평가. |
| 개발 아키텍처 | 개발 에이전트가 책임 안에서 변경을 완결하고 공유 의미를 재구성하는 비용을 줄이며, 합친 뒤에도 계약과 불변식을 유지한다. | 대표 변경의 소유 범위·계약 의존성·연결 검증, 실제 협업의 의미적 충돌·재작업·조정 근거. |

제품 runtime의 복수 agent 도입이 선택적이라는 판단으로 개발 아키텍처 목표를 축소하지 않는다. 반대로 파일 분리·개별 테스트 통과·`TaskEnvelope`의 존재를 협업 비용 개선의 실증으로 해석하지 않는다.

현재 `null_spike` 범위와 기존 `AgenticReviewInput`의 데이터 계약을 유지한다. Investigation은 read-only이며 모델·Task·상위 위임은 Approval이나 mutation 권한을 만들지 못한다. 결정론적 truth·Recovery·승인은 `reliability`, provider 전송은 `runtime_ai`, 조사·위임 조합은 `reliability_ai`가 소유한다. 범용 SQL·경로 도구, 옛 package wrapper 복원, 과거 실행 기록 재작성, generic plugin·DI 계층과 신규 orchestrator는 이번 보완의 필수 범위가 아니다.

## Findings to Work Mapping

06의 F1~F3은 기존 delta spec과 미완료 과제 안의 접점이다. 새 capability나 별도 경쟁 체크리스트를 만들지 않고 원인을 소유하는 계획에 반영한다.

| Finding | Existing Tasks | Required Clarification |
| --- | --- | --- |
| F1. 현재 API와 정본 안내·Prompt 경로의 불일치 | 3·7, 각 실행 계약을 바꾸는 과제 | API·native Prompt·CLI·guide·가까운 테스트가 같은 계약을 가리키게 한다. 문서·consumer 이전을 최종 통합까지 미루지 않는다. |
| F2. Provider 입력 projection 우회 | 1·4 | 기존 bounded projection이 허용 자료의 의미를 소유하고 초기 메시지·Evidence 도구·원격 output이 이를 소비하게 한다. 실제 provider 메시지에서 비허용 자료 부재를 검증한다. |
| F3. 조사와 Recovery의 교차 입력 검증 공백 | 2 | 기존 execution 진입점이 사건·대상·partition·snapshot 일치를 검증한다. 충돌·복수 요청 시 executor 미호출을 확인하고 하위 Approval 의미는 복제하지 않는다. |

F3은 개별적으로 유효한 입력을 조합하는 문제이며, 무승인 mutation 우회가 입증됐다는 뜻은 아니다. 기존 F1~F6 보완 closure나 green CI도 이 세 접점과 최신 변경 전체의 검증을 대신하지 않는다.

## Work Sequence

아래는 기존 과제의 의존성과 구현 결과를 보강할 안이다. 상세 Requirement·Scenario의 owner는 기존 delta spec이며, 각 과제는 미충족 Scenario의 실패를 먼저 확인하고 같은 focused 검사로 구현을 검증한다. 선행 코드를 사후에 test-first 수행으로 기록하거나 assertion을 약화하지 않는다.

| Order | Existing Tasks | Ownership and Work | Exit Evidence |
| --- | --- | --- | --- |
| 1 | 1·2. 조회·실행 경계 | `context.py`의 기존 projection이 provider 자료 정책을 소유하고 registry·조사 loop가 소비한다. `execute_delegated_task`는 조사 입력·Task·approved request의 교차 검증을 소유한다. | 실제 profile 수치·snapshot 출처와 current dbt projection을 구별한다. 실제 provider 메시지에 비허용 payload·개인 경로가 없고, 불일치·복수 요청·조사 실패에서 executor가 호출되지 않는다. |
| 2 | 3. Native Prompt | 공통 `investigate_incident` 경로에 한국어 seed·native composition·시작 시 객체와 실제 버전 고정을 연결한다. | API·위임·CLI가 같은 경로를 사용한다. Lookup 실패 시 provider 0회, label 이동에도 같은 객체 사용, compile history·digest와 wheel seed 포함을 검증한다. Inline 실행 정본·local fallback을 남기지 않는다. |
| 3 | 4. 근거·관측 | 실제 provider 호출과 registry dispatch 구간에 관측을 연결하고 invocation·turn·로컬 저장의 연결을 완성한다. | Canonical facts와 모델 설명을 분리하고 raw-before-parse·remote-output 순서와 실패 근거를 보존한다. 실제 usage·attempt·latency·prompt·도구 출처가 연결되고 관측 장애는 재호출·성공 위장·metadata 유출을 일으키지 않는다. |
| 4 | 5. Dataset 실행 | 공통 조사·Prompt·관측 경로를 소비하는 직렬 native 실험을 연결한다. | Dataset item ID multiset과 결과가 일치하고 누락·중복·실패는 nonzero다. Trusted dbt pair·실행 예산·실제 version과 revision을 보존하며 oracle 유출과 반복 실행의 원격 setup 부작용이 없다. |
| 5 | 6. 실제 평가 | 같은 Dataset version·사례·model·rubric에서 실제 실행한 baseline/candidate를 비교한다. | 16K 우선의 실제 실행 조건·도구 결과·실패·원격 trace audit을 남긴다. 사람 평가 또는 미평가 상태를 명시하고 미평가를 품질 채택으로 기록하지 않는다. |
| 6 | 7. 정본·최종 통합 | 각 과제와 함께 진행한 guide·consumer 이전을 마무리하고 검증된 delta·두 Purpose를 canonical Spec에 반영한다. | 최신 base/head의 관련 회귀·전체 non-resource suite·type·Ruff·format·Tach·Spec·Markdown 결과와 정확한 미충족 범위를 남긴다. 개발 협업 근거와 제품 모델 품질을 분리한다. |

Task 1의 profile은 사건 snapshot 조회이지 live DB 재프로파일링이 아니다. Dbt는 trusted artifact pair를 기존 shared lock·projection identity·impact API로 읽고 current 관측임을 표시한다. 빈 downstream은 분석이 증명하지 않은 no-impact로 승격하지 않는다.

Task 2는 기존 authoritative executor·exact Approval·stale 검사·재검증·멱등성·reconciliation을 유지한다. 실제 domain result에 따른 성공·실패·부분 변경과 `not_reported`를 구별하며, 하위 API가 보고하지 않은 mutation 상태를 추측하지 않는다. 하위 Recovery의 별도 상태 보고 문제는 범위를 자동 확대하지 않고 dependency 후속으로 구분한다.

Task 6은 기존 원격 Prompt·Dataset inventory와 등록 부작용을 확인한 뒤 수행한다. RTX 3070 8GB에서 Qwen3.5 4B의 16K context를 우선하고 실제 `num_ctx`·출력 상한·thinking·VRAM·offload·지연·usage·도구 성공/실패를 기록한다. 32K는 16K 결과가 필요성과 자원 여유를 뒷받침할 때 별도 변수로 시험한다. 등록은 명시적 setup으로 분리하며 과거 Prompt·실행 identity를 재작성하지 않는다.

문서·consumer 이전은 각 실행 계약 변경과 함께 진행한다. Task 7이 마지막이라는 이유로 최종 통합 때 처음 연결하지 않는다. Canonical Spec 동기화는 검증된 계약을 대상으로 하고 archive를 자동 수행하지 않는다.

## Parallelization Conditions

파일 배정이나 agent 수가 아니라 공유 의미와 실제 수정 범위로 독립·생산자–소비자·결합 변경을 구분한다. 공통 계약이 바뀌면 아래 분류도 다시 판단한다.

| Work Pair | Relationship | Condition |
| --- | --- | --- |
| Task 1 조회와 Task 2 execution preflight | 조건부 독립 | `AgenticReviewInput`·snapshot identity·도구 결과·오류 의미를 먼저 고정한다. 입력 모델·공개 export·공유 테스트를 동시에 바꾸지 않고 각 owner 안에서 닫히는 경우만 병렬 후보로 둔다. |
| Profile handler와 dbt handler | 조건부 독립 | 공통 projection·schema·권한·provenance를 먼저 고정한다. 기존 registry의 등록·dispatch를 함께 수정해야 하면 한 owner가 통합하고 억지로 모듈을 나누지 않는다. |
| Task 3 Prompt와 Task 4 관측 | 결합 | 같은 investigation service와 실제 호출 구간을 바꾸므로 기본적으로 순차 처리한다. Seed·저장 내부처럼 공통 계약과 공유 파일을 바꾸지 않는 부분만 분리한다. |
| Task 4 실행 결과와 Task 5 Dataset consumer | 생산자–소비자 | 결과·실패·prompt·관측 연결 계약이 안정된 뒤 consumer를 완성한다. 각 테스트의 개별 green과 실제 합친 동작을 구분한다. |
| Domain Recovery 결과와 execution 보고 | 결합 | Mutation·reconciliation·오류 의미는 기존 domain owner가 결정한다. 실제 result를 wrapper에 연결한 성공·실패 검증 없이 독립 완료로 판정하지 않는다. |
| 구현과 guide·consumer 이전 | 동반 변경 | 공개 접점·타입·가까운 테스트만으로 계약을 발견할 수 있게 갱신한다. 기존 안내로 충분하면 새 index나 agent 전용 문서를 추가하지 않는다. |

공유 schema·상태·오류·쓰기 권한의 의미에는 한 owner를 둔다. 여러 작업이 같은 파일이나 의미를 변경해야 하면 좁은 순차 통합으로 드러낸다. Branch·worktree·agent 실행 순서의 운영은 별도 workflow이며 이 계획이 새 실행 체계를 요구하거나 agent를 실제로 배치한 것은 아니다.

## Verification and Collaboration Evidence

제품 검증은 가까운 기존 테스트에서 시작하고, 실제 provider 메시지·조사 loop·위임 보고·Dataset consumer의 연결까지 확인한다. 실패·비허용 입력·예산·저장·관측·부분 mutation 경계를 포함하되 offline green, `completed`, SDK 제출·flush 반환, 원격 재조회, 사람 평가를 서로 대체하지 않는다.

개발 아키텍처의 검증은 실제 대표 변경의 작업 기록에 다음 근거를 남긴다. 별도 benchmark 플랫폼이나 고정 수치 목표를 새로 요구하지 않는다.

| Evidence | Record |
| --- | --- |
| 독립 완료 범위 | 각 작업이 읽고 수정한 owner·공유 파일·계약, 로컬 검증 결과와 다른 작업의 미결정에 의존한 부분. |
| 계약 인계 | 생산자와 소비자가 합의한 I/O·오류·상태 의미 및 호환 여부. |
| 통합 정확성 | 개별 테스트와 별도로 실제 연결한 성공·차단·실패·재검증·보고 불변식의 검증 결과. |
| 충돌·재작업 | 텍스트 충돌과 의미적 충돌을 구분하고 계약 오해·중복 정책·통합 오류로 다시 고친 범위와 원인. |
| 총 변경 비용 | 비교 가능한 경우 탐색·조정·통합·재작업을 포함한 비용. Agent 모델·도구·task 조건이 다르면 구조 효과와 분리한다. |

현재는 실제 병렬 개발의 비용 감소나 재작업 감소를 입증한 자료가 없다. 이번 계획 정리도 협업 실험이나 제품의 라이브·사람 평가를 수행한 근거가 아니다.

## Proposed OpenSpec Revisions

새 계획을 병렬로 유지하지 않고, 채택한 내용은 다음 기존 산출물에 반영하는 안이다. 이 문서를 작성하는 것만으로 해당 반영을 승인받았거나 완료한 것으로 처리하지 않는다.

| Artifact | Proposed Revision | Preserved Boundary |
| --- | --- | --- |
| [Proposal](../../openspec/changes/reliability-agentic-review-enable-bounded-tools/proposal.md) | 제품 기능과 개발 에이전트의 독립 변경·정확한 통합을 동등한 목표로 명시하고 05·06 근거를 연결한다. | Intent·scope·impact만 소유한다. 작업 순서나 review process를 넣거나 새 capability를 만들지 않는다. |
| [Design](../../openspec/changes/reliability-agentic-review-enable-bounded-tools/design.md) | D2에 provider 자료 정책의 단일 소유와 실제 도구 경로의 소비 관계를, D5에 execution 교차 입력 검증의 소유권을 명확히 한다. | 기술적 책임과 이전 선택만 소유한다. 새로운 동작·완료 기준을 발명하거나 generic 공통 계층을 추가하지 않는다. |
| [Tasks](../../openspec/changes/reliability-agentic-review-enable-bounded-tools/tasks.md) | 기존 7개 과제에 의존성·조건부 병렬화·실제 연결 검증·동반 문서 이전·개발 협업 근거를 구체화한다. | 기존 번호와 미완료 상태 0/7을 유지한다. Review·승인 대기를 새 구현 과제로 만들지 않는다. |
| Delta specs | 현재 F1~F3을 이미 포괄하므로 이번 보강만을 위한 수정은 제안하지 않는다. | 이후 새 observable behavior가 필요해지면 Design·Tasks에 숨기지 않고 해당 Spec에서 먼저 합의한다. |

## Next Action

다음 단계는 위 세 planning artifact의 구체적인 변경안을 확인받아 기존 Change에 반영하는 것이다. 그 뒤 구현 요청을 받으면 기존 spec-driven-tdd 적용 절차에 따라 Task 1·2의 미충족 Scenario부터 진행한다. 이 문서는 제품 구현·정본 동기화·원격 자산 변경을 시작하라는 지시가 아니다.

최종 전달에는 실제 조회 연동과 이후 변경을 포함한 정확한 상태의 독립 리뷰, 05가 지적한 오래된 PR 본문의 갱신, 최신 head/base에 근거한 readiness 판단도 남아 있다. 과거 closure·CI 성공만으로 전체 acceptance나 Ready/merge를 선언하지 않으며 PR 상태 변경과 병합은 별도 권한을 따른다.
