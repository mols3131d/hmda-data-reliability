---
type: openspec-spec-driven-tdd-tasks
category: tasks
title: Bounded Investigation Migration Tasks
description: "기존 7개 과제의 계약 소유권·의존성을 고정하고 조회·위임·native 평가·정본 이전과 개발 협업의 연결 근거를 완성한다."
tasks_completed: 7
tasks_total: 7
---

## Prerequisites

[Proposal](proposal.md)의 두 목표와 [Investigation Delta](specs/reliability-agentic-review/spec.md), [Prompt Delta](specs/review-ai-prompt-engineering/spec.md), [Design](design.md)을 적용 기준으로 사용한다. 이 Change 작성 이전의 구현은 완료로 소급 집계하지 않는다. 행동 변경은 미충족 Scenario의 실패를 먼저 확인하고 구현 후 같은 focused 검사를 다시 실행한다. 기존 통과 Scenario는 assertion을 약화하지 않고 회귀 근거로 사용한다.

실제 구현·실험·독립 확인과 사람 인계 근거는 [Continuation Evidence](../../../inbox/github-284-evolve-reliability-agentic-architecture/05-report-reliability-agentic-progress-and-remaining-work.md)에 있다. 사람의 품질 평가는 미평가이며 후보 Prompt를 채택하지 않았다. Task 완료는 그 평가나 commit·push·Ready·merge·archive를 대신하지 않는다.

## Dependencies and Ownership

공유 I/O·snapshot identity·오류·상태 의미의 owner를 먼저 정하고 consumer가 같은 계약을 사용하게 한다. 파일이나 agent 수로 독립성을 가정하지 않으며, 공유 계약·파일을 바꿔야 하면 좁은 순차 통합으로 처리한다. 새 branch·worktree 운영이나 agent 배치는 이 계획의 구현 결과가 아니다.

| Tasks | Relationship and Order | Ownership and Parallel Condition |
| --- | --- | --- |
| 1·2 | 공유 입력 계약 고정 후 조건부 독립 | Provider 자료 정책은 기존 context projection, 교차 입력 일치는 execution 진입점이 소유한다. 입력 모델·공개 export·공유 테스트를 동시 변경하지 않고 각 owner 안에서 끝날 때만 병렬 후보로 둔다. |
| 1의 profile·dbt handler | 공통 projection·schema·권한·provenance 고정 후 조건부 독립 | Registry 등록·dispatch까지 함께 바꾸면 한 owner가 통합한다. 병렬화를 위해 새 계층이나 모듈을 만들지 않는다. |
| 3·4 | 조회·결과 계약을 바탕으로 3 이후 4 | 같은 investigation service와 실제 호출 구간을 바꾸므로 기본적으로 순차 처리한다. 공유 계약·파일을 바꾸지 않는 seed·저장 내부 작업만 분리할 수 있다. |
| 4·5·6 | 실행 결과 생산자 이후 Dataset consumer, 그 뒤 실제 평가 | 5는 공통 Prompt·관측·결과·실패 계약을 소비한다. 6은 3~5의 연결 검증 뒤 수행하며 개별 green을 실제 연결 성공이나 품질 채택으로 대체하지 않는다. |
| 7 | 각 계약 변경에 동반하며 최종 통합에서 마무리 | Guide·CLI·consumer·가까운 테스트를 해당 과제와 함께 이전한다. 검증된 delta의 정본 반영과 전체 일치 확인을 마무리하며 최종 단계에서 처음 연결하지 않는다. |

Recovery 결과와 wrapper 보고는 결합 변경이다. Mutation·재검증·reconciliation·오류 의미는 기존 domain이 소유하고 execution은 실제 결과를 소비한다. 이 의미를 바꿔야 하면 별도 범위 판단 없이 하위 API까지 자동 확대하지 않는다.

## Tasks

- [x] 1. 사건 snapshot과 current artifact를 구분하는 실제 조회 gateway를 완성한다.
  - **Covers:** Bounded incident tools; Canonical provider input projection; Design D2·D3.
  - **Test first:** 원본 nested payload 변경, 비허용 Evidence 필드·column·asset·path 인자, 미연결 handler, artifact 누락과 빈 downstream의 의미를 기존 도구 테스트에서 고정한다. Fake provider와 실제 registry를 연결한 조사 loop에서 초기·후속 메시지의 비허용 필드·개인 경로 부재를 확인한다.
  - **Done when:** 기본 registry가 snapshot profile의 실제 수치와 출처를 반환하고, trusted artifact pair만 기존 shared lock·projection identity·impact API로 조회한다. 기존 context projection이 provider 자료의 의미를 소유하며 실제 초기·tool 메시지와 원격 output projection에 allowlist 밖 payload·개인 절대 경로가 없다. 빈 목록을 검증된 no-impact로 표현하지 않는다. 조사·위임·실험의 trusted caller 접점과 기존 테스트에 연결되며 touched 파일의 Ruff·format 검사가 통과한다.

- [x] 2. Task와 복구 요청의 사건 일치 및 실제 실행 보고를 완성한다.
  - **Covers:** Delegated task limits and recovery reporting; Advisory and read-only boundary; Design D5.
  - **Test first:** 다른 incident·target·partition의 approved request, 두 복구 요청 동시 제공, 충돌하는 snapshot refs와 조사 실패에서 executor가 호출되지 않는 검사를 추가한다.
  - **Done when:** execution 진입점의 preflight가 충돌을 차단하고 Task/caller의 도구 교집합·최소 예산을 적용한다. 기존 authoritative executor·Approval을 유지하며 성공·freshness 실패·부분 mutation·reconciliation·미보고 상태를 실제 domain result와 구분 가능한 ReportEnvelope로 보존한다. 기존 domain 결과를 실제 연결한 성공·차단·실패 검증으로 조사 사건·실행 대상·보고 참조의 일치를 확인하고, executor mock의 개별 green만으로 조합 완료를 판정하지 않는다.

- [x] 3. 조사용 native Prompt lifecycle을 공통 실행에 연결한다.
  - **Covers:** Prompt Delta의 변경된 모든 Requirement와 Bounded investigation instructions; Current review surface; Design D1·D4.
  - **Test first:** prompt lookup 실패 시 provider 호출 0회, 시작 후 label 이동에도 같은 객체 사용, native compile history·digest·한국어 지침·수치와 권한 경계를 offline native 객체로 검증한다.
  - **Done when:** 한국어 Markdown seed와 native composition을 명시적 setup에서 등록할 수 있고 API·위임·CLI가 시작에 고정한 실제 name/version을 사용한다. Inline system 실행 정본·local fallback·옛 package/설정 alias가 없고 배포 wheel에 필요한 seed가 포함된다. 기존 remote inventory의 확인과 새 이름 선택은 과거 Prompt version을 재작성하지 않는다.

- [x] 4. Invocation provenance와 실제 모델·도구 관측을 연결한다.
  - **Covers:** Typed review result boundary; Local provider response retention; Investigation provenance and failure retention; Verified model IO observation linkage; Independent external evaluation IO.
  - **Test first:** canonical 수치와 다른 모델 facts, invalid/깊은 JSON, tool-call-only·빈 응답, 응답/manifest 쓰기 실패·충돌·late response 및 관측 장애를 기존 조사·저장 테스트에서 고정한다. 실제 SDK의 비정상 도구 호출이 유효한 최종 본문과 함께 와도 성공으로 바뀌지 않고, 부분 도구 실행·재시도 없이 제한된 본문과 호출 원문을 로컬에 보존하는 생산자–소비자 연결을 검증한다.
  - **Done when:** 실제 input·revision·prompt·설정·turn·usage·attempt·latency·도구 결과가 private create-only 근거로 연결되고 canonical facts와 모델 narrative가 분리되며 실패가 completed로 변하지 않는다. 실제 호출 구간의 generation/tool observation이 올바르게 중첩되며 local raw 저장이 원격 output보다 앞선다. Task 1의 공통 projection을 거친 실제 도구 결과가 후속 모델 메시지·관측에 연결됨을 검증한다. 전송 장애는 모델 재호출·결과 변경을 일으키지 않고 credential·본문·개인 경로가 metadata에 자동 포함되지 않는다.

- [x] 5. 반복 Dataset 실험의 완전성과 실행 조건 추적을 완성한다.
  - **Covers:** Native synthetic dataset experiments; Provider-compatible bounded invocation; Bounded investigation budgets; Design D1·D4.
  - **Test first:** SDK task exception 누락·중복 ID·invalid input·실패 결과·oracle 유출과 반복 실행 중 setup 호출이 없는 조건을 기존 실험 테스트에서 확인한다.
  - **Done when:** 기존 Dataset을 직렬 native task로 실행하고 전체 조사 결과와 실제 Dataset version·revision·model·prompt·예산을 보존한다. 결과 multiset이 일치하고 모든 항목이 completed일 때만 CLI가 성공한다. Trusted dbt pair와 명시적 실행 예산을 전달할 수 있고 반복 실행은 Prompt·Dataset·평가 자산을 생성하거나 변경하지 않는다. 별도 실험 loop가 아닌 공통 조사·native Prompt·관측 경로를 소비함을 연결 검증한다. 실제 SDK 제출과 원격 확인은 별도 근거로 보고한다.

- [x] 6. 실제 실행한 후보의 로컬 모델 비교 근거를 확보한다.
  - **Covers:** Deterministic investigation evaluation; 기존 Versioned human utility evaluation 및 Baseline and candidate utility comparison evidence.
  - **Done when:** 기존 Prompt·Dataset inventory와 등록 부작용을 먼저 확인하고, 같은 Dataset version·사례·model·rubric으로 실제 실행한 baseline/candidate만 비교한다. RTX 3070 8GB에서 Qwen3.5 4B의 16K context를 우선 시험하고 실제 num_ctx·출력 상한·thinking·VRAM·offload·지연·usage·tool 성공·실패를 기록한다. 32K는 16K 결과가 필요성과 자원 여유를 뒷받침할 때만 별도 변수로 시험한다. 보존한 trace를 원격 재조회해 audit하고, 다섯 기준의 native 사람 평가 또는 미평가 상태를 실제 작성자·근거와 구별한다. 사람 평가가 없으면 품질 채택을 완료로 기록하지 않는다.

- [x] 7. 현재 계약·guide·consumer를 새 진입점으로 이전하고 통합 근거를 확보한다.
  - **Covers:** Current review surface; Deterministic investigation evaluation; Proposal Impact와 Design Migration Strategy.
  - **Done when:** 검증된 delta를 canonical Spec에 동기화하고 두 Purpose도 실행 계약과 일치시킨다. Architecture·domain map·도메인/평가/개발 guide·현재 consumer·CLI 예시는 새 경로를 가리키며 과거 실행 기록은 보존한다. 공개 API에서 계약·가까운 검증을 발견할 수 있고 기존 안내로 충분하면 새 index나 agent 전용 문서를 추가하지 않는다. 필요한 index는 native 도구로 재생성한다. 관련 deterministic 도메인·AI/runtime·consumer·실패 회귀와 최신 base/head의 전체 non-resource suite, type·Ruff·format·Tach·Spec·Markdown 검사가 통과하거나 정확한 미충족 근거가 남는다. 개발 에이전트의 실제 대표 변경이 읽고 수정한 owner·공유 파일·계약·로컬 검증·미결정 의존성, 생산자–소비자의 I/O·오류·상태 인계와 연결 검증을 기존 작업 기록에 남긴다. 텍스트 충돌과 의미적 충돌·통합 오류·재작업 범위 및 원인을 구별하며, 비교 가능한 경우 탐색·조정·통합·재작업을 포함한 총 비용과 agent·도구·task 조건을 기록한다. 이 근거는 제품 모델 품질과 분리하고 비교 자료 없이 비용 감소를 주장하지 않는다. 별도 benchmark 플랫폼이나 고정 수치 목표는 요구하지 않는다.
