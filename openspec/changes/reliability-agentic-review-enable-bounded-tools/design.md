---
type: openspec-spec-driven-tdd-design
category: design
title: Bounded Investigation Migration Design
description: "기존 조사 루프·Runtime adapter·artifact primitive를 재사용하는 이전과 native Prompt·관측의 연결 방식을 정한다."
---

## Technical Delta

[Proposal](proposal.md)과 [Investigation Delta](specs/reliability-agentic-review/spec.md), [Prompt Delta](specs/review-ai-prompt-engineering/spec.md)를 prerequisite로 사용한다.

### D1. Keep One Invocation Path

- **Decision:** 기존 `investigate_incident`를 공통 실행으로 유지하고 `execute_delegated_task`와 Dataset task가 이를 소비한다. Provider SDK 호출은 `runtime_ai.OpenAICompatibleAdapter`에 남긴다. 별도 실험용 loop·SDK adapter·멀티에이전트 프레임워크를 추가하지 않는다.
- **Rationale:** 현재 도구 이력·예산·원문 저장·failure 정규화를 한 경로에서 수정할 수 있다. Langfuse 의미는 `reliability_ai`에서 연결해 provider-neutral Runtime에 역의존을 만들지 않는다.

### D2. Bind Tool State at Registry Construction

- **Decision:** `ToolRegistry.from_review_input`에서 입력을 재검증·복사하고 canonical profile Evidence를 고정한다. Profile 비교는 저장된 baseline/current 수치를 읽으며 live profiling이나 DB connection을 요구하지 않는다. Provider 자료의 허용 필드·제한·출처 의미는 기존 `context.py`의 bounded projection이 소유한다. 초기 자료·Evidence 도구 응답·원격 output projection은 이 정책을 소비하고, registry·조사 loop가 별도 payload 정책이나 원본 전달 경로를 만들지 않는다. 도구가 추가한 current 관측도 이 owner의 bounded output 정책으로 연결하되 원입력 snapshot과 출처를 구분한다.
- **Rationale:** 범용 handler 확장은 trusted caller용으로 유지하되 기본 경로는 사건 snapshot만 소비한다. Snapshot 복사·도구 인자 검증·byte 한도는 허용 자료의 의미를 대신하지 않는다. 공유 정책의 변경이 실제 provider 메시지까지 전달되게 하며 generic projection 계층이나 중복 정책 모델을 추가하지 않는다.
- **Trade-off:** 기본 profile 도구는 새로 프로파일링한 현재 상태를 증명하지 않는다. Output provenance의 snapshot 구분이 이 제한을 설명한다.

### D3. Reuse the Artifact Projection Boundary

- **Decision:** trusted caller가 전달한 manifest/run-results pair를 사용하고, 같은 projection directory의 shared lock 안에서 기존 `artifact_projection_id`와 deterministic impact API를 호출한다. 모델 인자는 incident asset으로 제한한다. Artifact identity와 내부 경로는 로컬 근거에 보존하되 provider·원격 output projection에서는 개인 절대 경로를 제외한다.
- **Rationale:** 해시 계산과 분석 사이의 기존 promotion race를 같은 reader boundary로 제한할 수 있다. Path 문자열만으로 불변 snapshot임을 주장하거나 AI 도구에서 dbt graph 분석을 다시 구현하지 않는다.
- **Trade-off:** 기존 analyzer의 빈 downstream은 asset 미해결과 실제 leaf를 구분하지 않는다. Gateway는 이 한계를 드러내고 빈 목록만으로 no-impact를 확정하지 않도록 한다. 독립적인 graph 모델 변경은 이 이전에 끼워 넣지 않는다.

### D4. Pin Native Prompts and Observe Real Work

- **Decision:** 한국어 Markdown seed는 현재 prompt package를 재사용하고, 조사용 chat prompt는 과거 세 단계 prompt와 구분되는 이름으로 명시적 setup에서 등록한다. 정확한 이름은 기존 remote inventory와 충돌 여부를 확인한 후 고정한다. 서비스는 invocation 시작에 native 객체를 로드하고 모든 turn을 같은 객체와 history placeholder로 compile한다. Offline tests는 remote lookup 경계에 고정 native prompt 객체를 주입한다.
- **Rationale:** 현재 service의 inline system 문자열을 실행 정본으로 남기거나 과거 Prompt version을 재작성하지 않으면서 기존 native lifecycle을 유지할 수 있다.
- **Decision:** 실제 adapter 호출 구간에 generation, 실제 registry dispatch 구간에 tool observation을 조사 단위 아래 연결한다. Credential이나 전체 설정의 자동 인자 캡처는 사용하지 않는다. 로컬 원문 저장 후 관측 output을 갱신하며 SDK 전송 실패는 로컬 결과와 분리한다.
- **Rationale:** 기존 adapter와 로컬 store를 유지하면서 각 turn의 실제 메시지·도구·usage를 추적할 수 있다. 사후 manifest 재생으로 호출 시간을 합성하지 않는다.

### D5. Preserve Caller-Owned Recovery Requests

- **Decision:** 기존 `execute_delegated_task`가 조사 입력·Task·caller의 approved request를 조합하는 preflight를 소유한다. 이 경계에서 Task snapshot refs와 조사 Evidence identity, 제공된 request의 incident·target·partition을 대조하고 Backfill과 schema request가 함께 제공되면 선택하지 않는다. Exact proposal Approval·stale 검사·mutation·재검증·reconciliation 의미는 기존 deterministic domain이 계속 소유하며 wrapper에 복제하거나 AI 역의존을 만들지 않는다. 기존 domain executor와 그 request·Approval 계약은 변경하지 않는다.
- **Rationale:** 각 입력의 개별 유효성과 조합의 대상 일치를 구분해 조사한 사건과 별개 복구를 하나의 보고에 묶거나 `if/elif` 순서로 암묵 선택하는 일을 막는다. Wrapper receipt는 실제 domain result의 소비자이며 authoritative receipt나 mutation 상태의 새 owner로 재정의하지 않는다.

### Migration Strategy

- Worktree의 선행 구현·회귀 결과는 적용의 입력 자료다. 새 Change 생성 이전 작업을 test-first 또는 이 계획에 따른 작업으로 소급 기록하지 않고, 적용 시 미충족 Scenario부터 실패 재현과 구현을 연결한다.
- Package 이전은 한 번의 breaking migration으로 처리한다. 유지할 입력 데이터 계약 외에 옛 package·실행 모드·설정 alias를 추가하지 않는다. 현재 guide·CLI·consumer는 같은 변경에서 새 경로로 옮기고 과거 실행 자료는 그대로 둔다.
- 기존 Langfuse Dataset·Prompt inventory를 읽기 전용으로 확인한 뒤 필요한 등록만 명시적으로 수행한다. 반복 experiment는 기존 Dataset을 사용하며 baseline/candidate의 실제 코드·prompt revision을 유지한다.
- Canonical Spec의 Purpose는 delta merge만으로 바뀌지 않으므로 적용 시 두 Spec의 Purpose도 새 계약과 일치시킨다. Archive는 이 변경안의 자동 후속 작업으로 수행하지 않는다.
