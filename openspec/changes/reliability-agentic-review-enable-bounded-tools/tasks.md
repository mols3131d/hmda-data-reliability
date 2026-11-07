---
type: openspec-spec-driven-tdd-tasks
category: tasks
title: Bounded Investigation Migration Tasks
description: "선행 구현을 재검증하고 사건 범위 도구·위임·native Prompt·평가와 정본 이전을 완성한다."
tasks_completed: 0
tasks_total: 7
---

## Prerequisites

[Investigation Delta](specs/reliability-agentic-review/spec.md), [Prompt Delta](specs/review-ai-prompt-engineering/spec.md)와 [Design](design.md)을 적용 기준으로 사용한다. 이 Change 작성 이전의 구현은 완료로 소급 집계하지 않는다. 행동 변경은 미충족 Scenario의 실패를 먼저 확인하고 구현 후 같은 focused 검사를 다시 실행한다. 기존 통과 Scenario는 assertion을 약화하지 않고 회귀 근거로 사용한다.

## Tasks

- [ ] 1. 사건 snapshot과 current artifact를 구분하는 실제 조회 gateway를 완성한다.
  - **Covers:** Bounded incident tools; Canonical provider input projection; Design D2·D3.
  - **Test first:** 원본 nested payload 변경, 비허용 Evidence 필드·column·asset·path 인자, 미연결 handler, artifact 누락과 빈 downstream의 의미를 기존 도구 테스트에서 고정한다.
  - **Done when:** 기본 registry가 snapshot profile의 실제 수치와 출처를 반환하고, trusted artifact pair만 기존 shared lock·projection identity·impact API로 조회한다. Provider 자료에는 allowlist 밖 payload·개인 절대 경로가 없고 빈 목록을 검증된 no-impact로 표현하지 않는다. 조사·위임·실험의 trusted caller 접점과 기존 테스트에 연결되며 touched 파일의 Ruff·format 검사가 통과한다.

- [ ] 2. Task와 복구 요청의 사건 일치 및 실제 실행 보고를 완성한다.
  - **Covers:** Delegated task limits and recovery reporting; Advisory and read-only boundary; Design D5.
  - **Test first:** 다른 incident·target·partition의 approved request, 두 복구 요청 동시 제공, 충돌하는 snapshot refs와 조사 실패에서 executor가 호출되지 않는 검사를 추가한다.
  - **Done when:** preflight가 충돌을 차단하고 Task/caller의 도구 교집합·최소 예산을 적용한다. 기존 authoritative executor·Approval을 유지하며 성공·freshness 실패·부분 mutation·reconciliation·미보고 상태를 실제 domain result와 구분 가능한 ReportEnvelope로 보존한다.

- [ ] 3. 조사용 native Prompt lifecycle을 공통 실행에 연결한다.
  - **Covers:** Prompt Delta의 변경된 모든 Requirement와 Bounded investigation instructions; Current review surface; Design D1·D4.
  - **Test first:** prompt lookup 실패 시 provider 호출 0회, 시작 후 label 이동에도 같은 객체 사용, native compile history·digest·한국어 지침·수치와 권한 경계를 offline native 객체로 검증한다.
  - **Done when:** 한국어 Markdown seed와 native composition을 명시적 setup에서 등록할 수 있고 API·위임·CLI가 시작에 고정한 실제 name/version을 사용한다. Inline system 실행 정본·local fallback·옛 package/설정 alias가 없고 배포 wheel에 필요한 seed가 포함된다. 기존 remote inventory의 확인과 새 이름 선택은 과거 Prompt version을 재작성하지 않는다.

- [ ] 4. Invocation provenance와 실제 모델·도구 관측을 연결한다.
  - **Covers:** Typed review result boundary; Local provider response retention; Investigation provenance and failure retention; Verified model IO observation linkage; Independent external evaluation IO.
  - **Test first:** canonical 수치와 다른 모델 facts, invalid/깊은 JSON, tool-call-only·빈 응답, 응답/manifest 쓰기 실패·충돌·late response 및 관측 장애를 기존 조사·저장 테스트에서 고정한다.
  - **Done when:** 실제 input·revision·prompt·설정·turn·usage·attempt·latency·도구 결과가 private create-only 근거로 연결되고 실패가 completed로 변하지 않는다. 실제 호출 구간의 generation/tool observation이 올바르게 중첩되며 local raw 저장이 원격 output보다 앞선다. 전송 장애는 모델 재호출·결과 변경을 일으키지 않고 credential·본문·개인 경로가 metadata에 자동 포함되지 않는다.

- [ ] 5. 반복 Dataset 실험의 완전성과 실행 조건 추적을 완성한다.
  - **Covers:** Native synthetic dataset experiments; Provider-compatible bounded invocation; Bounded investigation budgets; Design D1·D4.
  - **Test first:** SDK task exception 누락·중복 ID·invalid input·실패 결과·oracle 유출과 반복 실행 중 setup 호출이 없는 조건을 기존 실험 테스트에서 확인한다.
  - **Done when:** 기존 Dataset을 직렬 native task로 실행하고 전체 조사 결과와 실제 Dataset version·revision·model·prompt·예산을 보존한다. 결과 multiset이 일치하고 모든 항목이 completed일 때만 CLI가 성공한다. Trusted dbt pair와 명시적 실행 예산을 전달할 수 있고 반복 실행은 Prompt·Dataset·평가 자산을 생성하거나 변경하지 않는다. 실제 SDK 제출과 원격 확인은 별도 근거로 보고한다.

- [ ] 6. 실제 실행한 후보의 로컬 모델 비교 근거를 확보한다.
  - **Covers:** Deterministic investigation evaluation; 기존 Versioned human utility evaluation 및 Baseline and candidate utility comparison evidence.
  - **Done when:** 기존 Prompt·Dataset inventory와 등록 부작용을 먼저 확인하고, 같은 Dataset version·사례·model·rubric으로 실제 실행한 baseline/candidate만 비교한다. RTX 3070 8GB에서 Qwen3.5 4B의 16K context를 우선 시험하고 실제 num_ctx·출력 상한·thinking·VRAM·offload·지연·usage·tool 성공·실패를 기록한다. 32K는 16K 결과가 필요성과 자원 여유를 뒷받침할 때만 별도 변수로 시험한다. 보존한 trace를 원격 재조회해 audit하고, 다섯 기준의 native 사람 평가 또는 미평가 상태를 실제 작성자·근거와 구별한다. 사람 평가가 없으면 품질 채택을 완료로 기록하지 않는다.

- [ ] 7. 현재 계약·guide·consumer를 새 진입점으로 이전하고 통합 근거를 확보한다.
  - **Covers:** Current review surface; Deterministic investigation evaluation; Proposal Impact와 Design Migration Strategy.
  - **Done when:** 검증된 delta를 canonical Spec에 동기화하고 두 Purpose도 실행 계약과 일치시킨다. Architecture·domain map·도메인/평가/개발 guide·현재 consumer·CLI 예시는 새 경로를 가리키며 과거 실행 기록은 보존한다. 필요한 index는 native 도구로 재생성한다. 관련 deterministic 도메인·AI/runtime·consumer·실패 회귀와 최신 base/head의 전체 non-resource suite, type·Ruff·format·Tach·Spec·Markdown 검사가 통과하거나 정확한 미충족 근거가 남는다. 개발 에이전트의 실제 독립 변경·계약 충돌·통합 오류·재작업 증거는 제품 모델 품질과 별도로 기록한다.
