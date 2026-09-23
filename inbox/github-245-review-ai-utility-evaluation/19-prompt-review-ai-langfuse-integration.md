---
type: prompt
title: "Review AI Langfuse Integration Next-Step Prompt"
description: "PR #245 완료 후 Langfuse를 optional live tracing 및 human evaluation layer로 도입하는 별도 PR 작업을 지시합니다."
tags:
  - "domain:review-ai"
  - "capability:reliability-agentic-review"
  - evaluation
  - langfuse
  - llmops
---

# Review AI Langfuse Integration Next-Step Prompt

PR #245가 수정·검토·병합된 뒤 최신 `main`에서 별도 Draft PR로 이 작업을 시작한다. 현재 PR #245에 Langfuse를 추가하지 않는다.

## Goal

Review AI의 repository-native evaluation contract를 유지하면서 Langfuse를 **optional live tracing + human evaluation workspace**로 도입한다.

첫 PR의 최소 목표는 다음 흐름을 실제로 연결하는 것이다.

```text
live Review AI invocation
        ↓
Langfuse trace
        ↓
human rubric_v1 annotation + rationale
        ↓
one-way import
        ↓
repository HumanUtilityEvaluation
```

Langfuse는 관찰과 human annotation을 위한 working surface다. 평가 의미, deterministic guard, acceptance와 canonical evaluation evidence는 repository가 계속 소유한다.

## Preconditions

1. PR #245가 `main`에 병합되었는지 확인한다. 아직 병합되지 않았다면 구현을 시작하지 말고 blocker를 보고한다.
1. 최신 `main`에서 새 branch와 Draft PR을 만든다. #245 branch를 후속 구현 branch로 재사용하지 않는다.
1. `CHATBOT.md`부터 applicable repository guidance를 다시 로드하고, 현재 `docs/mvp.md`, canonical OpenSpec, `review_ai`/`runtime_ai` 구현과 tests를 기준으로 상태를 재검증한다.
1. #245 이후 evaluation model이 단순화·변경되었으면 현재 canonical contract에 맞춘다. Inbox에 적힌 오래된 type, revision, finding 번호를 유지하기 위해 새 abstraction을 만들지 않는다.

우선 참고할 working context는 다음이다.

- [`12-proposal-review-ai-utility-evaluation-remediation-and-simplification.md`](12-proposal-review-ai-utility-evaluation-remediation-and-simplification.md)
- [`13-report-review-ai-hands-on-evaluation-guide.md`](13-report-review-ai-hands-on-evaluation-guide.md)
- [`18-review-review-ai-high-confidence/README.md`](18-review-review-ai-high-confidence/README.md)

Inbox는 비정본이므로 현재 code/spec과 충돌하면 현재 canonical source를 따른다.

## Boundaries

- Repository가 `rubric_v1`, evaluation semantics, same-case invariant, deterministic safety와 MVP acceptance를 소유한다.
- Langfuse가 없거나 unavailable이어도 Review AI core, deterministic tests와 recovery path는 정상 동작해야 한다.
- Langfuse annotation이나 dashboard 상태만으로 candidate 승인, recovery 또는 delegation authority를 변경하지 않는다.
- Repository prompt와 prompt identity를 canonical로 유지한다. 이 PR에서 Langfuse Prompt Management로 runtime authority를 이전하지 않는다.
- Automatic LLM judge, Promptfoo, generic experiment platform과 production-grade Langfuse self-host infrastructure를 도입하지 않는다.
- Credential, raw large payload, 전체 로그 또는 불필요한 evidence를 Langfuse로 export하지 않는다.
- Langfuse client/network failure를 Review AI provider result나 deterministic validation 결과로 재분류하지 않는다.

## Work

### 1. Research the Current Integration Surface

현재 Langfuse 공식 문서만 기준으로 Python SDK/OpenTelemetry tracing, score·human annotation API, credential/redaction, failure behavior를 조사한다. 기억이나 오래된 예제에 의존하지 않는다.

조사 후 아래 목표를 만족하는 가장 작은 지원 경로를 선택한다. Langfuse 기능이 존재한다는 이유만으로 dataset, experiment, prompt registry 또는 self-host stack을 추가하지 않는다.

### 2. Add an Optional Live Trace Projection

기존 live invocation provenance를 새 canonical schema로 복제하지 말고 Langfuse에 필요한 최소 projection만 보낸다.

Trace를 repository evidence와 다시 연결할 수 있도록 최소한 다음 identity를 보존한다.

- `invocation_id`
- `project_revision`
- prompt identity 또는 digest
- model과 sanitized configuration
- result/validation status
- output identity 또는 digest
- latency와 available usage

Evidence는 raw payload보다 identity/digest를 우선한다. Integration은 disabled-by-default 또는 명시적 opt-in이어야 한다.

### 3. Map Human `rubric_v1` Annotation

현재 canonical rubric의 다섯 criterion을 Langfuse human annotation surface에 매핑한다.

- `added_value`
- `actionability`
- `evidence_awareness`
- `uncertainty_handling`
- `prioritization`

각 criterion은 score와 rationale/comment를 함께 남길 수 있어야 한다. Langfuse schema가 repository contract와 다르면 repository model을 약화하지 말고 integration boundary에서 명시적으로 변환한다.

### 4. Import One Completed Evaluation

양방향 synchronization framework를 만들지 않는다. 한 trace에 완료된 human annotation을 읽어 exact invocation/output/revision에 결합된 repository `HumanUtilityEvaluation` 또는 현재 canonical successor로 변환하는 **one-way import**만 구현한다.

Import는 다음 identity가 일치하지 않으면 fail-closed 해야 한다.

- invocation
- evaluated output 또는 output digest
- project revision
- case/version
- rubric version

Baseline/candidate comparison 로직 자체는 이 PR에서 다시 설계하지 않는다. Import된 evaluation이 기존 comparison contract의 입력으로 사용될 수 있으면 충분하다.

### 5. Verify Without an External Service

기본 test suite는 실제 Langfuse instance 없이 실행 가능해야 한다. Fake/stub client로 최소한 다음을 검증한다.

1. Langfuse disabled 상태에서 기존 behavior가 변하지 않는다.
1. Trace projection이 필요한 identity만 포함하고 secret/raw evidence를 내보내지 않는다.
1. 다섯 rubric score와 rationale이 loss 없이 repository evaluation으로 변환된다.
1. Wrong invocation/output/revision/rubric annotation은 import되지 않는다.
1. Langfuse client/network failure가 Review AI core result와 recovery boundary를 바꾸지 않는다.

실제 Langfuse smoke는 opt-in으로 분리한다. 실행 가능한 환경이 있으면 live invocation 하나를 trace하고 human annotation 하나를 repository evaluation으로 import해 end-to-end path를 확인한다. 실행하지 못하면 PR Validation에 `⚪ Not Verified`로 기록한다.

### 6. Document Only the Project Boundary

필요한 code, test와 최소 project guidance만 남긴다. 문서는 다음만 설명한다.

- Langfuse가 맡는 역할과 repository가 계속 소유하는 역할
- opt-in configuration과 credential/redaction boundary
- live trace → human annotation → one-way import 절차
- Langfuse 없이 local/offline validation이 가능한 이유

Langfuse 일반 사용법을 repository에 복제하지 않는다. Capability contract가 materially 바뀌는 경우에만 현재 OpenSpec workflow를 따른다.

## Acceptance

다음이 모두 성립할 때 review-ready 후보로 본다.

- Langfuse 없이 기존 Review AI behavior와 tests가 유지된다.
- Live invocation과 Langfuse trace를 stable identity로 연결할 수 있다.
- 사람이 `rubric_v1` 다섯 score와 rationale을 exact trace/output에 기록할 수 있다.
- 완료된 annotation 한 건을 exact invocation/output/revision에 묶인 repository evaluation으로 fail-closed import할 수 있다.
- Secret/raw evidence leakage와 Langfuse failure isolation이 test로 고정된다.
- Dataset/experiment registry, prompt authority migration, LLM judge, Promptfoo와 production self-host stack이 scope에 들어오지 않는다.
- Current-head focused tests와 CI evidence가 존재한다.
- 실제 Langfuse smoke를 실행하지 않았다면 그 한계를 명시한다.
- Fresh review에서 dependency와 integration complexity가 얻는 live-human-eval 가치에 비해 과도하지 않은지 다시 판단한다.

## Stop Conditions

다음 중 하나가 필요해지면 scope를 넓히지 말고 blocker와 더 작은 대안을 보고한다.

- Repository evaluation contract를 Langfuse schema에 맞춰 약화해야 함
- Production-grade self-host infrastructure가 필수임
- Generic two-way synchronization 또는 experiment platform이 필요함
- Langfuse가 deterministic safety나 recovery path의 필수 dependency가 됨

작업 완료 보고는 선택한 integration 방식, repository/Langfuse 경계, 주요 변경 surface, 수행한 validation, 미검증 live 부분과 남은 risk만 간결하게 남긴다.
