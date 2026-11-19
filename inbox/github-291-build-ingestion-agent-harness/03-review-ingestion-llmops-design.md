---
type: review
title: Ingestion LLMOps Design Review
description: PR 291의 적재 조사 설계 번들을 검토하고, 구현 전에 정할 계약과 검증 과제를 정리합니다.
---

# Ingestion LLMOps Design Review

> [!IMPORTANT]
> **Revise (`changes_required`).** 시스템 간 역할과 조사 흐름은 잡혔다. `02` 번들에서 **모델에 맡길 업무, 준비 판정의 근거, 적재 결과를 연결하는 방법, 중단 뒤 재현하는 방식**을 구체화하면 구현에 들어갈 수 있다.

- **Target** — [02 적재 LLMOps 설계 번들](02-proposal-ingestion-llmops/README.md)
- **Revision** — 로컬 코드 `90bbbe66`, 작업 트리의 번들 문서 네 개. 번들 SHA-256 `16d8ebdaa51543cb895b5e1206aff20ca2d016d760fcb81947aa31fcb79493b6`.
- **Scope** — LangGraph·LangChain 기반 조사, 준비 판정과 읽기 전용 인계. 작업 트리 설계를 Draft PR `617aba04`의 목표 및 완료 조건과 대조했다. [PR #291](https://github.com/mols3131d/hmda-data-reliability/pull/291), [완료 조건](https://github.com/mols3131d/hmda-data-reliability/blob/617aba0434bed79273c55530f67bfc04189afffd/inbox/github-291-build-ingestion-agent-harness/01-plan-ingestion-agent-harness-mvp.md#acceptance)

## Findings

| ID | Severity | Finding | Action |
| --- | --- | --- | --- |
| F1 | 🟠 Major | 그래프에 규칙 판정 확정 뒤 후속 조치를 해석하는 분기가 빠져 있다. | 첫 조사의 업무와 모델 호출 조건, 호출자에게 넘길 결과를 정한다. |
| F2 | 🟠 Major | `ready`의 필수 검사와 실제로 읽은 파일 버전의 연결 방법이 비어 있다. | 검사별 증거와 `ready`·`blocked`·`needs_human` 판정표를 함께 정한다. |
| F3 | 🟠 Major | 조사 ID와 DAG 실행 ID만으로 조사 범위와 실제로 적재한 입력의 일치를 확인하기 어렵다. | 인계할 범위와 버전을 명시하고, 사후 보고에서 일치를 입증할 수 있는 기록을 고른다. |
| F4 | 🟠 Major | 재현에 사용할 기록과 기한이 지난 응답의 처리 기준이 빠져 있다. | 재현에 필요한 근거·버전과 재개 시 이어서 쓸 예산, 기한 경과 시 종료 동작을 정한다. |

F1·F4는 완료 조건을 구체화하는 항목(`acceptance_gap`)이고, F2·F3는 실행에 필요한 근거 계약(`contract_dependency`)이다. 네 항목 모두 `current_required`다.

## Details

### F1 · Select the First Workflow

- 그래프는 규칙 판정이 확정되면 결과 검증으로 이동한다. 위임 표는 사실을 모두 확보한 뒤에도 해석이나 다음 조치가 필요하면 모델을 호출한다. [조사 흐름](02-proposal-ingestion-llmops/architecture-plan.md#investigation-workflow), [위임 표](02-proposal-ingestion-llmops/decision-contract.md#delegation)
- 조사 시작 조건, 처음 제공할 근거, 모델이 조회를 고르는 조건, 호출자가 사용할 결과를 하나의 흐름으로 명시한다. 설계는 적재 조사 업무 전반에 적용하고, 여러 입력에서 다음 조회나 조치가 달라지는지를 검증한다. 인계에는 대상 범위, 근거 ID, 불확실성과 다음 조치를 담는다.

### F2 · Define Readiness Evidence

- 근거 스키마는 필수 검사를 모두 통과하면 `ready`를 반환한다. 현재 적재는 실행할 때 원천 목록을 다시 찾는다. 파티션 로더는 지정 연도·파일로 행을 고르고 입력으로 받은 전체 파일의 필수 열을 검사한다. [근거 스키마](02-proposal-ingestion-llmops/evidence-tool-schemas.md#evidence-and-failure), [현재 적재 진입점](../../src/hmda_reliability/data_operations/runner.py), [파티션 로더](../../src/hmda_reliability/hmda_data/ingestion/partition.py)
- **검사해야 하는 파일 집합과 적재할 행의 범위**를 명시한다. 파일별 구조, 파싱, 대상 행 확인에 각각 어떤 근거가 필요한지 정하고, 실제로 읽은 입력을 그 버전에 묶는 방법을 선택한다. 파일이 바뀌었거나 검사 범위 일부를 확인할 수 없으면 미확인으로 남긴다. `ready`는 이 범위의 원천 준비를 확인한 결과로 정의한다.

### F3 · Bind the Handoff to the Observed Run

- 설계는 예상과 실제의 차이를 보고한다. 현재 DAG는 XCom 저장을 끄고 성공 시 asset 기록에 연도·행 수 등을 남긴다. 그 요약에는 적재 파일 범위와 입력 버전이 빠져 있다. Bronze 커밋 뒤에 asset 기록을 남기므로 단계 상태와 실제 데이터 갱신을 각각 확인해야 한다. [시스템 흐름](02-proposal-ingestion-llmops/architecture-plan.md#system-workflow), [현재 DAG](../../src/hmda_reliability/orchestration/dags/hmda_data_plane.py)
- 읽기 전용 인계의 진입점과 받을 결과 형식을 정한다. 사후 조사를 첫 범위에 넣는다면 호출자가 읽을 실행·단계 기록과 타당한 시도 연결 방법을 정한다. 입력 일치를 확인할 수 있는 실행만 사전 판정과 대조하고, 연결이 불분명한 실행은 확인된 단계 상태와 부족한 근거를 보고한다.

### F4 · Specify Resume and Replay

- 체크포인트 계획에는 완료 기록을 재사용하고 완료가 불명확한 시도도 예산에 포함한다는 방침이 있다. 실제 Runtime AI는 기한을 넘겨 끝난 응답도 반환할 수 있다. 기존 Reliability AI는 응답을 보존한 뒤 기한을 검사하고, 기한이 지났으면 추가 조회로 넘어가기 전에 종료한다. [체크포인트 설계](02-proposal-ingestion-llmops/architecture-plan.md#state-and-recovery), [Runtime AI](../../src/hmda_reliability/runtime_ai/provider.py), [기존 조사 서비스](../../src/hmda_reliability/reliability_ai/investigation/service.py)
- 재현에는 기존 실행의 근거와 입력·모델·프롬프트 버전을 참조하고, 자료가 없으면 재현할 수 없는 이유를 남긴다. 같은 조사에서 중단 지점을 이어갈 때는 기존 ID와 남은 예산을 사용한다. 기한이 지난 응답은 기록하고 추가 조회나 판정에 반영하기 전에 종료한다.

저장소 구현과 구체적인 예산 수치는 이 동작을 기준으로 구현 단계에서 정할 수 있다. 실제 모델과 Langfuse 원격 조회를 연결한 뒤, 운영 채택 여부는 담당자의 조사 시간과 재조회 횟수로 판단한다. [채택 기준](02-proposal-ingestion-llmops/README.md#how-to-decide)

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | 번들 구조와 로컬 링크 | `rumdl check` 문서 4개, Inbox frontmatter 검사, 상대 링크 26개 |
| ✅ Pass | 검토 대상 및 기준 일치 | 로컬 문서 해시와 GitHub의 Draft PR head 확인 |
| ✅ Pass | 독립 검토 | 품질과 실패 경로를 별도로 검토하고, 후보를 문서·코드·명세에 대조 |
| ⚪ Not Verified | 실제 실행·재개·관측 | 설계에 대한 문서 및 소스 검토. 후보 구현에서 검증할 항목이다. |
