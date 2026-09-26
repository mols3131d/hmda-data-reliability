---
type: plan
title: "Review AI Langfuse Integration Plan"
description: "PR #248의 optional Langfuse 연동을 위한 착수 조건, record projection, human annotation, 실패 격리와 단계별 검증 계획입니다."
tags:
  - "domain:review-ai"
  - "capability:reliability-agentic-review"
  - evaluation
  - langfuse
  - llmops
---

# Review AI Langfuse Integration Plan

**첫 구현은 기존 live 실행 한 경로에서 검증된 로컬 invocation record를 Langfuse에 표시하고, 사람이 정확한 output에 `rubric_v1` 점수와 근거를 남기는 데 한정한다.** 실시간 provider 자동 계측이나 새로운 평가 저장소를 만들지 않는다. Langfuse는 optional 보조 도구이며 repository가 evaluation semantics, deterministic safety, prompt identity와 acceptance boundary를 계속 소유한다.

이 문서는 `agent/feat/review-ai-langfuse-evaluation` branch와 PR #248이 소유하는 실행 계획이다. Canonical requirements는 [Review AI Spec](../../openspec/specs/reliability-agentic-review/spec.md), 제품 acceptance는 [MVP](../../docs/mvp.md), domain ownership은 [Review AI guide](../../docs/domains/review-ai.md)가 소유한다. 이 계획은 해당 계약을 대체하지 않는다.

## Current State

2026-09-26 확인 기준이다. 아래 revision은 계획 수정 전 코드 상태를 식별하며 이후 변경의 검증 결과를 대신하지 않는다.

| Item | State | Evidence |
| --- | --- | --- |
| Utility evaluation prerequisite | Complete | #245 구현 뒤 #250의 `1d7e5c70baa03540644e0dac71b740330f3e58cb`에서 canonical Spec 반영과 [Change archive](../../openspec/changes/archive/2026-09-25-review-ai-utility-evaluation/README.md)를 완료했다. |
| Local main integration | Complete | 로컬 HEAD `9cfc21b6432c845c0303be3e46f35c313b5ecc5e`에 위 main revision을 병합했다. |
| Remote delivery | Pending | 마지막 확인한 Draft PR head는 `7df0f772d0fc0b2dba3f5e1ad548ffc3436866ef`다. 로컬 병합은 아직 push하지 않았고 PR 설명도 이전 prerequisite 상태다. |
| Contract review | Reviewed | MVP, domain guide, canonical Spec, live harness, provenance와 human evaluation 계약을 검토했다. Langfuse implementation, runtime test와 live smoke는 수행하지 않았다. |
| Vendor evidence | Blocked | 공식 문서 접근이 network domain policy로 차단됐다. 선택할 SDK 버전, capture 제어, score/comment mapping과 bounded flush 동작은 미확인이다. |

OpenSpec canonicalization을 다시 수행하거나 기다릴 필요는 없다. **다음 작업은 아래 Entry Checks이며, 확인 전에는 Langfuse dependency나 production integration code를 추가하지 않는다.** Code, base 또는 vendor version이 바뀌면 영향을 받는 근거만 다시 확인한다.

## Goal

현재도 로컬 record에 입력, 출력, model/config와 provenance가 남는다. 도입 가설은 Langfuse가 새로운 판단을 제공한다는 것이 아니라, 사람이 record를 찾아 input/output과 근거를 읽고 항목별 점수를 기록하는 수작업을 줄인다는 것이다. 같은 합성 사례 한 건으로 기존 흐름과 제안 흐름을 비교해 도입 비용보다 이득이 있는지 판단한다.

성공 범위는 실제 invocation의 **실행 후 projection과 사람의 annotation**이다. 전체 호출의 실시간 span tree, repository `HumanUtilityEvaluation` 생성, baseline/candidate comparison 또는 MVP 전체 완료를 뜻하지 않는다.

## Entry Checks

| Check | Required evidence | Stop condition |
| --- | --- | --- |
| Workflow value | 기존 합성 사례에서 record 탐색, 근거 확인, 다섯 항목 채점에 필요한 수작업과 Langfuse가 줄일 작업을 짧게 비교한다. 별도 benchmark는 만들지 않는다. | 줄일 마찰이 없거나 작은 연동보다 운영 비용이 크면 도입하지 않는다. |
| Supported SDK | 사용할 Python SDK 버전과 공식 문서 URL, 확인일을 기록한다. Python/runtime 호환성, 수동 trace/observation 생성, 자동 input/output capture 억제와 기존 OpenTelemetry 설정에 대한 영향을 확인한다. | 공식 surface를 확인할 수 없거나 전역 계측 없이 allowlist를 지킬 수 없으면 구현을 보류한다. |
| Human annotation | 해당 배포에서 score별 0/1/2 값과 non-empty rationale, 정확한 output 연결, 미완료 항목 구분을 표현할 수 있는지 확인한다. | rubric 의미를 바꾸거나 custom evaluation UI가 필요하면 범위를 확대하지 않고 보고한다. |
| Client lifecycle | 짧은 프로세스에서 init/export/flush/shutdown failure와 대기 상한을 어떻게 통제하고 확인할지 선택한 버전의 근거로 정한다. | 호출 완료를 무한히 기다리거나 core 결과를 바꾸지 않고 종료할 수 없다면 보류한다. |
| Live destination | 사용할 Langfuse endpoint/project, 접근 권한과 합성 데이터 export 허용 범위를 확인한다. Credential은 사용자가 local environment에 직접 설정한다. | 대상이나 권한이 없으면 live 검증은 blocked로 남기고 외부 project를 임의로 만들지 않는다. |

공식 문서 확인 출발점은 [SDK overview](https://langfuse.com/docs/observability/sdk/overview), [Masking](https://langfuse.com/docs/observability/features/masking), [Annotation queues](https://langfuse.com/docs/evaluation/evaluation-methods/annotation-queues)다. 링크는 기능 검증의 증거가 아니다. Network policy가 차단하면 다른 통로로 우회하지 않고 접근 허용 또는 해당 버전의 공식 자료를 요청한다.

앞의 네 check는 dependency와 구현 착수 조건이며, live destination은 외부 전송과 smoke의 조건이다. 확인 결과와 남은 blocker는 이 문서에 이어서 기록한다. Deferred importer를 위한 score retrieval API 조사는 첫 구현의 prerequisite가 아니다.

## Implementation Decisions

### Owner and Lifecycle

1. [기존 live harness](../../scripts/run_agentic_review_live.py)에서 별도의 명시적 Langfuse opt-in을 확인한다. Live provider opt-in만으로 외부 export를 허용하지 않는다.
1. 기존 `review_null_spike()` 호출, deterministic validation, 로컬 provenance 저장과 harness의 검증을 그대로 마친다.
1. 검증된 [invocation record](../../src/hmda_reliability/review_ai/evidence.py)를 읽어 Review AI 전용의 작은 projector로 allowlist payload를 만든다. 기존 client/utility가 해당 역할을 소유하면 재사용하며 generic exporter interface를 만들지 않는다.
1. Harness가 optional client 생성, export와 종료를 소유한다. SDK import와 초기화는 비활성 경로에 필요하지 않게 하고 dependency 설치 방식은 기존 package configuration에 맞춘다.

첫 slice에서는 `review_null_spike()`의 public API, [로컬 저장 처리](../../src/hmda_reliability/review_ai/service.py), core evidence schema를 변경하지 않는다. Review-specific metadata와 rubric을 `runtime_ai`에 넣지 않는다. Provider SDK 자동 계측, global tracer/provider 교체와 환경 전체 수집은 사용하지 않는다.

### Export Allowlist

첫 live 증명은 harness의 합성 null-spike 사례에 한정한다. 실데이터 반출은 별도 검토 없이 확대하지 않는다. Bounded 또는 sanitized record라는 이유만으로 `model_dump()` 결과 전체를 전송하지 않는다.

| Projection | Included | Excluded or constrained |
| --- | --- | --- |
| Attribution | `invocation_id`, `project_revision`, prompt template/version/digest, `rubric_v1`, accepted output의 exact digest | Vendor ID를 core field로 추가하거나 provider `trace_id`와 같은 의미로 사용하지 않는다. |
| Execution | record의 status, validation policy/status, model, timeout/retry/token/byte limits, temperature, recorded time, latency와 제공되는 usage | Credential, provider base URL, raw error, 환경 변수와 전체 log를 제외한다. Export 시간을 실제 model latency로 표시하거나 없는 usage/cost를 추정하지 않는다. |
| Human context | accepted 사례의 bounded deterministic facts, 평가에 필요한 draft, evidence identity/source/facts와 context gaps | Raw rows, 전체 manifest, unbounded evidence를 제외한다. 실제 field별 mapping과 크기 제한을 구현 전에 고정한다. |
| Human output | accepted structured output의 review/utility content와 정확한 digest | Raw response와 rendered prompt는 제외한다. 실패 결과의 partial output은 첫 slice에서 반출하거나 채점하지 않는다. |

Context나 output을 잘라 의미가 달라졌는데도 평가 가능한 것처럼 표시하지 않는다. Allowlist/크기 조건으로 판단 근거를 제공할 수 없으면 해당 export를 생략하고 이유를 남긴다. Exact output digest는 [기존 `utility_output_digest()`](../../src/hmda_reliability/review_ai/evaluation.py)를 재사용한다.

### Human Annotation

- 채점 대상은 `invocation_id + output_digest + rubric_v1`로 고정하고 같은 record의 revision, prompt와 model/config를 연결한다. UI가 새 output으로 대상을 덮어쓰지 않게 한다.
- Repository-owned `added_value`, `actionability`, `evidence_awareness`, `uncertainty_handling`, `prioritization` 각각에 0/1/2 score와 비어 있지 않은 rationale를 남긴다. 총점이나 공통 comment 하나로 대체하지 않는다.
- 다섯 항목 중 값 또는 근거가 빠지면 incomplete다. Vendor UI의 완료 표시만으로 repository rubric 충족을 주장하지 않는다. 기존 `RubricScore` 계약을 재사용할 수 있는 validation에는 이를 사용한다.
- Score config와 queue/display metadata는 rubric의 projection이다. 작은 수동 setup으로 충분하면 queue provisioning 자동화를 만들지 않는다. 채점과 utility 판단은 사람이 수행하며 agent가 점수를 만들어 human evidence로 기록하지 않는다.
- First slice는 integration-local annotation까지다. `HumanUtilityEvaluation`, comparison 또는 candidate 승인으로 자동 승격하지 않으며, 이를 위해 `output_fixture_id`, case/version 또는 evaluation schema를 일반화하지 않는다.

### Failure Isolation

| Condition | Core behavior | Integration behavior |
| --- | --- | --- |
| Langfuse disabled 또는 SDK 미설치 상태에서 disabled | 기존 result, provenance와 harness exit 의미를 유지한다. | SDK import, client 생성, network 호출을 하지 않는다. |
| `input_rejected` 또는 `provenance_failed` | 기존 상태를 그대로 유지한다. | 검증된 record가 없으므로 export와 annotation을 생략한다. |
| Harness provenance 검증 실패 | 기존 검증 실패와 exit 의미를 유지한다. | Export하지 않는다. |
| Durable `unavailable` 또는 `validation_failed` record | 기존 상태를 그대로 유지한다. | 최소 status/typed failure metadata만 표시하고 human utility annotation 대상에서 제외한다. |
| Init, projection, export, flush 또는 shutdown 실패 | Result, 로컬 record와 recovery authority를 변경하지 않는다. | Sanitized 연동 상태를 별도로 표시하고 configured 상한 안에 종료한다. Raw exception이나 credential을 출력하지 않는다. |
| Client가 전송을 수락했으나 ingestion 미확인 | Core 성공 여부와 별개다. | 원격 조회 전에는 전달·smoke 성공을 주장하지 않는다. |

로컬 저장 실패를 나타내는 `provenance_failed`를 Langfuse 실패에 재사용하지 않는다. 예외 처리는 integration 경계에 제한하고 기존 review 예외나 취소를 성공으로 바꾸지 않는다. 별도 polling worker, durable export queue 또는 retry framework는 추가하지 않는다.

## Execution Sequence

Agent가 조사, 설계 구체화, 구현과 검증을 순서대로 담당한다. Network policy, secret 입력, 외부 project 권한과 실제 human utility 판단은 대신 승인하거나 우회하지 않는다. Routine implementation 선택은 이 범위에서 진행하되 canonical contract 변경이나 scope 확대가 필요하면 먼저 보고한다.

1. **Resolve entry checks.** Workflow 비교와 버전별 공식 근거를 확보하고 SDK, field mapping/크기 제한, lifecycle 상한과 annotation 완료 확인 방법을 정한다. 접근 차단이 남으면 이를 다음 blocker로 유지한다.
1. **Prepare implementation contracts.** 착수 시 current branch/base와 source/test를 재확인한다. Repository의 현행 OpenSpec workflow에 맞춰 #248의 구현 계약과 test tasks를 준비하며 archived utility Change를 재활성화하지 않는다. 해당 artifact가 생기면 이 문서에서 연결하고 상세 요구사항이나 task 상태를 중복 관리하지 않는다.
1. **Implement the offline slice.** 기존 [live harness tests](../../tests/review_ai/test_live_harness.py), [service tests](../../tests/review_ai/test_service.py), [utility tests](../../tests/review_ai/test_utility_evaluation.py)의 패턴을 재사용한다. 아래 risk별 focused test와 최소 projector/optional client 연결을 구현하고 repository의 lint/type/dependency gates를 수행한다. 이 단계에서 live network가 필요한 기본 test를 만들지 않는다.
1. **Prove the human workflow.** 사용자가 설정한 대상과 credential로 합성 사례 한 건을 opt-in 실행한다. 프로세스 종료 후 remote record를 조회하고 사람이 다섯 항목을 채점한다. Local revision/invocation/output digest, 원격 연결, mapping 확인과 실패 여부만 필요한 만큼 보존한다. Credential이나 전체 payload/log를 inbox에 복사하지 않는다.
1. **Review and deliver.** 실제 구현 revision에서 independent review와 필요한 재검증을 수행한다. PR 설명은 current scope와 검증 근거, owning artifact 링크로 갱신하고 예전 canonicalization blocker를 제거한다. Commit/push와 PR 상태 변경은 해당 작업 권한과 repository policy를 따른다.

## Validation and Completion

| Risk | Required check | Completion evidence |
| --- | --- | --- |
| Optional boundary regression | SDK 없는 disabled 경로, 기존 accepted/rejected/failure 결과와 local provenance를 검증한다. | Network/client 호출 없이 기존 계약과 harness exit 의미를 유지한다. |
| Data leakage or misattribution | Allowlist 밖 값, oversize payload, 다른 invocation/output과 failed record를 검사한다. | 금지 field가 없고 exact identity/digest가 보존되며 채점 불가 상태가 구분된다. |
| Export failure affects review | Init/projection/export/flush/shutdown 오류와 timeout, 로컬 저장 실패를 각각 주입한다. | Core 의미를 보존하면서 연동 실패를 숨기지 않고 종료한다. |
| Rubric meaning loss | 각 criterion의 점수/근거, 누락·중복·범위 밖 값과 output 연결을 검사한다. | 다섯 항목 모두 충족할 때만 complete이며 incomplete를 성공으로 간주하지 않는다. |
| Live delivery or usability gap | 실제 invocation 하나를 실행하고 프로세스 종료 뒤 원격 record와 human annotation을 확인한다. | 사람이 필요한 근거를 보며 exact output에 채점했고 workflow value 가설을 확인한다. |

Test double과 offline 검증은 live ingestion이나 실제 UI의 사용성을 증명하지 않는다. Live 또는 human annotation을 수행하지 못하면 `Not Verified` 또는 구체적인 blocker로 남기며 첫 slice를 완료했다고 선언하지 않는다. Langfuse 연결 성공만으로 review utility나 MVP 전체 acceptance를 충족했다고 주장하지 않는다.

완료 조건은 **동일 implementation revision의 필요한 checks와 review가 통과하고, 합성 invocation의 원격 표시와 다섯 항목 human annotation을 실제로 확인하며, Langfuse 비활성·실패에도 repository-native 계약이 유지되는 것**이다. 이후 code/base/vendor version이 material하게 바뀌면 영향받는 검증을 갱신한다.

## Deferred Scope

- Completed annotation의 repository one-way import, canonical evaluation 생성과 baseline/candidate 비교 자동화는 제외한다. 실제 수요와 공식 API를 검토하고 별도 scope 결정을 받은 뒤에만 진행한다.
- Langfuse로 prompt authority를 이전하거나 annotation 결과만으로 candidate, recovery 또는 delegation을 승인하지 않는다.
- Automatic LLM judge, Promptfoo, generic evaluator/plugin framework, dataset/experiment platform, custom evaluation UI와 production-grade self-host infrastructure를 만들지 않는다.
- Private/unstable API, scraping, generic two-way synchronization과 future convenience를 위한 core schema 확장은 제외한다.
- 이미 완료된 utility evaluation canonicalization/archive는 #248에서 다시 수행하지 않는다.
