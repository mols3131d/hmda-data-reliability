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

아래 작업은 **PR #245가 수정·검토·병합된 뒤 최신 `main`에서 시작하는 별도 PR**로 수행한다. 현재 PR #245에 Langfuse를 추가하지 않는다.

## Goal

Review AI의 repository-native evaluation contract를 유지하면서, Langfuse를 **optional live observability + human evaluation workspace**로 도입한다.

핵심 목적은 현재 빠져 있는 다음 흐름을 작고 검증 가능한 형태로 연결하는 것이다.

```text
actual model invocation
        ↓
trace / provenance
        ↓
human rubric scoring + rationale
        ↓
repository HumanUtilityEvaluation
        ↓
baseline / candidate comparison
        ↓
durable repository evidence
```

Langfuse는 이 흐름의 관찰·annotation 편의성을 제공하는 외부 surface다. **평가 의미, acceptance policy, deterministic safety와 canonical proof의 authority는 repository가 계속 소유한다.**

## Preconditions

작업을 시작하기 전에 다음을 확인한다.

1. PR #245가 `main`에 병합되었는지 확인한다. 병합되지 않았다면 이 작업을 구현하지 말고 현재 blocker를 보고한다.
1. 최신 `main`에서 새 branch를 생성한다. 이전 #245 branch 위에서 후속 구현을 이어가지 않는다.
1. `CHATBOT.md`, root `AGENTS.md`, `.agents/route/ROUTE.md`, target path의 `AGENTS.md`, Git/GitHub·development·testing 관련 Skill/Rule을 다시 로드한다.
1. 현재 `docs/mvp.md`, canonical OpenSpec, `review_ai`/`runtime_ai` implementation과 tests를 기준으로 상태를 재검증한다.
1. 이 Inbox의 과거 artifact는 비정본 working context로만 사용한다. 특히 오래된 revision, finding 번호, merge-ready 판단을 현재 사실로 승계하지 않는다.

우선 참고할 Inbox context는 다음이다.

- [`12-proposal-review-ai-utility-evaluation-remediation-and-simplification.md`](12-proposal-review-ai-utility-evaluation-remediation-and-simplification.md)
- [`13-report-review-ai-hands-on-evaluation-guide.md`](13-report-review-ai-hands-on-evaluation-guide.md)
- [`18-review-review-ai-high-confidence/README.md`](18-review-review-ai-high-confidence/README.md)
- [`18-review-review-ai-high-confidence/evidence-map.md`](18-review-review-ai-high-confidence/evidence-map.md)

## Research First

구현 전에 현재 Langfuse 공식 문서를 조사해 다음을 확인한다. 기억이나 오래된 예제에 의존하지 않는다.

- Python SDK와 OpenTelemetry 기반 tracing의 현재 권장 통합 방식
- trace / observation metadata와 score API
- human annotation 및 annotation queue의 현재 기능과 제약
- dataset / experiment 기능이 이 PR에 실제 필요한지
- local/self-host와 cloud 사용 시 필요한 infrastructure와 configuration
- credential, data retention, masking/redaction 관련 경계
- SDK failure, network failure와 application failure를 분리하는 권장 방식

조사 결과를 현재 repository 요구와 대조해 **최소 integration shape**를 먼저 결정한다. Langfuse 기능이 존재한다는 이유만으로 prompt management, dataset registry, evaluator framework 또는 self-host stack까지 도입하지 않는다.

## Architecture Constraints

다음 경계는 구현에서 유지한다.

1. **Repository remains authoritative.** `rubric_v1`, human evaluation semantics, same-case comparison invariant, deterministic guards와 MVP acceptance는 repository contract가 소유한다.
1. **Langfuse is optional.** Langfuse가 설정되지 않았거나 unavailable이어도 deterministic tests, Review AI core와 recovery path가 정상 동작해야 한다.
1. **No new authority.** Langfuse score, dashboard 상태 또는 annotation만으로 candidate를 자동 승인하거나 recovery authority를 변경하지 않는다.
1. **No prompt authority migration.** 첫 PR에서는 repository prompt와 prompt identity가 canonical이다. Langfuse Prompt Management를 runtime authority로 사용하지 않는다.
1. **No automatic LLM judge as acceptance authority.** Human rubric evaluation을 대체하지 않는다.
1. **No Promptfoo in this PR.** Prompt/model matrix regression 또는 red-team 도구 도입은 별도 필요가 확인될 때 판단한다.
1. **No production self-host platform build.** PostgreSQL, Redis, ClickHouse, object storage 등을 이 PR의 제품 인프라로 추가하지 않는다. Self-host가 필요하다면 연구 결과와 후속 선택지로만 기록한다.
1. **No secret or excessive evidence export.** API key, credential, raw large payload, 전체 로그를 Langfuse metadata에 보내지 않는다.

## Minimum Integration Scope

### 1. Live Trace Adapter

기존 live Review AI invocation에서 이미 존재하는 provenance를 Langfuse trace/observation으로 투영할 수 있는 작은 adapter boundary를 설계한다.

가능한 경우 다음 identity를 연결한다.

- `invocation_id`
- `project_revision`
- prompt identity와 prompt digest
- provider/model과 sanitized configuration
- bounded evidence identity 또는 digest
- result status와 validation outcome
- latency
- available usage/token metadata
- output identity/digest

Repository의 기존 invocation evidence를 복제해 새 canonical schema를 만들지 않는다. Langfuse에는 필요한 projection만 보낸다.

### 2. Human Rubric Mapping

현재 repository의 `rubric_v1` 다섯 criterion을 Langfuse human score surface에 매핑한다.

- `added_value`
- `actionability`
- `evidence_awareness`
- `uncertainty_handling`
- `prioritization`

각 score는 숫자만 저장하지 말고 rationale/comment를 함께 보존할 수 있어야 한다. Langfuse의 score representation이 repository contract와 정확히 일치하지 않으면 adapter가 명시적으로 변환하며, repository model을 Langfuse schema에 맞춰 약화하지 않는다.

### 3. Human Evaluation Intake Boundary

실제 live output에 대한 human annotation을 repository `HumanUtilityEvaluation` 또는 그 시점의 canonical successor contract로 가져오는 최소 경로를 만든다.

다음 binding을 잃지 않는다.

- exact evaluated output
- output digest
- invocation identity
- project revision
- case/version identity
- rubric version
- criterion score와 rationale

Langfuse annotation을 가져온다는 이유만으로 동일 case/revision 검증이나 output digest 확인을 생략하지 않는다.

### 4. Failure Isolation

Langfuse 전송·조회·annotation synchronization failure는 Review AI의 deterministic result와 분리한다.

- tracing failure가 provider result를 성공으로 바꾸거나 실패로 바꾸지 않는다.
- tracing failure가 recovery authority에 영향을 주지 않는다.
- 실패가 중요하면 좁고 typed된 integration result 또는 log/evidence로 관찰 가능하게 한다.
- broad exception swallowing으로 defect를 숨기지 않는다.

## Tests

외부 Langfuse 서비스 없이 기본 test suite가 재현 가능해야 한다.

최소한 다음을 검증한다.

1. Langfuse disabled/unconfigured 상태에서 기존 Review AI behavior가 바뀌지 않는다.
1. Fake/stub client를 사용해 trace metadata projection이 의도한 identity만 포함하는지 검증한다.
1. Credential과 불필요한 raw evidence가 export되지 않는지 검증한다.
1. Human score mapping이 다섯 rubric criterion과 rationale을 loss 없이 repository evaluation으로 변환하는지 검증한다.
1. Wrong invocation/output digest/revision에 연결된 annotation은 fail-closed 한다.
1. Langfuse network/client failure가 Review AI core result나 recovery boundary를 훼손하지 않는지 검증한다.
1. 기존 `tests/review_ai`, 관련 `runtime_ai` tests와 dependency boundary 검증이 계속 통과한다.

실제 Langfuse instance가 필요한 smoke test는 opt-in으로 분리한다. Credential이나 외부 service가 없어 실행하지 못했다면 PR Validation에 `⚪ Not Verified`로 정확히 기록한다.

## OpenSpec and Documentation

이 integration이 capability contract를 materially 변경한다면 repository OpenSpec workflow를 따른다. 새 change가 필요하면 범위를 **Langfuse optional adapter와 live human-evaluation bridge**로 한정하고, 기존 Review AI evaluation contract 전체를 다시 설계하지 않는다.

문서에는 최소한 다음을 명확히 한다.

- Langfuse가 무엇을 소유하고 무엇을 소유하지 않는지
- repository-native evidence와 Langfuse trace/score의 관계
- local/offline validation이 외부 서비스 없이 계속 가능한 이유
- opt-in configuration과 credential boundary
- live human evaluation 절차

Langfuse 사용법 전체를 repository 문서에 복제하지 말고 프로젝트에 필요한 경계와 진입점만 남긴다.

## PR Scope

새 branch와 Draft PR을 만들고 하나의 coherent change로 유지한다.

권장 change topic은 `review-ai-langfuse-evaluation`이다. 실제 branch/PR 이름은 최신 repository naming policy를 따른다.

이 PR에는 다음을 섞지 않는다.

- #245에서 남은 correctness remediation
- Promptfoo 도입
- prompt registry migration
- automatic LLM judge
- generic experiment platform 구축
- production-grade Langfuse self-host infrastructure
- unrelated Review AI schema redesign
- recovery/approval authority 변경

## Acceptance

다음이 모두 성립할 때만 이 PR을 review-ready 후보로 본다.

- Langfuse 없이 repository core가 완전히 동작하고 test 가능하다.
- 실제 live invocation을 Langfuse trace와 안정적으로 연결할 수 있는 identity mapping이 있다.
- 사람이 남긴 `rubric_v1` score와 rationale을 exact invocation/output/revision에 다시 결합할 수 있다.
- repository evaluation/comparison contract가 Langfuse availability와 독립적으로 유지된다.
- secret/raw evidence leakage를 방지하는 검증이 있다.
- Langfuse failure가 deterministic safety 또는 recovery authority를 바꾸지 않는다.
- current-head tests와 CI evidence가 존재한다.
- 실제 Langfuse smoke를 수행하지 않았다면 그 한계를 명시한다.
- fresh review에서 새로운 external dependency가 MVP 대비 과도하지 않은지 다시 판단한다.

## Final Handoff

작업 완료 시 다음만 간결하게 보고한다.

1. 선택한 Langfuse integration 방식과 선택 이유
1. repository authority와 Langfuse responsibility 경계
1. 변경된 주요 code/test/doc surface
1. 실제 수행한 validation과 미검증 live 부분
1. 남은 risk와 다음 단계

구현 중 더 큰 evaluation platform이나 infrastructure가 필요해 보이면 즉시 scope를 넓히지 않는다. 현재 MVP 요구를 만족하는 더 작은 repository-native 방법과 비교한 뒤, 별도 제안으로 분리한다.
