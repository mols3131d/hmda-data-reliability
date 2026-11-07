---
type: review
title: "Reliability Agentic Implementation Review and Remediation"
description: "PR #284의 로컬 구현과 03 인계의 완료 주장을 검증하고, 확인된 결함의 수정 범위와 재검증 기준을 기록한다."
tags:
  - reliability
  - ai-engineering
  - testing
---

# Reliability Agentic Implementation Review and Remediation

> [!NOTE]
> **Assessment: `clear` for F1~F6 remediation.** 2026-11-07 최초 결함 6건과 교정 중 확인된 잔여 문제를 수정하고, 마지막 독립 재리뷰에서 남은 material current-scope 후보가 없음을 확인했다. 이번 보완은 완료했지만, 실제 profile/dbt integration·W5 Spec/정본 문서·live/human 평가와 PR 승인·Ready/merge는 완료하지 않았다.

- **Target:** [03 Handoff](03-report-reliability-agentic-refactor-handoff.md)의 W1~W4 및 W5 일부 완료 주장과 로컬 구현.
- **Revision:** 최초 검토는 clean HEAD `0b2ac8c86d9fe8e560af0a5ad9b8cf5cf7228a14`, 구현 부모 `c3ac46ad11a9ce90019d9811d746db941438792b`와 로컬 `origin/main` `57cd2bd49aa380273f677719c6b2aa68f49641ee` 기준이었다. 최종 보완은 같은 HEAD 위 working tree이며, 독립 확인의 tracked diff SHA-256은 `8bf2e919b81f6278e3865bc50e75088bc07f0a817a7d10412a0da849baf139ff`다. 이후 편집은 이 판정을 기록하는 Inbox 문서뿐이다.
- **Scope:** 실제 조회, 위임 권한·예산, 실패·변경 상태, 원문·provenance, 평가 결과 이전. 알려진 W5 미완료 자체나 무관한 기존 결함은 새 finding으로 계산하지 않았다.

## Findings

아래는 최초 검토의 결함 기록이며 모두 수정했다. 현재 구현과 검증 결과는 [Remediation Progress](#remediation-progress)를 따른다.

| ID | Severity | Finding | Action |
| --- | --- | --- | --- |
| F1 | Major | 기본 도구가 실제 조회 없이 고정 성공 응답을 생성한다. | 실제 조회를 연결하거나 미설정 도구를 비노출·차단한다. |
| F2 | Major | Task의 허용 도구·호출 수·시간 예산이 실행에 적용되지 않는다. | 위임 제한을 registry와 실행 설정에 강제한다. |
| F3 | Major | 조사 루프가 호출 수·프롬프트 크기 상한을 넘는다. | dispatch 및 provider 호출 전에 상한을 검사한다. |
| F4 | Major | 조사 실패를 완료로 보고하고 복구 후 변경·재개 정보를 버린다. | 실패 상태와 mutation-aware 결과를 구조적으로 보존한다. |
| F5 | Major | 원문 저장 실패·ID 충돌을 숨기고 완료를 반환한다. | 고유 실행 ID, 실패 전달, 원문·이력 참조를 보존한다. |
| F6 | Major | 평가 output에서 조사 내용과 근거가 빠진다. | findings·hypotheses·uncertainties·도구 기록을 회수 가능하게 한다. |

6건 모두 최초 `Disposition: current_required`로 수용해 수정했다. F1~F3의 scope relation은 `explicit_target`, F4~F6은 `acceptance_gap`이다. 기술 구현의 수정 권한은 후속 사용자 요청으로 부여되었으며, Inbox가 정본 권한을 대신하지 않는다.

## Details

### F1: Fabricated Tool Observations

#### F1 Locations

- [Investigation tools](../../src/hmda_reliability/reliability_ai/investigation/tools.py): `ToolRegistry._dispatch`.

#### F1 Evidence

기본 `compare_profiles`는 프로파일 수치 없이 비교 완료 문구를 반환한다. `inspect_dbt_impact`는 `unrelated.asset`에도 `stg_hmda_loans`, `mart_hmda_loan_outcomes`와 고정 test를 `success`로 반환했다. 일반 조사 경로는 handler 없는 기본 registry를 사용한다.

#### F1 Impact

모델이 실제로 관측하지 않은 계통·비교 결과를 근거로 판단할 수 있다. 기존 테스트도 고정 모델 목록을 기대하므로 통과가 실제 조회를 입증하지 않는다.

#### F1 Action

미설정 도구는 노출하거나 실행하지 않는다. 도구 사용 가능 여부, 허용 목록과 인자 스키마를 실행 경계에서도 검증한다. 실제 조회가 연결되지 않았다는 사실은 남은 기능 제한으로 보고한다.

### F2: Unenforced Delegation Limits

#### F2 Locations

- [Execution service](../../src/hmda_reliability/reliability_ai/execution/service.py): `execute_delegated_task`.
- [Task contract](../../src/hmda_reliability/reliability_ai/execution/contracts.py): `TaskEnvelope`.

#### F2 Evidence

`allowed_tools=()`, `max_tool_calls=1`, `workflow_budget_seconds=0.001`인 Task에서도 세 도구가 실행됐다. 실제 요청의 read timeout은 30초였다. Task 제한을 조사 호출에 전달하지 않는다.

#### F2 Impact

상위 요청자가 부여한 조회 권한과 비용 경계를 넘는다. 기존 승인 복구의 `allowed_actions` 검사는 읽기 도구 제한을 대체하지 못한다.

#### F2 Action

Task와 caller 설정의 더 좁은 제한을 적용한다. 허용하지 않은 도구는 provider에 노출하지 않고 dispatch도 차단한다.

### F3: Unenforced Investigation Bounds

#### F3 Locations

- [Investigation service](../../src/hmda_reliability/reliability_ai/investigation/service.py): 도구 dispatch 및 provider 호출.

#### F3 Evidence

`max_tool_calls=1`, `max_prompt_bytes=1`인데 도구 3개를 실행하고 `completed`를 반환했다. 상한 도달 후에도 다음 요청은 `tool_choice="auto"`였다.

#### F3 Impact

한 번의 병렬 도구 응답이나 이어지는 새 도구 요청으로 상한을 넘을 수 있고, 누적 도구 결과가 컨텍스트 한도를 넘는다.

#### F3 Action

개별 도구 실행 전에 잔여 호출 수·시간을 검사한다. provider 호출 전 전체 메시지의 UTF-8 크기를 검사하고, 호출 수 소진 뒤에는 추가 도구를 허용하지 않는다.

### F4: Lost Failure and Mutation State

#### F4 Locations

- [Execution service](../../src/hmda_reliability/reliability_ai/execution/service.py): 조사 결과 처리와 복구 예외 처리.
- [Recovery contract](../../openspec/specs/reliability-recovery-backfill/spec.md): `Mutation-aware recovery result`, `Recovery reconciliation`.

#### F4 Evidence

provider 연결 실패가 `status="completed"`, 빈 facts와 빈 blocked 목록으로 보고됐다. `BackfillValidationError`에 `mutation_state="partition_changed"`, `reconciliation_action="resume_verification"`를 주입했을 때 최종 보고에는 문자열 오류만 남았다. 실제 DB 장애를 일으킨 재현은 아니다.

#### F4 Impact

감독자는 조사 실패를 정상 완료로 오인하거나, 이미 변경된 데이터를 변경 전 실패로 오인해 잘못 재실행할 수 있다.

#### F4 Action

조사 실패를 명시적으로 보고한다. 승인·검증 거부, 변경 후 검증 실패와 정상 성공을 구분하고 도메인이 반환한 변경·재검증·재개 근거를 보존한다.

### F5: Hidden Persistence Failure

#### F5 Locations

- [Investigation service](../../src/hmda_reliability/reliability_ai/investigation/service.py): 원문 저장, invocation ID와 최종 결과.

#### F5 Evidence

저장소가 `InvocationEvidenceWriteError`를 내도 `completed`, `failure_code=None`, `manifest_path=None`이 반환됐다. 동일 incident와 동일 초를 고정한 두 실행 모두 완료됐지만 첫 번째 원문 파일만 남았다. 수집한 turn 기록도 결과에 연결되지 않는다.

#### F5 Impact

완료 결과와 원문이 불일치하거나 조사 경위를 회수할 수 없고, 저장 실패를 감지할 수 없다.

#### F5 Action

실행별 고유 identity와 원문·도구·turn 기록 참조를 보존한다. 저장 실패는 성공으로 숨기지 않고 명시적으로 반환한다. 실패한 조사도 가능한 범위에서 기록을 보존한다.

### F6: Incomplete Evaluation Output

#### F6 Locations

- [Experiment runner](../../src/hmda_reliability/reliability_ai/evaluation/experiment.py): Dataset task output.

#### F6 Evidence

findings·hypotheses·uncertainties를 가진 조사 결과를 가짜 Dataset task로 전달했지만 output은 `status`, `failure_code`, `incident_id`, `tool_calls_count`, `facts`만 남겼고 CLI는 exit 0이었다.

#### F6 Impact

조사의 유용성·불확실성·근거를 같은 평가 결과에서 검토하기 어렵다. 라이브 평가 미실행과는 별도의 결과 계약 결함이다.

#### F6 Action

조사 결과의 핵심 내용과 안전한 근거 참조를 평가 output에 보존하고, output 회수 및 실패 exit-code를 offline에서 검증한다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| Pass | 독립 두 관점 리뷰 | 별도 Verifier와 Challenger가 검토하고 Root가 후보를 통합했다. Caller가 6건을 메모리 probe로 재현했다. |
| Pass | `uv run --no-sync pytest tests/reliability_ai tests/runtime_ai -q --tb=short` | 131 passed. |
| Pass | `uv run --no-sync pytest tests/reliability tests/data_operations tests/orchestration tests/scripts/ci tests/scripts/test_tach.py tests/scripts/test_tach_config.py -q -n auto --tb=short` | 597 passed. |
| Pass | Ruff lint, `ty check`, `tach check` | 최초 reviewed HEAD에서 각각 통과했다. |
| Pass | `uv run --no-sync ruff format --check src tests scripts` | 234 files already formatted. |
| Fail | `uv run --no-sync ruff format --check .` | 변경하지 않은 기존 #269 Inbox 문서 한 곳의 코드 블록 포맷 차이. 이번 PR의 회귀에서 제외했다. |
| Not Verified | 전체 suite, 실제 Ollama·Langfuse, 사람 평가 | 수행하지 않았다. 원격 setup이나 데이터 DB 변경은 하지 않았다. |

최초 조회 시 원격 PR head는 `d8cc1c1e2023c29223bae78179bf3f50872e1c3c`이며 문서 3개만 포함했다. 당시 로컬 구현은 3커밋 앞서 있었으므로 원격 green CI를 이 구현의 검증 증거로 사용하지 않는다. 이번 보완은 커밋·푸시하지 않았다.

## Remediation Plan

2026-11-07 사용자 요청으로 아래 보완에 착수한다. 기존 [01 Plan](01-plan-reliability-agentic-complete-refactor.md)의 전체 PR 목표를 대체하지 않는다.

1. F1~F3: 미설정 도구 차단, 인자 검증, Task 제한 적용, 개별 호출·누적 컨텍스트 상한을 작은 수정과 focused test로 보완한다.
1. F4~F5: 실패 상태와 mutation-aware 근거, 고유 실행 ID·원문·turn 기록을 보존하고 오류 주입·충돌 회귀를 검증한다.
1. F6: Dataset output을 보완하고 offline runner 계약을 검증한다.
1. 관련 domain·소비자 회귀와 정적 검사를 실행한 뒤 수정 상태의 독립 리뷰를 받는다. 결과와 잔여 범위를 이 문서에 갱신한다.

완료 기준은 6건의 재현이 회귀 테스트로 보호되고, 관련 suite·정적 검사와 수정 상태의 독립 리뷰가 통과하는 것이다. 기존 외부 Approval·정본 Recovery API는 유지한다. 커밋·푸시, 원격 Langfuse setup, 실제 DB mutation, W5 전체 Spec·정본 문서·live/human 평가는 이 보완의 완료로 간주하지 않는다.

## Remediation Progress

수정 기준은 같은 HEAD 위의 working tree다. 정본 Recovery API와 provider adapter는 변경하지 않았다.

| ID | Implemented | Regression Evidence |
| --- | --- | --- |
| F1 | handler 없는 profile·dbt 도구를 비노출·차단하고, 실제 dispatch에서 허용 목록과 엄격한 인자 스키마를 검증한다. | 미설정 도구, unrelated asset, 추가·누락·잘못된 타입의 인자 차단. |
| F2 | Task 허용 도구와 caller/Task 중 더 좁은 호출 수·시간 제한을 적용한다. | 빈 허용 목록의 도구 비노출과 1ms 요청 timeout. |
| F3 | 개별 dispatch의 호출 수·시간, 누적 메시지 UTF-8 크기, provider 시작 직전 deadline을 검사한다. | batch 초과 차단, 한도 뒤 no-tools 합성, prompt 초과·preflight 만료 시 provider 미호출. |
| F4 | 조사 실패 뒤 mutation을 중단한다. 복구의 proposal ID, mutation·재개 context와 원래 결과를 보존하고 `failed`·`blocked`·`partial`을 구분한다. | provider 실패 시 복구 미호출, 변경 전·후 backfill/schema 실패, freshness 실패, schema 후보·OS 실패와 정상 profile 근거 보존. |
| F5 | UUID 실행 ID, 원문 경로, assistant/tool turn과 provenance manifest를 연결한다. 저장·파싱 실패는 명시적 오류다. | 같은 clock의 두 실행 원문 구분, response·manifest 저장 오류와 중첩 JSON 실패의 남은 증거 보존. |
| F6 | Dataset task output에 JSON 직렬화된 조사 결과와 도구 호출 수를 반환하고 전체 Dataset 항목 identity를 대조한다. | offline Dataset에서 findings·가설·불확실성·도구 결과·참조 보존과 성공/실패 exit code, 항목 누락·중복 실패. |

관련 테스트는 [Investigation Tools](../../tests/reliability_ai/test_investigation_tools.py), [Investigation Agent](../../tests/reliability_ai/test_investigation_agent.py), [Execution Service](../../tests/reliability_ai/test_execution_service.py), [Experiment Runner](../../tests/reliability_ai/test_experiment_runner.py)에 있다.

### Corrective Review

1차 수정의 독립 DualVantage 리뷰는 tracked diff SHA-256 `de3a0c9071214b573bc87c911b0f9259da2d5fab5d77d4414841bb694d825c74`를 기준으로 수행됐다. 별도 Verifier와 Challenger가 검토하고 Root가 후보를 통합했다. Challenger는 정적 검토만 수행했고, Verifier는 focused 검사 30개와 안전한 재현을 수행했다. Caller는 아래 3건을 모두 기존 권한 안의 `current_required`로 수용했다.

| Candidate | Scope Relation | Evidence and Resolution |
| --- | --- | --- |
| F4 freshness false-success | `acceptance_gap` | `validation_passed=True`, `freshness_validation_passed=False`가 성공으로 보고됐다. 명시적 freshness 실패를 `partial`로 보고하고 도메인 결과를 보존하도록 수정했다. |
| F4 schema candidate exception | `direct_regression` | 좁힌 예외 경계에서 `SchemaRecoveryCandidateError`가 유출됐다. 후보 소실은 `not_started`·변경 전 실패로 context와 함께 보고한다. |
| F2/F3 stale remaining budget | `explicit_target` | preflight 뒤 deadline이 지났는데 이전 잔여 시간으로 provider를 시작했다. `invoke` 직전 재계산과 no-provider 회귀를 추가했다. |

2차 독립 리뷰는 tracked diff SHA-256 `cc332c3001e2b3a474e204178e30b7da13c7baa149e5b8910b77672fdd4ed95f`를 기준으로 위 세 수정의 해결을 확인했다. Verifier는 focused 테스트 35개와 메모리 probe를, Challenger는 정적 검토를 수행했다. 추가로 아래 후보 3건을 확정했으며, Caller는 기존 F3/F4 권한 안의 `current_required`로 수용해 수정했다.

| Candidate | Scope Relation | Evidence and Resolution |
| --- | --- | --- |
| F3 tool preflight deadline | `explicit_target` | 도구 인자 fingerprint 계산 뒤 deadline이 지나도 dispatch를 시작했다. dispatch 직전 재검사와 handler 미호출 clock 회귀를 추가했다. |
| F4 schema OS exception | `direct_regression` | staging의 예상 가능한 `OSError`가 보고서를 건너뛰었다. 좁은 OS 예외 경계에서 `failed`·`not_reported`와 실제 상태 확인 요청을 보존한다. 변경 여부를 추측해 `not_started`로 표시하지 않는다. |
| F4 schema profile evidence | `acceptance_gap` | 정상 schema 복구의 `profile_snapshot`이 보고서에서 소실됐다. 전체 도메인 결과의 JSON을 receipt에 보존한다. |

2차 리뷰의 미확정 중첩 JSON 후보는 Caller가 별도로 검증했다. 깊이 2,000과 Python 재귀 한도에 100을 더한 입력은 이 런타임에서 오류를 재현하지 못했다. Python 3.13.13에서 깊이 16,000·32,001바이트의 JSON은 출력 상한 32,768바이트 안에서 `RecursionError`를 냈다. 도구 인자와 최종 보고서 두 경로에서 manifest 생략을 회귀로 재현한 뒤, 좁은 파싱 경계에서 `invalid_investigation_output`과 원문·manifest를 반환하도록 수정했다. 직접 ToolRegistry 사용의 같은 오류도 검증한다. 이는 F5 증거 보존의 `acceptance_gap`으로 수용했다.

이 수정 뒤 2차 리뷰의 상태 기준은 후속 리뷰로 대체됐다.

3차 독립 리뷰는 tracked diff SHA-256 `8d7017194ceaecb26e6970e4af06ff690f3d465e83a77cfafb34a0d90507ecb6`를 기준으로 위 교정을 확인했다. Verifier는 focused 테스트 41개와 설치 SDK 집계 probe를 수행했고, Challenger는 정적으로 검토했다. Caller는 아래 결과를 구분해 수용했다.

| Candidate | Disposition | Resolution |
| --- | --- | --- |
| F6 missing Dataset results | `current_required` · `acceptance_gap` | Langfuse 4.15.6은 개별 예외 항목을 결과에서 제외한다. 입력과 결과의 항목 ID multiset을 대조해 누락·중복이면 exit 1을 반환한다. |
| F5/F6 unsafe error serialization | `current_required` · `acceptance_gap` | 깊이 300의 facts가 manifest 실패 뒤에도 직렬화 불가 결과에 남았다. 직렬화 불가 payload는 오류 결과로 정규화하고 원문·turn·참조는 유지한다. |
| F4/F5 malformed JSON completion | `current_required` · `acceptance_gap` | 잘못된 JSON을 비정형 summary로 승격하던 경로를 제거했다. JSON 객체가 아니면 `invalid_investigation_output`이며 복구로 진행하지 않는다. |
| F4 final backfill identity I/O | 아래 설명 참조 | 최종 검증에서 정본 Recovery API가 비정형 DB 예외를 낼 수 있다. 위임 계층의 좁은 DB/OS 오류 경계를 보완했다. |

마지막 후보의 보고서 유출은 F4 안의 `current_required`로 보완했다. 알려진 domain context가 없는 DB/OS 오류는 승인·proposal·조사 참조와 `not_reported` 상태, 실제 대상 확인 요청을 남긴다. 하위 Recovery API 내부의 최종 identity I/O에 알려진 mutation state를 결합하는 변경은 수정하지 않은 dependency의 기존 gap이며, 이번 wrapper 보완과 별도 `follow_up` · `contract_dependency`로 남긴다. 이 문서는 하위 API의 모든 오류가 mutation-aware라고 보증하지 않는다.

4차 독립 리뷰는 tracked diff SHA-256 `0ab21fe3cd5084078c360d85e36eb6bd46d21412190b7abcfd83aa20ea393b83`를 기준으로 Dataset 완전성, malformed JSON 차단과 DB/OS 오류 보고를 확인했다. Verifier는 focused 테스트 50개와 SDK mock probe를, Challenger는 정적 검토를 수행했다. 두 관점에서 남긴 같은 직렬화 후보는 한 건으로 통합했다. 거부된 도구 인자에 깊이 300의 추가 필드가 있으면 fallback의 `common.tool_calls`에도 직렬화 불가 payload가 남았다. Caller는 F5/F6의 `current_required` · `acceptance_gap`으로 수용했다.

최신 수정은 개별 도구 기록도 직렬화 가능 여부를 검사한다. 실패한 기록은 호출 ID·이름·지연을 유지한 오류 기록으로 정규화하며, 원래 인자 문자열과 도구 결과 원문은 turn에 보존한다. 깊이 300의 도구 인자·handler 결과 두 경로에서 JSON-safe 오류, 원문·호출 참조와 manifest 회수를 검증했다.

마지막 독립 재리뷰는 상단 revision의 patch와 개별 파일 hash를 시작·종료에 대조했다. Verifier는 focused 테스트 24개와 mixed-record·실행 caller·평가 전달 probe로 마지막 후보의 해결을 확인했다. Challenger는 별도 문맥에서 정적으로 검토했다. 실행 검증은 Verifier만 수행했으며 양쪽이 runtime을 재현한 것으로 계산하지 않는다. Root는 남은 material 후보가 없다고 인계했고, Caller는 기존 독립 리뷰와 최신 closure 근거를 합쳐 이번 보완 범위의 완료 게이트를 닫았다.

최종 source identity의 예로 조사 서비스 SHA-256은 `f7bb82ce371533029cf7ff9a4b05af0416dab543843a226502f6afd0173b70d6`, 대응 조사 테스트는 `b0d1b5c3c9c1f7c7da05e6eadaae4a451405b9bd94b9d83439ae18278c1cf100`, 신규 평가 테스트는 `f494c3826f09709c9b4b1ceb0060bdb72dde1d1dcee550071a6a97e7b096933d`다. 판정 기록 후 source/tests는 변경하지 않았다.

### Corrective Validation

| Result | Check | Evidence |
| --- | --- | --- |
| Pass | 1차 수정의 AI·Recovery·data operations·orchestration·CI/Tach 회귀 | 기존 Validation의 두 pytest 대상 집합을 함께 실행해 750 passed, 162.79초. 이후 위 3건을 추가 수정했으므로 최종 상태의 전체 결과로 사용하지 않는다. |
| Pass | 잔여 3건 수정 후 focused 회귀 | `test_investigation_agent.py`와 `test_execution_service.py`: 22 passed. |
| Pass | 잔여 수정 후 정적 검사 | AI source/tests의 Ruff lint·`ty check` 통과, 34개 파일 포맷 확인. |
| Pass | 2차 리뷰 대상의 관련 전체 회귀 | 754 passed, 148.69초. Ruff 전체 lint·`ty check`·Tach·235개 source/test/script 포맷·`git diff --check` 통과. 이후 추가 수정된 AI 경로는 아래 focused 결과로 구분한다. |
| Pass | 2차 잔여 문제·중첩 JSON 수정 후 회귀 | investigation agent/tools와 execution service의 41개 테스트, AI source/tests lint·타입 검사 통과. |
| Pass | 3차 잔여 문제 수정 후 회귀 | `tests/reliability_ai tests/runtime_ai`: 170 passed. AI source/tests의 lint·타입 검사 및 Tach 통과. 결정론적 Recovery source는 변경하지 않았다. |
| Pass | 4차 잔여 문제 수정 후 focused 회귀 | `test_investigation_agent.py`: 19 passed. 중첩 도구 인자·결과의 JSON-safe fallback과 turn·manifest 보존을 포함한다. AI source/tests lint·타입 검사 통과. |
| Pass | 최종 상태의 AI·runtime 회귀 및 정적 게이트 | 172 passed, 3.13초. `ruff check .`, `ty check`, `tach check`, source/test/script 235개 포맷과 `git diff --check` 통과. |
| Pass | 최종 상태의 독립 재리뷰 | Verifier의 focused 24개와 mock probe, Challenger의 독립 정적 검토. 남은 material current-scope 후보 없음. |
| Pass | 보완 문서 검증 | Inbox 01·03·04의 rumdl 및 native Inbox artifact 계약 검증 통과. |

## Risks and Limits

조사 A와 승인 복구 B의 일치 검사가 wrapper에 없다는 추가 쟁점은 미확정이다. 하위 exact approval gate가 B를 검증하므로 무승인 쓰기 우회로 확정하지 않았다. 무승인 복구 우회와 SDK wire 형식 불일치 가설은 기각했으며, W1 전체 API 의미 보존을 728개 테스트 통과만으로 완전 증명했다고 주장하지 않는다.

기본 profile 비교·dbt impact handler는 연결하지 않았다. 도구가 없는 상태를 실제 조회 성공으로 가장하지 않으며, 실제 integration은 남은 기능 범위다. 동기 provider·handler의 진행 중 작업을 강제 취소하지는 못하고 신규 호출 시작과 늦은 응답 뒤의 진행을 제한한다.

절대 artifact root를 설정하면 Dataset output의 파일 참조도 절대 경로일 수 있다. 1차 독립 리뷰는 로컬 경로 비공개가 정본 요구인지 확정하지 못했으므로 결함으로 수용하지 않았다. 실제 Langfuse 전송과 민감정보 검토는 live/human 평가에서 별도로 확인해야 한다.

마지막 reviewer는 authored 파일·Git·실데이터를 변경하지 않았으나 자동 hook이 Git-ignored agent event log를 추가한 것을 관측했다. 파일시스템 전체 무변경 검토로 표현하지 않는다. 라이브 provider·원격 Langfuse·실데이터 DB 검증과 전체 PR acceptance는 여전히 미검증이다.
