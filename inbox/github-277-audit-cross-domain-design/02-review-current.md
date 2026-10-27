---
type: review
title: Cross-Domain Current Audit and Integration Handoff
description: 현행 main에서 예약 접점 테스트를 보강하고 선행 PR 통합 조건과 source 후속의 범위를 구분합니다.
---

# Cross-Domain Current Audit and Integration Handoff

> [!IMPORTANT]
> **Review readiness: not_ready.** 현재 main 기준의 보강·전체 실행은 완료했지만 #273–#276은 아직 Draft/open이다. 이들의 병합을 요구하는 최종 통합 acceptance는 충족하지 않았다. 아래 실행을 선행 PR이 모두 반영된 최종 검증으로 해석하지 않는다.

- **Target:** [PR #277](https://github.com/mols3131d/hmda-data-reliability/pull/277)의 예약 integration tests, 새 cross-domain regression과 PR-owned Inbox.
- **Revision:** base `be1dca8d044494e92a0d25c791471a41b5d11bcf`; implementation/test head `172a6993c8ad0f564f62c1e7674e410dda9834f0`.
- **Scope:** 예약/신규 test·design 12파일과 read-only support 3파일. Domain 내부 테스트와 production/Spec/CI 설정은 수정하지 않았다.

## Changes and Interface Evidence

| Interface | Current oracle / change |
| --- | --- |
| Source→Bronze→quality gate→dbt→promotion | 기존 실제 system E2E와 실제 DAGRun을 실행했다. 정상 적재와 승인된 복구 이후 mart 결과를 고정 `(year,state,purpose,applications,approvals,denials)` 두 tuple로 보강했다. |
| Operations/Platform→Reliability→approved recovery | 실제 persisted dirty/clean identity, read-only lifecycle, exact proposal binding, rejected/mismatched approval의 zero mutation, revalidation과 replay를 보존했다. |
| Reliability→Review AI→Runtime AI | 실제 detector/draft material에서 default harness/reviewer/adapter/SDK/store를 연결했다. HTTP만 통제하고 200/400/500의 CLI status/typed failure, 실제 HTTP 횟수와 record attempt_count, complete wire payload와 canonical replay/digest를 비교한다. |
| Workflow admission→selection→validation | main PR entry, opened/synchronize/reopened event, path filter 부재와 prospective merge checkout을 고정한다. 실제 runner/classifier 및 기존 step wiring suite를 함께 실행했다. |
| Pytest→telemetry/xdist | serial span assertions는 유지하고 xdist case의 설명을 실제 관측한 compatibility로 좁혔다. |

새 HTTP 테스트는 실제 provider 호출이나 사람 평가가 아니다. Fake approval은 오직 deterministic fixture의 exact proposal contract를 검사하며 사람 승인 증거를 만들지 않는다.

## Historical Adoption

[Historical bundle](01-review-historical/README.md)의 94파일 inventory·954개 실행 수와 과거 mutant는 당시 revision의 자료다. 현재 coverage와 실행 결과는 새로 판정한다.

| Historical item | Decision | Current evidence / owner |
| --- | --- | --- |
| G1/G2 source overlap, mixed source schema | obsolete as outstanding | 최신 main의 #252 수정과 #269의 [최종 검토](../github-269-audit-hmda-data-design/08-review-final-delivery.md)에 회귀·전달 근거가 있다. |
| G3/G4/G5/G6 recovery cleanup/profile scope, lineage shape, failed evaluation | obsolete as original finding | #252와 #272의 [현행 검토](../github-272-audit-reliability-design/02-review-current/README.md)를 적용한다. 별도 후속 graph policy/Spec gap까지 해결됐다는 뜻은 아니다. |
| G7 / Review AI AI1 | deferred / scope_decision | 유효 input의 개별 metadata facts 초과가 raw ValidationError라는 새 probe를 #273에서 확인했다. Provider/store 0회; Review AI source owner 필요. |
| G8 / S1 / CI C1 | deferred / scope_decision | 세 uncertainty CLI probe에서 full_tests/full_type=true지만 openspec_bulk=false, Change targets 비어 있음. Tooling source owner가 fallback을 결정·수정해야 한다. |
| Operations D1 results-only identity | obsolete as outstanding | 최신 main의 manifest/results 각각 단독 drift oracle가 이미 보호한다. #275에서 다시 확인했으며 중복 구현하지 않는다. |
| Review AI AI2/AI3/AI4 | accepted in #273 | Service capture/replay, provided-but-omitted citation, heterogeneous criterion score oracle를 보강했다. 해당 PR 미병합이므로 위 전체 suite에는 아직 포함되지 않는다. |
| Runtime token/UTF-8 gaps | accepted in #274 | Non-default token wire와 UTF-8 byte limit을 보강했다. #274 미병합이다. |
| S2 / CI C2 | accepted / implemented | PR trigger/path-filter/prospective merge assertions를 추가했다. 임시 workflow의 paths-ignore·PR-head-ref·closed-only event 세 negative control을 새 witness가 모두 거부했다. Hosted event 실험은 아니다. |
| S3 / S5 | accepted in #276 | Bootstrap public main failure와 enabled/disabled/root literal Rule oracle. #276 미병합이다. |
| S4 empty YAML scalar | deferred / scope_decision | Reviewer가 public validator에서 comment-only null, 빈 quoted scalar 뒤 comment 세 사례의 errors=[]를 새로 확인했다. Tooling source owner 필요. |
| S6 xdist claim | accepted / implemented | 실제 assertion에 맞게 설명을 compatibility smoke로 한정했다. |

## Scope Decisions and Preserved Follow-ups

PR #272의 [최신 handoff](../github-272-audit-reliability-design/02-review-current/README.md#handoff)는 일반적인 “#277 인계” 문구가 exclusive write 목록을 확대하지 않는다고 정정했다. 현재 #277은 위 source 문제를 취합하며 source/Spec/lefthook을 수정할 권한을 새로 만들지 않는다. 다음은 아직 해결하지 않았다.

- **Review AI source owner:** AI1의 typed per-evidence rejection. 총 context overflow와 무관한 ValueError 전파는 보존해야 한다.
- **Tooling owner:** C1의 uncertain inventory fail-safe와 S4의 actual YAML nonempty validation.
- **Shared tooling owner:** #270 F3/#272 H4의 hook Git-local 환경 누수. 이번에는 외부 임시 `uv` wrapper로 child boundary에서 `git rev-parse --local-env-vars` 전체를 제거했다. Hostile Git-local environment를 넣은 private init/add/commit probe와 parent HEAD/index 불변을 확인했다. 영구 hook 수리는 아니다.
- **Existing domain/source owners:** #269 H5/S1, #271 C11 lock symlink, #272 graph policy와 누락 THEN은 각각의 current handoff에 남긴다. 과거 또는 타 작업의 재현을 이번 실행으로 세지 않는다.

## File Coverage

아래는 현행 target inventory다. 두 specialist가 각자 15/15파일을 reviewed로 확인했으며 제외·미검토 파일은 없다.

| File | Contract / oracle |
| --- | --- |
| [tests/data_operations/test_quality_gate.py](../../tests/data_operations/test_quality_gate.py) | 전체 Bronze partition, requested/non-requested dirty, canonical source, missing/null partition |
| [tests/data_operations/test_system_recovery_e2e.py](../../tests/data_operations/test_system_recovery_e2e.py) | 실제 CSV→DuckDB→gate→dbt→promotion→lifecycle→exact approval→recovery→revalidation/replay; literal mart outcomes 보강 |
| [tests/data_operations/test_system_recovery_e2e.design.md](../../tests/data_operations/test_system_recovery_e2e.design.md) | scenario, human/live exclusion, 고정 end-to-end outcome oracle |
| [tests/orchestration/test_airflow_dagrun.py](../../tests/orchestration/test_airflow_dagrun.py) | 실제 Airflow CLI 다섯 경로, SQLite task/events, data/bytes, timeout/cleanup/isolation |
| [tests/orchestration/test_airflow_dagrun.design.md](../../tests/orchestration/test_airflow_dagrun.design.md) | CLI 관측 경계와 fixture/isolation/exclusion |
| [tests/orchestration/test_airflow_execution.py](../../tests/orchestration/test_airflow_execution.py) | wrapper delegation, event payload, skip, failure cause |
| [tests/review_ai/test_live_harness.py](../../tests/review_ai/test_live_harness.py) | opt-in/config/revision/provenance 실패; 공유 environment helper |
| [tests/review_ai/test_runtime_integration.py](../../tests/review_ai/test_runtime_integration.py) | 신규 실제 Review AI/SDK/store, HTTP 200/400/500, wire/replay/attempts/secret oracle |
| [tests/scripts/ci/test_ci_classifier_openspec.py](../../tests/scripts/ci/test_ci_classifier_openspec.py) | 정상 pairing/bulk/archive; uncertainty source defect는 후속 |
| [tests/scripts/ci/test_ci_steps.py](../../tests/scripts/ci/test_ci_steps.py) | 실제 Git, path/exit, external argv stub, OpenSpec modes |
| [tests/scripts/ci/test_ci_workflow.py](../../tests/scripts/ci/test_ci_workflow.py) | workflow trigger/filter/ref 신규 oracle와 기존 wiring/pinning/failure |
| [tests/test_pytest_opentelemetry.py](../../tests/test_pytest_opentelemetry.py) | 실제 serial span oracle와 xdist compatibility; 과장된 설명 축소 |
| [tests/scripts/ci/conftest.py](../../tests/scripts/ci/conftest.py) | read-only support; Git/tool/OpenSpec fixtures |
| [tests/scripts/ci/helpers.py](../../tests/scripts/ci/helpers.py) | read-only support; classifier/runner subprocess와 Git |
| [tests/review_ai/conftest.py](../../tests/review_ai/conftest.py) | read-only support; 실제 detector/draft의 deterministic material |

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | Current full non-resource suite | `uv run --no-sync pytest --testmon --testmon-forceselect -q -ra`: **1,162 passed, 3 skipped, 1 warning (251.39s)**. 새 private cache에서 전체 1,165개를 실행/skip했으며 main+#277의 `87c4ec31c91419401eca3291eb443d7581922e2a`에 한정한다. 이후 변경은 required event assertion 3행뿐이며 아래 focused 검증으로 확인했다. |
| ✅ Pass | Final workflow delta | `172a6993c8ad0f564f62c1e7674e410dda9834f0`에서 workflow module **54 passed (3.67s)**. Closed-only negative control을 거부하고 default/explicit required event controls는 수용했다. |
| ✅ Pass | Changed Python | 변경 4파일의 Ruff check/format check와 ty check 통과. pre-commit도 통과했다. |
| ✅ Pass | Workflow negative controls | 임시 사본의 paths-ignore 추가, PR head checkout, closed-only event를 각각 신규 witness가 거부했다. 원본 workflow는 수정하지 않았다. |
| ✅ Pass | Git environment isolation | Hostile parent env 아래 child의 Git-local 변수 0개, private init/add/commit 성공, parent HEAD/index bytes 불변. |
| ❌ Fail | Existing C1 uncertainty contract probe | Missing inventory / symlinked Change / invalid related path 모두 exit0, openspec_bulk=false와 empty Change targets. 위 source scope decision으로 남긴다. |
| ✅ Pass | Artifact mechanics | Native rumdl, Inbox validator, 실제 YAML parser의 필수값 검사, local links와 git diff check 통과. |
| ⚪ Not Verified | Final merged prerequisites | #273–#276 미병합. 병합 후 최신 main에서 새 통합 revision의 전체 suite와 CI를 다시 확인해야 한다. |
| ⚪ Not Verified | Environment-dependent tests | Optional Langfuse SDK 부재, cached zizmor actual audit, Windows npm/Node 세 항목 skip. Fork test의 multithreaded process DeprecationWarning 1개는 통과와 별도로 기록한다. |

## Current Review

**Assessment: clear.** Review-lead가 quality/adversarial 두 specialist의 독립 결과를 조정했다. 정확한 reviewed implementation head는 `172a6993c8ad0f564f62c1e7674e410dda9834f0`이며 base는 `be1dca8d044494e92a0d25c791471a41b5d11bcf`다. 예약/신규 test·design 12개와 support 3개를 각 관점에서 모두 full-body 검토했다. 87c4ec31의 전체 본문과 172a6993의 event assertion 3행을 구분해 확인했다.

수용한 공백은 닫혔고 남은 `current_required` finding은 없다. Source/공유 tooling 후속은 `follow_up / scope_change`로 분리했다. Reviewer는 suite를 재실행하지 않았으며 위 실행 결과는 coordinator evidence다. Test delta clear와 별개로 선행 #273–#276 미병합에 따른 통합 readiness는 **not_ready**다.

최종 Inbox-only delivery는 이 head의 test/source/Spec blob을 보존한다. 전달 후 exact remote head, prospective merge CI와 review readiness는 [현재 PR 본문](https://github.com/mols3131d/hmda-data-reliability/pull/277)에서 확인한다. Draft/Ready/approval/merge를 자동 전환하지 않는다.

## Next Action

1. #273–#276의 current test delta·CI·인간 검토를 각각 완료한다. 인간의 명시적 lifecycle 결정 후 main에 반영한다.
1. 최신 main을 이 branch에 merge하고 관련 source/test blobs와 위 disposition을 재확인한다. 타 PR branch를 임의로 한데 합치지 않는다.
1. 새 prospective merge에서 full non-resource suite·CI와 필요한 independent review를 확인하고 #277의 readiness를 다시 판정한다.
1. Source/tooling 후속을 수정하려면 owner와 구체적 write scope를 먼저 정한다. 이번 임시 wrapper·green test suite를 영구 수리 증거로 사용하지 않는다.
