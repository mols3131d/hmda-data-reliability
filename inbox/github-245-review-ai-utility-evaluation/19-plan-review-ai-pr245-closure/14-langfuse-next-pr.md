# 14 — Evaluate the Langfuse Follow-Up PR

이 작업은 PR #245가 실제로 `main`에 병합되고 13의 OpenSpec transition gate가 완료된 뒤에만 시작한다.

## Goal

현재 Review AI에서 실제로 남아 있는 **live observability와 human evaluation workflow의 마찰**을 확인하고, Langfuse가 그 마찰을 충분히 줄이는 경우에만 가장 작은 optional integration을 도입한다.

Langfuse 도입 자체가 목표가 아니다. Repository가 evaluation semantics, deterministic safety와 durable contract를 계속 소유하고, Langfuse는 필요성이 확인된 관찰·human annotation surface만 담당한다.

## Preconditions

1. PR #245 merge와 resulting `main` revision을 확인한다.
1. 13의 transition gate 결과를 확인하고 current canonical OpenSpec을 다시 읽는다.
1. 최신 `main`에서 새 branch와 Draft PR을 만든다. #245 branch를 재사용하지 않는다.
1. `CHATBOT.md`부터 applicable repository guidance를 다시 로드하고 current `docs/mvp.md`, canonical OpenSpec, `review_ai`/`runtime_ai` implementation과 tests를 다시 읽는다.
1. 이 Inbox의 type/field 이름을 보존하기 위한 compatibility abstraction을 만들지 않는다.

Working context로 과거 #245 Inbox를 참고할 수 있지만 current code/spec이 우선한다.

## Ownership Handoff

이 파일은 새 작업의 seed다. 새 Langfuse branch/PR이 생기면 planning, review와 durable working context는 그 새 work unit이 소유한다. 이 파일을 새 PR의 mutable status owner로 계속 갱신하지 않는다.

## Decision First

구현 전에 다음 세 질문에 답한다.

1. #245 이후에도 사람이 live invocation을 찾아 output과 provenance를 읽고 rubric score/rationale를 기록하는 과정에 material한 마찰이 남아 있는가?
1. Current Langfuse official Python/OpenTelemetry와 human annotation/score surface가 그 마찰을 custom platform보다 작은 비용으로 줄이는가?
1. Langfuse가 unavailable이어도 repository core와 deterministic validation을 그대로 유지할 수 있는가?

셋 중 하나라도 `no`이면 integration 범위를 줄이거나 도입을 중단한다.

## Boundaries

- Repository가 rubric identity, evaluation semantics, same-case invariant, deterministic safety와 MVP acceptance를 소유한다.
- Langfuse가 없거나 unavailable이어도 Review AI core, deterministic tests와 recovery path는 정상 동작해야 한다.
- Langfuse annotation/dashboard만으로 candidate 승인, recovery 또는 delegation authority를 변경하지 않는다.
- Repository prompt와 prompt identity를 canonical로 유지한다. 첫 PR에서 Langfuse Prompt Management로 runtime authority를 이전하지 않는다.
- Provider `trace_id`와 Langfuse trace/observation identity를 같은 의미로 재사용하지 않는다.
- Automatic LLM judge, Promptfoo, generic experiment platform, dataset registry와 production-grade self-host infrastructure를 도입하지 않는다.
- Credential, raw large payload, 전체 로그 또는 불필요한 evidence를 export하지 않는다.

## Minimum Work

### 1. Research the Supported Surface

현재 공식 문서를 기준으로 다음만 확인한다.

- Python/OpenTelemetry tracing의 최소 supported path
- trace/observation metadata와 stable application identity 연결 방법
- human rubric annotation/score와 rationale/comment 기록 방법
- completed annotation을 public supported API로 다시 읽을 수 있는지
- credential/redaction과 SDK/network failure behavior

Private API, scraping 또는 추측한 SDK behavior를 전제로 설계하지 않는다.

### 2. Prove Optional Trace Projection

Live invocation을 Langfuse trace/observation과 연결하는 최소 projection을 만든다. 새 canonical provenance schema를 만들지 않는다.

우선하는 identity는 repository가 이미 가진 값이다.

- `invocation_id`
- `project_revision`
- prompt identity/digest
- model과 sanitized configuration
- result/validation status
- output digest 또는 안정적인 output identity
- latency와 available usage

Evidence는 raw payload보다 identity/digest를 우선한다.

### 3. Prove Human Annotation Mapping

현재 canonical human rubric criterion과 score/rationale를 Langfuse human annotation surface에서 표현할 수 있는지 검증한다.

Langfuse가 요구하는 display description이나 score configuration은 integration projection으로 취급한다. Repository rubric semantics를 vendor schema에 맞춰 약화하거나 generic rubric engine을 만들지 않는다.

현재 rubric 의미가 실제 human evaluator에게 모호해 평가 재현성이 깨진다는 evidence가 있을 때만 canonical owner의 최소 설명 보강을 별도로 제안한다. Langfuse configuration 편의만으로 #245-era core schema를 확장하지 않는다.

## Conditional Work — Import Only if It Stays Small

Completed human annotation의 repository import는 첫 PR의 자동 필수 범위가 아니다. 다음 조건을 모두 만족할 때만 같은 PR에 포함한다.

- public supported API로 필요한 score/rationale와 trace identity를 읽을 수 있음
- existing repository evaluation contract가 가짜 identity나 vendor-specific field 없이 결과를 표현할 수 있음
- 별도 polling worker, generic synchronization framework 또는 새 storage architecture가 필요하지 않음
- import가 repository를 canonical evidence owner로 유지하는 데 실제 가치를 제공함

조건을 만족하면 **한 건의 completed evaluation을 one-way import**하고 exact invocation/output/revision/rubric identity mismatch를 fail-closed 한다.

조건을 만족하지 않으면 trace + human annotation까지만 첫 PR로 닫고 import는 별도 follow-up 판단으로 남긴다. 이를 해결하려고 미리 `output_fixture_id`를 optional로 만들거나 evaluation source/backend hierarchy를 추가하지 않는다.

## Do Not Pre-Build

다음은 실제 adapter가 요구하고 더 작은 대안이 없다는 evidence가 생기기 전에는 만들지 않는다.

- `EvaluationBackend`, `EvaluatorProvider` 같은 plugin protocol
- generic evaluation source/type hierarchy
- standalone human-score CLI/UI
- generic standalone evaluation store
- two-way sync or polling worker
- Langfuse ID를 core evaluation/invocation contract에 영구 추가하는 field
- dataset/experiment abstraction
- rubric configuration framework

## Validation

외부 서비스 없이 가능한 검증을 우선한다.

- Langfuse disabled 상태에서 기존 behavior 유지
- trace projection의 stable identity와 secret/raw-evidence exclusion
- Langfuse client/network failure isolation
- human rubric mapping이 선택되었다면 score/rationale 변환 검증
- import가 포함되었다면 wrong invocation/output/revision/rubric identity rejection

실제 Langfuse smoke는 opt-in으로 분리한다. 환경이 있으면 최소 live invocation 하나와 human annotation 흐름을 확인한다. 실행하지 못하면 PR Validation에 `⚪ Not Verified`로 기록한다.

## Acceptance

첫 PR은 실제 선택한 scope에 맞춰 acceptance를 선언한다. 최소 공통 조건은 다음이다.

- Langfuse 없이 기존 Review AI behavior와 tests가 유지됨
- live invocation을 repository identity로 Langfuse observation에 연결할 수 있음
- 사람이 current rubric score와 rationale을 실제 output에 연결해 기록할 수 있음
- secret/raw evidence leakage와 Langfuse failure가 repository result semantics를 오염시키지 않음
- 도입된 abstraction이 실제 integration에 필요한 최소 범위임
- current-head focused tests와 CI evidence가 존재함

Import를 포함했다면 추가로 completed annotation 한 건을 exact repository identity에 fail-closed하게 바인딩할 수 있어야 한다. Import를 포함하지 않았다면 그 부재를 실패로 취급하지 않고 이유와 후속 판단만 명시한다.

## Stop Conditions

다음 중 하나가 필요해지면 scope를 넓히지 않고 blocker와 더 작은 대안을 보고한다.

- Repository evaluation contract를 Langfuse schema에 맞춰 약화해야 함
- 단순 integration을 위해 #245-era core eval을 대규모 refactor해야 함
- production-grade self-host infrastructure가 필수임
- generic two-way synchronization, polling worker 또는 experiment platform이 필요함
- human annotation/import에 supported public API가 없고 private/unstable API 또는 scraping이 필요함
- Langfuse가 deterministic safety나 recovery path의 필수 dependency가 됨
- 얻는 human-eval workflow 이득보다 dependency/integration complexity가 큼
