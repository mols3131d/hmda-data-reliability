# 14 — Start the Langfuse Follow-Up PR

이 작업은 PR #245가 실제로 `main`에 병합되고 13의 OpenSpec transition gate가 완료된 뒤에만 시작한다.

## Goal

Review AI의 repository-native evaluation contract를 유지하면서 Langfuse를 **optional live tracing + human evaluation workspace**로 도입한다.

첫 PR의 최소 목표는 다음 흐름을 실제로 연결하는 것이다.

```text
live Review AI invocation
        ↓
Langfuse trace
        ↓
human rubric annotation + rationale
        ↓
one-way import
        ↓
repository human evaluation
```

Langfuse는 관찰과 human annotation을 위한 working surface다. 평가 의미, deterministic guard, acceptance와 canonical evaluation evidence는 repository가 계속 소유한다.

## Preconditions

1. PR #245 merge와 resulting `main` revision을 확인한다.
1. 13의 transition gate 결과를 확인하고 current OpenSpec `specs/**`를 기준으로 상태를 다시 읽는다.
1. 최신 `main`에서 새 branch와 Draft PR을 만든다. #245 branch를 재사용하지 않는다.
1. `CHATBOT.md`부터 applicable repository guidance를 다시 로드하고 현재 `docs/mvp.md`, canonical OpenSpec, `review_ai`/`runtime_ai` 구현과 tests를 다시 읽는다.
1. #245 이후 evaluation model이 단순화·변경되었으면 현재 canonical contract에 맞춘다. 이 Inbox의 오래된 type을 보존하기 위한 compatibility abstraction을 만들지 않는다.

Working context는 `12-proposal-review-ai-utility-evaluation-remediation-and-simplification.md`, `13-report-review-ai-hands-on-evaluation-guide.md`, `18-review-review-ai-high-confidence/README.md`를 historical context로 참고할 수 있다. Inbox와 current code/spec이 충돌하면 canonical source를 따른다.

## Ownership Handoff

이 파일은 새 작업을 시작하기 위한 seed다. 새 Langfuse branch 또는 PR이 생기면 active planning, review와 durable working context는 그 새 work unit의 Inbox가 소유한다. 이 파일을 새 PR의 mutable status owner로 계속 갱신하지 않는다.

## Boundaries

- Repository가 rubric, evaluation semantics, same-case invariant, deterministic safety와 MVP acceptance를 소유한다.
- Langfuse가 없거나 unavailable이어도 Review AI core, deterministic tests와 recovery path는 정상 동작해야 한다.
- Langfuse annotation/dashboard만으로 candidate 승인, recovery 또는 delegation authority를 변경하지 않는다.
- Repository prompt와 prompt identity를 canonical로 유지한다. 첫 PR에서 Langfuse Prompt Management로 runtime authority를 이전하지 않는다.
- Automatic LLM judge, Promptfoo, generic experiment platform과 production-grade Langfuse self-host infrastructure를 도입하지 않는다.
- Credential, raw large payload, 전체 로그 또는 불필요한 evidence를 export하지 않는다.
- Langfuse failure를 Review AI provider result나 deterministic validation 결과로 재분류하지 않는다.

## Work

### 1. Research the Current Integration Surface

현재 Langfuse 공식 문서를 기준으로 Python SDK/OpenTelemetry tracing, human annotation/score API, credential/redaction과 failure behavior를 조사한다. 아래 목표를 만족하는 가장 작은 supported path를 선택한다.

### 2. Add an Optional Live Trace Projection

기존 live invocation provenance를 새 canonical schema로 복제하지 말고 Langfuse에 필요한 최소 projection만 보낸다. 최소 identity는 `invocation_id`, `project_revision`, prompt identity/digest, model/sanitized configuration, result/validation status, output identity/digest, latency와 available usage다. Evidence는 raw payload보다 identity/digest를 우선한다.

### 3. Map Human Rubric Annotation

현재 canonical human rubric의 criterion을 Langfuse annotation surface에 매핑하고 score와 rationale/comment를 함께 보존한다. Langfuse schema가 repository contract와 다르면 repository model을 약화하지 말고 integration boundary에서 변환한다.

### 4. Import One Completed Evaluation

양방향 synchronization framework를 만들지 않는다. 완료된 human annotation 한 건을 읽어 exact invocation/output/revision/case/rubric identity에 묶인 repository evaluation으로 **one-way import**한다. Identity가 맞지 않으면 fail-closed 한다.

Baseline/candidate comparison 로직 자체는 재설계하지 않는다. Imported evaluation이 기존 canonical comparison input으로 사용될 수 있으면 충분하다.

### 5. Verify without an External Service

Fake/stub client로 다음을 검증한다.

- Langfuse disabled 상태에서 기존 behavior 유지
- trace projection의 identity와 secret/raw-evidence exclusion
- rubric score+rationale의 lossless conversion
- wrong invocation/output/revision/rubric import rejection
- Langfuse client/network failure isolation

실제 Langfuse smoke는 opt-in으로 분리한다. 환경이 있으면 live invocation 하나를 trace하고 human annotation 하나를 repository evaluation으로 import한다. 실행하지 못하면 PR Validation에 `⚪ Not Verified`로 기록한다.

### 6. Document Only the Project Boundary

Langfuse 역할과 repository authority, opt-in configuration/credential boundary, trace → annotation → import 절차와 외부 서비스 없이 local validation 가능한 이유만 문서화한다. Langfuse 일반 사용법을 복제하지 않는다. Capability contract가 materially 바뀌는 경우에만 current OpenSpec workflow를 따른다.

## Acceptance

- Langfuse 없이 기존 Review AI behavior와 tests가 유지된다.
- Live invocation과 Langfuse trace를 stable identity로 연결할 수 있다.
- 사람이 canonical rubric score와 rationale을 exact trace/output에 기록할 수 있다.
- 완료 annotation 한 건을 exact invocation/output/revision에 묶인 repository evaluation으로 fail-closed import할 수 있다.
- Secret/raw evidence leakage와 Langfuse failure isolation이 test로 고정된다.
- Dataset/experiment registry, prompt authority migration, LLM judge, Promptfoo와 production self-host stack이 scope에 들어오지 않는다.
- Current-head focused tests와 CI evidence가 존재한다.
- 실제 smoke를 실행하지 않았다면 그 한계를 명시한다.
- Fresh review에서 dependency/integration complexity가 얻는 live-human-eval 가치에 비해 과도하지 않은지 다시 판단한다.

## Stop Conditions

다음 중 하나가 필요해지면 scope를 넓히지 않고 blocker와 더 작은 대안을 보고한다.

- Repository evaluation contract를 Langfuse schema에 맞춰 약화해야 함
- Production-grade self-host infrastructure가 필수임
- Generic two-way synchronization 또는 experiment platform이 필요함
- Human annotation import에 supported public API가 없고 private/unstable API, scraping 또는 별도 polling framework가 필요함
- Langfuse가 deterministic safety나 recovery path의 필수 dependency가 됨
