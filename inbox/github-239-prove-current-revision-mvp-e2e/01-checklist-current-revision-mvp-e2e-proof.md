---
type: plan
title: "Current-Revision MVP E2E Proof Checklist"
description: "Executes and records the six canonical MVP acceptance proofs on one repository revision without adding new cross-domain coupling."
---

# Current-Revision MVP E2E Proof Checklist

> [!IMPORTANT]
> 이 문서는 [`docs/mvp.md`](../../docs/mvp.md)의 acceptance를 실행하고 기록하기 위한 non-canonical Inbox artifact다. 새로운 acceptance를 정의하지 않는다.

## Execution Contract

Final proof는 하나의 exact Git revision에서 수행한다.

- Final proof 전에 repository에 필요한 준비 변경을 모두 커밋하고 exact HEAD SHA를 고정한다.
- `docs/mvp.md`의 여섯 acceptance를 모두 같은 revision에서 판정한다.
- 하나의 universal case를 Data Lake, Airflow, Reliability, Review AI 전체에 강제하지 않는다.
- 기존 contract가 identity 연결을 요구하는 boundary에서는 그 identity를 그대로 보존한다. 특히 Reliability의 incident/proposal/approval과 Review AI의 incident/evidence/`RemediationDraft` binding을 독립적인 fixture로 대체하지 않는다.
- Airflow는 Data Lake data plane proof를 담당하며 Reliability control-plane이나 Agentic review를 새 runtime dependency로 연결하지 않는다.
- Deterministic failure를 live model 결과로 보완하지 않는다.
- Live model의 문장 동일성은 reproducibility 조건이 아니다. 입력 provenance, project revision, validation 결과와 invocation evidence를 추적할 수 있어야 한다.
- Test-only bypass, mock authorization 또는 acceptance를 통과시키기 위한 contract 약화는 허용하지 않는다.
- 여섯 acceptance가 모두 `PASS`일 때만 MVP completion을 주장한다.

## Proof Record

Final proof 시작 시 ignored `.local/pr239/proofs/<SHA>/record.json`에 아래 field를 기록한다. 아래 표는 기록 schema이며 실행 결과를 tracked 문서에 다시 쓰지 않는다. PR metadata에 exact proof SHA와 결과 요약을 연결한다.

| Field | Value |
| --- | --- |
| Branch | `mols/test/prove-current-revision-mvp-e2e` |
| Proof revision | `RUNTIME RECORD` |
| Base revision | `main@7497a57bbd2ed03ba6f887611bd32bda3b7e9520` |
| Started at | `RUNTIME RECORD` |
| Environment | `RUNTIME RECORD` |
| Evidence root | `RUNTIME RECORD` |
| Final result | `RUNTIME RECORD` |

## Preflight

Proof revision을 고정하기 전에 실행 준비를 끝낸다.

- [ ] Proposal과 이 checklist를 포함한 필요한 tracked 준비 변경이 모두 커밋됐다.
- [ ] `git status --short`에 의도하지 않은 tracked change가 없다.
- [ ] `git rev-parse HEAD`의 결과를 runtime record의 `Proof revision`에 기록했다.
- [ ] repository environment와 dependency가 현재 revision 기준으로 준비됐다.
- [ ] live invocation에 필요한 `HMDA_AGENTIC_REVIEW_*` 설정과 artifact root가 준비됐다.
- [ ] provider credential을 evidence에 기록하지 않는 경계를 확인했다.
- [ ] 실행 결과를 `PASS`, `FAIL`, `BLOCKED` 중 하나로 기록할 위치를 정했다.

## Deterministic Baseline

먼저 current revision의 일반 regression baseline을 확인한다.

```bash
uv run pytest
```

- [ ] Command가 성공했다.
- [ ] 실패 또는 skip을 acceptance 성공으로 재해석하지 않았다.
- [ ] 실패가 있으면 final boundary proof 전에 원인을 분류했다.

Baseline이 깨져 있으면 live provider invocation으로 이를 보완하지 않는다.

## Acceptance Matrix

아래 command와 evidence는 canonical acceptance를 실행하기 위한 현재 repository entry point다. 같은 behavior를 이미 더 넓은 command에서 검증했다면 중복 실행하지 않아도 되지만, 어떤 실행이 해당 acceptance를 증명했는지는 명시적으로 연결한다.

| Acceptance | Primary execution | Required evidence | Result |
| --- | --- | --- | --- |
| Data Lake proof | deterministic recovery E2E + actual Airflow DAGRun | Source/Bronze state, real dbt staging/mart result, Airflow task/Asset evidence | `RUNTIME RECORD` |
| Reliability proof | deterministic recovery E2E | incident, proposal/approval binding, recovery, re-validation, replay result | `RUNTIME RECORD` |
| Agentic contract proof | Review AI + Runtime AI deterministic suites | structured input/output contract, evidence binding, validation/evaluation, provider-neutral runtime behavior | `RUNTIME RECORD` |
| Live Agentic proof | opt-in live review script | actual provider invocation, project revision, prompt/model/config identity, evidence refs, output, latency, available usage | `RUNTIME RECORD` |
| Safety proof | deterministic recovery safety cases + Review AI authority guards | pre-approval zero mutation, advisory-only AI, rejected/unavailable/invalid AI result grants no recovery authority | `RUNTIME RECORD` |
| Reproducibility proof | focused deterministic rerun | semantically equivalent deterministic result and evidence chain on the same revision; live invocation evidence preserved | `RUNTIME RECORD` |

## Data Lake And Airflow Proof

Deterministic system recovery E2E의 clean data-plane stage는 HMDA-shaped source를 Bronze로 적재하고 real dbt build와 staging/mart 결과를 검증한다. 전체 module은 이후 Reliability와 Safety proof도 함께 포함한다.

```bash
uv run pytest tests/data_operations/test_system_recovery_e2e.py
```

확인한다.

- [ ] Clean source가 expected Bronze partition state로 적재된다.
- [ ] Quality gate와 real dbt build가 clean path에서 성공한다.
- [ ] Candidate/current projection과 staging/mart 결과가 검증된다.
- [ ] Synthetic incident input이 같은 HMDA source/case contract에서 재현 가능하다.

Actual Apache Airflow data-plane boundary는 별도로 실행한다.

```bash
uv run pytest tests/orchestration/test_airflow_dagrun.py
```

확인한다.

- [ ] 실제 Airflow CLI를 통한 DAGRun proof가 성공한다.
- [ ] Ordered promotion에서 raw, gate, analytics task 상태와 순서가 성립한다.
- [ ] Bronze/staging/mart 결과와 Asset update evidence가 일치한다.
- [ ] Blocking quality gate와 dbt failure에서 downstream promotion boundary가 보존된다.
- [ ] Scheduler daemon 또는 distributed executor까지 증명했다고 과장하지 않는다.

Airflow fixture와 Reliability fixture에 하나의 global case identity를 강제하지 않는다. 각 proof가 소유하는 canonical boundary와 oracle을 그대로 사용한다.

## Reliability Proof

`tests/data_operations/test_system_recovery_e2e.py`의 deterministic lifecycle evidence를 사용한다.

확인한다.

- [ ] Controlled `null_spike`가 deterministic evidence로 탐지된다.
- [ ] Incident analysis가 mutation 없이 수행된다.
- [ ] Clean candidate와 exact recovery proposal binding이 검증된다.
- [ ] Proposal과 일치하는 approved action만 recovery를 허용한다.
- [ ] Approved recovery 뒤 target content identity가 expected clean state로 복원된다.
- [ ] Post-recovery quality gate와 lifecycle re-validation이 clean state를 확인한다.
- [ ] Replay가 redundant mutation 없이 reconciliation된다.

여기서 approval의 blocking contract는 proposal-bound authority다. Git revision 자체를 새로운 approval authorization key로 요구하지 않는다.

## Agentic Contract Proof

Default Review AI와 Runtime AI suite는 network provider 없이 deterministic contract를 검증한다.

```bash
uv run pytest tests/review_ai tests/runtime_ai
```

확인한다.

- [ ] `Incident`, `Evidence`, `RemediationDraft` identity binding이 검증된다.
- [ ] Structured review output과 deterministic validation/evaluation이 재현된다.
- [ ] Invalid or mismatched input은 provider invocation 전에 거부된다.
- [ ] Accepted review도 approval, recovery 또는 data mutation authority를 얻지 않는다.
- [ ] Runtime settings와 provider-neutral invocation contract가 검증된다.

## Live Agentic Proof

Deterministic contract가 통과한 뒤에만 실제 provider invocation을 실행한다.

```bash
uv run --env-file .env python scripts/run_agentic_review_live.py
```

실행 전에 확인한다.

- [ ] `HMDA_AGENTIC_REVIEW_LIVE=true`다.
- [ ] base URL, API key, model이 명시돼 있다.
- [ ] tracked worktree가 clean하다.
- [ ] `HMDA_AGENTIC_REVIEW_PROJECT_REVISION`이 `auto`이면 Git HEAD를 사용한다. Explicit value를 사용하는 경우에도 full SHA가 proof revision 및 현재 HEAD와 일치한다.

실행 뒤 확인한다.

- [ ] 실제 provider-started invocation이 발생했다.
- [ ] 결과가 `accepted`이고 structured output, accepted validation과 durable invocation evidence가 일치한다. Typed failure는 진단 근거로 보존하지만 live `PASS`를 충족하지 않는다.
- [ ] invocation evidence에 model/config, prompt identity, project revision, evidence refs, output, latency와 제공 가능한 usage가 남았다.
- [ ] API key 또는 credential이 evidence에 저장되지 않았다.
- [ ] live invocation이 approval, recovery 또는 data mutation을 수행하지 않았다.

Provider 환경 문제로 유효한 invocation을 만들 수 없으면 `BLOCKED`로 기록한다. Deterministic contract failure는 live result와 무관하게 `FAIL`이다.

## Safety Proof

Safety는 별도 AI 품질 점수가 아니라 authority boundary로 판정한다.

Deterministic recovery E2E와 Review AI/Runtime AI suite의 앞선 실행 결과에서 다음 evidence를 연결한다.

- [ ] Rejected approval은 target을 변경하지 않는다.
- [ ] Mismatched proposal identity 또는 action은 recovery를 허용하지 않는다.
- [ ] Agentic output만으로 recovery 또는 data mutation이 실행되지 않는다.
- [ ] Invalid, rejected 또는 unavailable review가 recovery authority를 부여하지 않는다.
- [ ] Provider availability 자체가 deterministic recovery authority를 변경하지 않는다.
- [ ] Approval은 검증된 recovery proposal에 결합된다.

이미 앞선 command가 이 oracle을 검증했다면 safety만을 위해 같은 테스트를 다시 실행하지 않는다. 대신 exact test result와 evidence pointer를 기록한다.

## Reproducibility Proof

Final acceptance 전에 핵심 deterministic boundary를 같은 proof revision에서 다시 실행한다.

```bash
uv run pytest \
  tests/data_operations/test_system_recovery_e2e.py \
  tests/orchestration/test_airflow_dagrun.py \
  tests/review_ai \
  tests/runtime_ai
```

확인한다.

- [ ] Normal, incident, recovery와 주요 failure path가 다시 같은 semantic oracle을 만족한다.
- [ ] Evidence identity와 persisted state의 의미가 첫 실행과 모순되지 않는다.
- [ ] 두 번째 실행 때문에 예상하지 않은 persistent mutation이나 stale state 의존성이 드러나지 않는다.
- [ ] Live model 문장 자체의 동일성을 요구하지 않는다.
- [ ] 앞서 수행한 live invocation evidence가 proof revision과 함께 보존돼 있다.

## Failure Handling

실패 또는 blocker를 발견하면 먼저 아래 record를 남긴다.

```text
Revision:
Acceptance:
Stage:
Command:
Expected:
Observed:
Primary error:
Relevant evidence:
Result: FAIL | BLOCKED
```

같은 PR에서 remediation을 수행하려면 proposal의 admission rule을 모두 만족해야 한다.

- 기존 MVP contract 위반을 proof가 직접 재현했다.
- 새 capability가 아니다.
- 가장 작은 coherent change로 해결할 수 있다.
- 수정 후 새 SHA에서 영향을 받는 proof를 다시 실행할 수 있다.

이 조건을 만족하지 않으면 별도 work unit으로 분리하고 현재 proof는 `FAIL` 또는 `BLOCKED`로 유지한다.

## Final Acceptance

Final proof 종료 시 아래 acceptance별 result와 evidence pointer를 runtime record 및 PR metadata에 기록한다. 이 tracked 표는 실행 schema이며 완료 상태가 아니다.

| Acceptance | Result | Evidence pointer |
| --- | --- | --- |
| Data Lake proof | `RUNTIME RECORD` | `RUNTIME RECORD` |
| Reliability proof | `RUNTIME RECORD` | `RUNTIME RECORD` |
| Agentic contract proof | `RUNTIME RECORD` | `RUNTIME RECORD` |
| Live Agentic proof | `RUNTIME RECORD` | `RUNTIME RECORD` |
| Safety proof | `RUNTIME RECORD` | `RUNTIME RECORD` |
| Reproducibility proof | `RUNTIME RECORD` | `RUNTIME RECORD` |

- [ ] 모든 result가 `PASS`다.
- [ ] 각 evidence pointer가 exact proof revision을 설명한다.
- [ ] Final proof 이후 tracked implementation 또는 repository artifact가 바뀌지 않았다.
- [ ] 변경이 있었다면 최종 SHA에서 baseline, focused rerun, live invocation을 포함한 여섯 acceptance 모두의 근거를 다시 확보했다. 영향받는 proof만의 재실행은 중간 진단이며 final acceptance를 대신하지 않는다.
- [ ] PR metadata의 proof SHA와 validation 상태가 실제 final revision과 일치한다.

하나라도 `FAIL` 또는 `BLOCKED`이면 MVP completion으로 판정하지 않는다.
