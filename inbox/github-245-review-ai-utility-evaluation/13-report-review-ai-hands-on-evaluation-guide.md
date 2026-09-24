---
type: report
title: "Review AI Hands-On Evaluation Guide"
description: "현재 Review AI의 offline utility fixture와 opt-in live provider review를 직접 실행하고, 사람이 유용성과 한계를 구분해 판단하는 절차를 제공합니다."
tags:
  - "domain:review-ai"
  - "capability:reliability-agentic-review"
  - "pull-request"
  - "report"
  - "evaluation"
  - "human-review"
---

# Review AI Hands-On Evaluation Guide

## Purpose

현재 구현을 직접 사용해 다음 두 질문에 답하는 것이 목적이다.

1. 고정된 null-spike 사례에서 Review AI의 출력이 사람이 다음 조사를 더 잘 결정하게 하는가?
1. 출력, evidence와 invocation record를 사람이 충분히 이해하고 신뢰 경계를 확인할 수 있는가?

이 체험은 PR #245의 merge-ready utility proof를 대신하지 않는다. [09 current-head review](09-review-review-ai-utility-evaluation-current-head.md)의 F1-F3은 현재 head에서 미해결이므로, 이 보고서의 결과는 **현 기능의 유용성·사용성 판단 근거**로만 기록한다. baseline/candidate 비교를 merge 또는 promotion의 근거로 사용하지 않는다.

## What You Can Evaluate Today

현재 CLI가 만드는 사례는 사용자가 임의의 incident를 입력하는 범용 console이 아니다. 두 runner 모두 고정된 synthetic `income` null-spike 사례를 사용한다.

| Path | What it does | What you can judge | What it does not prove |
| --- | --- | --- | --- |
| Offline utility proof | 고정 baseline/candidate와 미리 입력된 score를 비교하고 create-only JSON을 만든다. | 출력·comparison artifact의 구조와 현재 fixture가 무엇을 주장하는지 | 실제 model output 또는 실제 human utility |
| Live provider proof | 명시적으로 opt-in한 provider에 bounded review prompt를 보내고 typed result와 invocation evidence를 남긴다. | 실제 모델이 evidence 안에서 유용한 advisory review를 만드는지 | 일반 incident에 대한 성능, recovery 안전성, F1-F3 해소 |

어느 경로도 approval, recovery, SQL, shell, file, database 또는 data mutation을 수행하지 않는다. Live provider proof는 외부 또는 로컬 provider 호출 비용과 시간이 들 수 있으므로, 실제 호출 전에 사용자가 provider와 model을 선택한다.

## Preparation

작업 디렉터리는 repository root로 가정한다. 아래 경로는 예시 artifact root이며, Git tracked worktree를 바꾸지 않는 `.local/` 또는 `.tmp/` 아래에 둔다.

```bash
git status --short
uv run pytest tests/review_ai tests/runtime_ai
```

첫 command는 현재 변경 상태를 확인한다. Live runner에서 `HMDA_AGENTIC_REVIEW_PROJECT_REVISION=auto`를 사용할 때 tracked worktree가 깨끗해야 Git HEAD를 invocation evidence에 자동 바인딩할 수 있다. 현재처럼 작업 중인 변경이 있다면 live 실행에 non-empty revision label을 명시해 무엇을 시험했는지 기록한다.

예를 들어 local provider를 사용할 경우 `.env`에는 다음 값이 필요하다. 실제 API key 값은 report, terminal 출력 또는 artifact에 기록하지 않는다.

```dotenv
HMDA_AGENTIC_REVIEW_LIVE=true
HMDA_AGENTIC_REVIEW_BASE_URL=http://localhost:11434/v1
HMDA_AGENTIC_REVIEW_API_KEY=ollama
HMDA_AGENTIC_REVIEW_MODEL=<installed-model-name>
HMDA_AGENTIC_REVIEW_PROJECT_REVISION=hands-on-2026-09-21
HMDA_RELIABILITY_ARTIFACTS_DIR=.local/hands-on-review-ai
```

`HMDA_AGENTIC_REVIEW_MODEL`에는 실제 provider에서 사용할 수 있는 모델명을 입력한다. default timeout, retry, output/prompt byte limit은 [`.env.example`](../../.env.example)에 정의되어 있으며, 필요할 때만 local `.env`에서 조정한다.

## Exercise 1: Inspect the Offline Fixture

먼저 network 없이 현재 evaluation fixture가 무엇을 비교하는지 확인한다.

```bash
uv run --no-sync python scripts/run_review_ai_utility_proof.py \
  --artifact-root .local/hands-on-review-ai \
  --project-revision hands-on-offline-2026-09-21
```

stdout에는 baseline과 candidate의 five-criterion score, delta, `accept` decision이 출력되고 다음 경로 아래에 JSON proof bundle이 생성된다.

```text
.local/hands-on-review-ai/agentic-review/utility/proofs/review-ai-utility-proof-v1.json
```

### Inspect

JSON에서 다음을 차례로 읽는다.

1. `comparison.baseline_output`: deterministic null-rate 증가와 root cause 미확정만 반복하는 baseline이다.
1. `comparison.candidate_output.utility_contributions`: evidence gap, investigation priority, remediation critique, material uncertainty를 가진 fixture output이다.
1. `comparison.criterion_deltas`: baseline과 candidate의 점수 차이다.
1. `comparison.rationale`: 현재 runner가 미리 고정한 accept 이유다.

### Record a judgment

다음 질문에 짧게 답한다.

- candidate가 실제로 새로운 판단을 돕는가, 아니면 이미 context에 있는 내용을 다른 말로 반복하는가?
- 다섯 criterion이 내 업무의 유용성을 충분히 설명하는가?
- baseline과 candidate에 이미 사람이 준 점수와 `accept`가 코드에 고정되어 있다는 점을 이해했는가?

이 단계에서 `accept`는 사용자의 판단이 아니다. fixture contract가 기대하는 결과일 뿐이다. 직접 판단한 내용은 Exercise 3의 기록에 별도로 남긴다.

## Exercise 2: Run One Live Advisory Review

provider가 준비되었고 `.env`의 `HMDA_AGENTIC_REVIEW_LIVE=true`를 명시했다면 다음 command를 실행한다.

```bash
uv run --env-file .env python scripts/run_agentic_review_live.py
```

성공한 실행은 stdout에 `status: "accepted"`와 structured output을 출력한다. provider가 시작된 실행은 다음 위치에 sanitized invocation evidence를 남긴다.

```text
.local/hands-on-review-ai/agentic-review/invocations/<invocation-id>.json
```

`input_rejected`는 provider 호출 전 거부이므로 invocation JSON을 만들지 않는다. `validation_failed`와 `unavailable`은 provider가 시작된 뒤의 typed failure이며 invocation JSON을 남긴다. `provenance_failed`는 provider 결과 또는 실패를 받았지만 durable evidence를 저장하지 못한 경우다.

### Inspect an accepted result

`accepted`이면 stdout output과 invocation JSON을 나란히 읽는다. JSON에서 특히 다음을 확인한다.

| Check | Read | Human question |
| --- | --- | --- |
| Bounded evidence | `evidence_refs`, `canonical_input.evidence`, `canonical_input.review_context` | 모델이 실제로 제공된 evidence 안에서만 말했는가? 필요한 gap도 보이는가? |
| Fact preservation | `parsed_output.incident_id`, `target_column`, `deterministic_facts` | null-rate, target column, incident identity를 바꾸거나 과장하지 않았는가? |
| Decision support | `parsed_output.utility_contributions`, `findings`, `uncertainties` | 다음 조사 순서나 draft 위험을 더 명확히 했는가? |
| Guard result | `validation.status`, `validation.violations` | accepted라면 violation이 비어 있는가? validation failure라면 거절 사유가 이해되는가? |
| Replay context | `prompt_identity`, `prompt_digest`, `project_revision`, `configuration` | 어느 prompt/model/revision 조건에서 이 output이 나왔는지 재구성할 수 있는가? |
| Operational cost | `latency_ms`, `attempt_count`, `usage` | 이 응답 속도와 비용이 실제 조사 workflow에 맞는가? |

credential은 invocation evidence에 포함되어서는 안 된다. configuration에는 sanitized `base_url`, model과 limit만 남아야 한다.

## Exercise 3: Score the Live Output Yourself

Live output을 읽은 뒤, 별도 메모나 issue comment에 아래 형식으로 평가를 기록한다. 현재 CLI에는 human score를 입력해 comparison evidence로 저장하는 intake command가 없으므로, 이 기록은 의도적으로 사람이 소유한다.

```text
Case: fixed synthetic income null-spike
Invocation: <invocation_id>
Revision: <project_revision>
Model: <configuration.model>

added_value: 0 | 1 | 2
Rationale:

actionability: 0 | 1 | 2
Rationale:

evidence_awareness: 0 | 1 | 2
Rationale:

uncertainty_handling: 0 | 1 | 2
Rationale:

prioritization: 0 | 1 | 2
Rationale:

Overall decision: useful | not useful | inconclusive
Why:
```

점수는 다음의 working anchor로 사용한다. 이는 현재 `rubric_v1`에 아직 코드화되지 않은 human interpretation이며, 이 체험을 통해 anchor가 충분한지도 함께 판단한다.

| Criterion | 0 | 1 | 2 |
| --- | --- | --- | --- |
| `added_value` | facts 또는 context gap의 재진술 | 새 관점은 있으나 다음 판단을 거의 좁히지 못함 | evidence에 근거해 조사 또는 판단을 실질적으로 좁힘 |
| `actionability` | 실행할 다음 행동이 없음 | 행동은 있으나 범위 또는 근거가 모호함 | 지금 할 bounded 다음 행동과 근거가 명확함 |
| `evidence_awareness` | evidence 밖을 단정하거나 facts를 흐림 | evidence와 gap을 일부 구분함 | 확인된 사실, 인용 evidence, 미확인 영역을 분명히 구분함 |
| `uncertainty_handling` | 과신하거나 전면적 회피만 함 | uncertainty는 언급하지만 영향이 모호함 | 중요한 불확실성, 그 영향, 해소에 필요한 evidence를 구체화함 |
| `prioritization` | 우선순위가 없거나 모두 우선이라고 함 | 순서는 있으나 근거가 약함 | 영향과 evidence에 연결된 조사 순서가 명확함 |

특히 `utility_contributions`가 채워졌다는 사실만으로 `added_value=2`를 주지 않는다. `missing_evidence`나 `unconfirmed_context`에 이미 적힌 문장을 반복했는지, 아니면 다음 판단을 줄이는 synthesis를 제공했는지 구분한다.

## Exercise 4: Deliberately Observe a Safe Failure

동일한 fixed case에서 provider 없이 configuration guard가 어떻게 동작하는지 확인하려면 live flag를 제외한 상태로 실행한다.

```bash
HMDA_AGENTIC_REVIEW_LIVE=false \
uv run --env-file .env python scripts/run_agentic_review_live.py
```

예상 결과는 `Agentic review live proof is disabled.`와 exit code 0이다. provider 호출이나 invocation artifact는 생기지 않아야 한다.

다음과 같은 결과는 defect로 단정하기 전에 환경 또는 provider 상태로 분류한다.

| Result | Meaning | Human action |
| --- | --- | --- |
| `Missing live configuration` | 필수 환경 변수 누락 | `.env`의 base URL, API key, model, opt-in flag를 확인한다. |
| `input_rejected` | provider 호출 전 input 또는 prompt preflight 거부 | failure code를 기록한다. 현재 F2의 context-overflow typed handling은 미해결 review finding이므로 예외 전파가 보이면 merge evidence로 사용하지 않는다. |
| `unavailable` | provider transport 또는 retry가 실패 | provider health, URL, model availability를 확인하고 output utility와 혼동하지 않는다. |
| `validation_failed` | provider output이 schema 또는 deterministic guard를 통과하지 못함 | failure code, validation violation과 invocation evidence를 읽고 모델 output을 utility 평가 대상으로 삼지 않는다. |
| `provenance_failed` | result를 durable evidence로 남기지 못함 | artifact path/permission을 확인하고 성공한 review로 채택하지 않는다. |

## Decision Checklist

체험 뒤에는 다음 세 가지를 분리해 결정한다.

1. **Usability:** 고정 사례의 실제 output이 나의 다음 조사 행동을 줄였는가?
1. **Trust:** evidence, facts, uncertainty와 invocation metadata가 판단을 검토하기에 충분했는가?
1. **Product direction:** fixed synthetic case에서 유용했다면, 다음에는 사용자 제공 incident를 평가할 수 있는 intake를 우선할지, 아니면 F1-F3 remediation과 evaluation simplification을 먼저 끝낼지?

현재 권장되는 답은 세 번째 질문에서 **F1-F3 remediation을 먼저 끝내는 것**이다. 체험 결과가 긍정적이어도 same-case attribution, typed preflight failure와 provider-visible evidence set의 불일치는 merge gate에서 별도로 닫아야 한다.

## Suggested Human Handoff

체험을 마친 뒤 아래 다섯 줄만 남기면 다음 작업의 판단에 충분하다.

```text
Live run status: <accepted | typed failure>
Most useful output: <one item or none>
Most confusing or unhelpful output: <one item or none>
Rubric decision: <useful | not useful | inconclusive>
Next decision: <fix F1-F3 | revise output/prompt | design human intake | stop>
```

이 기록에는 API key, raw provider error, 불필요한 raw prompt나 대용량 payload를 포함하지 않는다. invocation ID와 artifact path만 남기면 필요한 evidence를 다시 찾을 수 있다.
