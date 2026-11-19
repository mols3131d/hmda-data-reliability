---
type: openspec-spec-driven-tdd-design
category: design
title: HMDA Ingestion Investigation Design
description: LangGraph 조사 상태, 원천 검사 재사용, 실행 근거 읽기와 오프라인 재현의 구현 경계를 정합니다.
---

## Technical Delta

[제안서](proposal.md)와 [적재 조사 명세](specs/reliability-ai-ingestion-investigation/spec.md)를 선행 계약으로 사용한다. [워크플로우 도식](../../../inbox/github-291-build-ingestion-agent-harness/02-proposal-ingestion-llmops/architecture-plan.md)은 설계 참고 자료다.

### D1. Investigation State and Provider Contract

- **Decision:** `hmda_reliability.reliability_ai.ingestion`에 로컬 `investigate_ingestion` 진입점을 둔다. 준비 모드는 신뢰된 `DataOperationRequest`, 사후 모드는 허용된 실행 참조와 선택적 이전 조사 ID를 받는다. LangGraph의 상태에서 필수 검사 판정과 다음 조치의 결정 여부를 별도 값으로 관리한다.
- **Decision:** LangChain Core의 모델·메시지 계약을 기존 OpenAI-compatible Runtime AI loop와 별개로 구현할 provider interface에 연결한다. Codex App Server adapter를 ChatGPT 구독 OAuth 기반 첫 로컬 제공자로 검증하고, Ollama adapter도 같은 구조화 제안 계약을 반환하게 한다. `langchain-core`를 직접 import하므로 프로젝트 dependency로 선언한다.
- **Rationale:** 기존 Python investigation loop와 단일 chat-completions adapter는 Codex 구독 OAuth를 제공자 선택지로 표현하지 못한다. 먼저 incident investigation의 provider interface와 graph execution을 교체하고, 이 Change의 ingestion 조사에서 해당 경계를 사용한다. Adapter는 제공자별 요청·응답·중단을 맡고 LangGraph는 허용 도구, 순서와 조사 종료를 관리한다. [런타임 선택](../../../inbox/github-291-build-ingestion-agent-harness/01-report-llmops-runtime-selection.md), [Codex 제공자 설계](../../../inbox/github-291-build-ingestion-agent-harness/04-design-runtime-ai-codex-oauth-provider.md)

### D2. Captured Source and Shared Read Path

- **Decision:** 식별 가능한 고정 사본을 재사용하고, 변경 가능한 입력은 허용된 파일을 원래 상대 이름으로 로컬에 캡처한다. 상대 이름과 파일별 SHA-256의 정렬 목록을 정규 JSON으로 직렬화해 입력 버전을 만든다. 원천 ID는 캡처된 승인 파일에만 매핑한다.
- **Decision:** HMDA Data 내부의 원천 파서와 파티션 필터를 적재와 조회가 공유하게 한다. 사전 검사는 격리된 임시 DuckDB에 대상 행을 읽고, 실제 적재기에 전달되는 전체 파일의 필수 열과 요청 연도·파일의 대상 행을 확인한다.
- **Trade-off:** 원천 사본을 확보하거나 파싱하는 데 시간이 들 수 있다. 완료한 검사는 해당 버전의 근거로 재사용하고, 호출 예산에 맞춰 미확인 범위를 인계한다. [파일별 구조 검사](../../../src/hmda_reliability/hmda_data/ingestion/_common.py), [파티션 필터와 검사](../../../src/hmda_reliability/hmda_data/ingestion/partition.py)

### D3. Airflow Result Reader

- **Decision:** 조사 쪽 읽기 어댑터에서 Airflow 공개 REST API의 태스크 인스턴스를 조회한다. `raw_load`, `quality_gate`, `dbt_build`를 기존 DAG의 세 태스크 ID에 매핑한다. stage state는 `dag_id`, `run_id`, `task_id`, `map_index`, `try_number`로 식별하며, 추가 증거는 같은 시도로 연결할 수 있을 때 결합한다.
- **Rationale:** 현재 DAG는 XCom 저장을 끄고 성공한 적재의 asset 기록에 결과 일부를 남긴다. 기본 asset 기록에서 시도와 실제 원천 버전을 함께 얻을 수 없는 경우 명세의 미확인 결과를 적용한다. [Airflow DAG](../../../src/hmda_reliability/orchestration/dags/hmda_data_plane.py)

### D4. Local Records and Replay Clock

- **Decision:** 새 그래프 실행 기록은 조사 ID에 입력·버전·기한을 기록하고 각 모델·도구 호출의 시작과 반환을 연결한다. 오프라인 재현은 별도 실행 ID에서 저장된 응답·관찰값·시간 흐름을 재현용 provider와 tool port로 공급해 같은 그래프를 실행한다. 기존 저장 구현은 비공개 원자적 저장 성질을 재사용할 수 있지만 기존 investigation service나 실행 loop에 의존하지 않는다.
- **Rationale:** Codex App Server와 Ollama는 중단 및 응답 완료 방식을 서로 다른 transport 계약으로 제공한다. 공통 기록에는 adapter 종류, 호출 시도와 실제 반환 시각을 포함하고, 조사 기한을 넘긴 응답은 판정에 반영하기 전에 종료한다. [Codex 중단 계약](../../../inbox/github-291-build-ingestion-agent-harness/04-design-runtime-ai-codex-oauth-provider.md)

### D5. Langfuse Prompt and Observation Linkage

- **Decision:** 현재 `langfuse==4.15.6` 경로를 사용한다. 모델 분기의 첫 진입에서 프롬프트 버전을 확인하고 버전과 호출 ID를 로컬 기록에 묶는다. 로컬 결과가 기록되면 같은 조사 ID의 관측 결과와 전송 오류를 별도 기록으로 남긴다.
- **Rationale:** 로컬 판정의 재현과 원격 제출은 서로 다른 실패 경계를 가진다. 기존 관측 투영을 재사용하면 합성 입력 허용 여부와 외부로 보내는 필드를 일관되게 적용할 수 있다. [Reliability AI 관측 절차](../../../docs/development/review-ai-evaluation.md)
