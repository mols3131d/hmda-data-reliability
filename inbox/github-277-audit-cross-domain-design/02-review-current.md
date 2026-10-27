---
type: review
title: Cross-Domain Final Integration Audit
description: 선행 PR 병합을 반영한 cross-domain 통합 revision의 계약 보존, 검증, 독립 리뷰와 전달 근거를 기록합니다.
---

# Cross-Domain Final Integration Audit

> [!IMPORTANT]
> **Review readiness: ready.** 선행 #269–#276을 반영한 최종 통합 실행, 독립 리뷰와 아래 exact base/head의 prospective merge CI를 확인했다. Inbox-only 전달은 검증한 실행 대상 blob을 보존하며, 최종 delivery head의 CI는 PR 본문에서 재확인한다. PR은 Draft이며 Ready 전환·approval·merge는 별도 인간 결정이다.

- **Target:** [PR #277](https://github.com/mols3131d/hmda-data-reliability/pull/277)의 exclusive integration test lane와 PR-owned Inbox.
- **Base:** `66f6372cc58d34ad469acee56202eed040a9a5d7`.
- **Execution/review head:** `2665ce7d45c4d74ada3105374123b12e2d2bde70`. 기존 head `35e100a74ab4a44f408df5e2acc158fd6dad993a`에 최신 main을 additive merge했다.
- **Boundary:** 이번 continuation의 authored delta는 이 PR의 Inbox다. Production/Spec/shared CI·hook·domain-owned unit tests를 변경하지 않는다. 전달 head의 정확한 revision과 원격 CI는 PR 본문에서도 재조회한다.

## Prerequisite Integration

2026-10-27 원격 조회와 main의 first-parent history에서 8개 PR의 병합을 확인했다.

| PR | Merge commit |
| --- | --- |
| [#269](https://github.com/mols3131d/hmda-data-reliability/pull/269) | `d6e5e31fbadbe3d1c63b67810ccf3fc3fb2760dc` |
| [#270](https://github.com/mols3131d/hmda-data-reliability/pull/270) | `ac3a2ab7f12036de69d21b1d9f6bf135c85a4075` |
| [#271](https://github.com/mols3131d/hmda-data-reliability/pull/271) | `15e2164697a8f086abbc20e05147a2b54b842fd4` |
| [#272](https://github.com/mols3131d/hmda-data-reliability/pull/272) | `be1dca8d044494e92a0d25c791471a41b5d11bcf` |
| [#273](https://github.com/mols3131d/hmda-data-reliability/pull/273) | `22fca0e3e4c145f1af71512dbe18ff1e561c5d4c` |
| [#274](https://github.com/mols3131d/hmda-data-reliability/pull/274) | `cdfedf054e92ae19d458ba9a960d8d7b4a53c0b2` |
| [#275](https://github.com/mols3131d/hmda-data-reliability/pull/275) | `42bf2aa5db80b97694f01ee80acbe6cb3bde1e60` |
| [#276](https://github.com/mols3131d/hmda-data-reliability/pull/276) | `66f6372cc58d34ad469acee56202eed040a9a5d7` |

`35e100a7..2665ce7d`의 executable delta는 선행 PR의 [service](../../tests/review_ai/test_service.py), [utility evaluation](../../tests/review_ai/evaluation/test_utility_evaluation.py), [SDK provider](../../tests/runtime_ai/test_provider.py), [bootstrap](../../tests/scripts/test_bootstrap.py), [Rule index](../../tests/scripts/test_generate_agent_routes.py) 테스트 5파일이다. 실제 provider 입력·저장 provenance 일치, 제외 evidence 인용 거부, criterion별 score 귀속, 명시 token·UTF-8 bytes, 첫 실패 중단과 enabled Rule의 고정값 oracle가 추가됐다. #275는 문서만 변경했다.

이 구간의 `src/`, `openspec/`, `dbt/`, `scripts/`, workflow, dependency와 shared hook/config delta는 없다. 따라서 아래의 기존 source 후속을 해결했다고 해석하지 않는다.

## Interface Evidence

| Interface | Current oracle |
| --- | --- |
| Source→Bronze→quality gate→dbt→promotion | 실제 system recovery E2E와 Airflow DAGRun. 정상·승인된 복구 이후 mart의 고정 두 tuple을 확인한다. |
| Operations/Platform→Reliability→approved recovery | Persisted dirty/clean identity, read-only lifecycle, exact proposal binding, rejected/mismatched approval의 zero mutation, revalidation과 replay. |
| Reliability→Review AI→Runtime AI | 실제 detector/draft→harness/reviewer/adapter/SDK/store를 연결하고 HTTP만 통제한다. 200/400/500의 typed failure, wire payload, actual attempt count, canonical replay/digest와 secret 부재를 비교한다. |
| Workflow admission→selection→validation | main PR entry·required events·무경로필터·prospective merge checkout과 실제 classifier/runner wiring. |
| Pytest→telemetry/xdist | Serial span contract와 xdist compatibility smoke. Worker span export의 완전성은 주장하지 않는다. |

새 HTTP 테스트는 외부 provider 호출이 아니다. Fake approval은 exact proposal 계약만 검사하며 사람 승인 증거가 아니다.

### Reliability H3 Mapping

[PR #272 H3](../github-272-audit-reliability-design/02-review-current/README.md#pr-277-handoff)의 reserved integration과 lower-level 회귀를 이번 전체 실행에 연결한다. 새 통합 test를 중복 작성하지 않는다.

| Handoff contract | Owning regression / integration | Evidence boundary |
| --- | --- | --- |
| Results-only identity | [test_projection_identity_distinguishes_artifact_pairs](../../tests/data_platform/test_artifacts.py)의 `results-only` | Artifact pair의 results bytes만 바뀌어도 identity가 달라진다. Lifecycle caller의 projection 전달은 source 대조이며, lifecycle 결과의 results-only 변화에 대한 별도 E2E assertion으로 세지 않는다. |
| Stale results-only promotion | [test_promotion_rejects_artifacts_changed_after_verification](../../tests/data_operations/test_dbt_runner.py)의 `run_results_path` | 실제 promotion API가 거부하고 기존 current pair bytes와 파일 상태를 보존한다. |
| Partition replay no-write | [test_deterministic_system_recovery_e2e](../../tests/data_operations/test_system_recovery_e2e.py)의 S7, [test_recovery_resumes_verification_without_repeating_overwrite](../../tests/reliability/test_approval_backfill_validation.py) | 전체 경로에서는 ingested timestamp 불변·already_recovered·실제 identity를 확인한다. 소유 회귀의 replay result/action을 [executor의 overwrite 분기](../../src/hmda_reliability/reliability/recovery/executor.py)와 정적으로 대조했다. 소유 회귀만으로 mutation 진입점 미호출을 직접 계측했다고 주장하지 않는다. |
| Partition cleanup failure | [test_backfill_preserves_committed_state_on_staging_cleanup_failure](../../tests/reliability/test_approval_backfill_validation.py), [test_backfill_unlock_failure_preserves_completed_result_and_can_replay](../../tests/reliability/test_approval_backfill_validation.py) | Before/after·profile failure 조합 및 freshness replay에서 fault를 resource 경계에만 주입한다. Typed error의 실제 committed identity·reconciliation과 다음 replay 성공을 검사한다. |
| Schema cleanup failure | [test_schema_recovery_preserves_completed_state_on_cleanup_failure](../../tests/reliability/test_schema_recovery_executor.py) | Unlock/close/staging × before/after의 실제 DB 상태·typed metadata·replay를 검사한다. |

위 owning node는 모두 `2665ce7d`의 전체 suite에 포함됐다. Cleanup API가 반환하는 typed failure는 [null-spike evaluator](../../src/hmda_reliability/reliability/evaluation/null_spike.py)의 `evaluate_null_spike_vertical_slice`와 [volume-drop evaluator](../../src/hmda_reliability/reliability/evaluation/volume_drop.py)의 `evaluate_volume_drop_vertical_slice`에서 `(ApprovalGateError, BackfillValidationError)`를 받아 `_failure_result`로 전달하는 source 경로와 대조했다. [Replay profile-failure 전달 회귀](../../tests/reliability/test_null_spike_evaluation.py)와 [완료 recovery evidence 보존 회귀](../../tests/reliability/test_evaluation_report.py)도 전체 실행에 포함됐다.

이는 API cleanup fault 주입과 evaluator의 typed-error routing을 조합한 근거다. Evaluator별 cleanup fault 주입, 모든 context field의 end-to-end 보존, 실제 dbt/Airflow/evaluator 전체 경로의 동시 fault E2E까지 검증했다고 확대하지 않는다.

## Historical Adoption

[원래 historical bundle](01-review-historical/README.md)과 [이전 current audit](https://github.com/mols3131d/hmda-data-reliability/blob/35e100a74ab4a44f408df5e2acc158fd6dad993a/inbox/github-277-audit-cross-domain-design/02-review-current.md)은 각 revision의 기록이다. 과거 실행 수와 negative control을 이번 실행으로 재사용하지 않는다.

| Item | Decision | Evidence / owner |
| --- | --- | --- |
| G1/G2 source overlap·mixed schema | obsolete as outstanding | #252 수정과 병합된 #269의 [최종 검토](../github-269-audit-hmda-data-design/08-review-final-delivery.md). |
| G3–G6 cleanup/profile scope·lineage container·failed evaluation | obsolete as original finding | #252와 병합된 #272의 [현행 검토](../github-272-audit-reliability-design/02-review-current/README.md). Individual graph policy·Spec·reporter 후속은 별개다. |
| G7 / Review AI AI1 | deferred / scope_decision | 개별 evidence facts overflow의 typed rejection은 [#273 source 후속](../github-273-audit-review-ai-design/02-review-current.md). Source blob은 변하지 않았으며 이번에 probe를 재실행하지 않았다. |
| G8 / S1 / CI C1 | deferred / scope_decision | Uncertain OpenSpec inventory의 fail-safe는 tooling owner. 이전 세 CLI probe와 해당 source가 보존됐다. |
| Operations D1 results-only identity | obsolete as outstanding | [Dbt runner 회귀](../../tests/data_operations/test_dbt_runner.py)의 manifest/results 각각 단독 drift 거부·기존 bytes 보존을 현재 실행에 포함한다. |
| Review AI AI2/AI3/AI4 | accepted / merged | #273의 provider capture/replay·omitted citation·criterion score oracle를 최종 통합했다. |
| Runtime token/UTF-8 gaps | accepted / merged | #274의 explicit token wire·UTF-8 byte limit oracle를 최종 통합했다. |
| S2 / CI C2 | accepted / implemented | #277의 workflow entry/events/path-filter/checkout oracle. 이전 negative control은 이전 revision의 근거로 보존한다. |
| S3 / S5 | accepted / merged | #276의 bootstrap public main 실패 중단·enabled Rule literal oracle를 최종 통합했다. |
| S4 empty YAML scalar | deferred / scope_decision | 실제 YAML nonempty 판정은 [#276 source 후속](../github-276-audit-common-support-design/02-review-current.md#source-follow-up). 이번 문서는 별도의 실제 YAML parser로 검사한다. |
| S6 xdist claim | accepted / implemented | #277에서 관측 범위를 compatibility로 한정했다. |

## Preserved Source Follow-ups

일반적인 “#277 인계” 문구는 exclusive write 목록을 확대하지 않는다. 아래는 현재 test diff의 blocker와 구분한 미해결 후속이다.

- **Review AI source owner:** AI1의 typed per-evidence rejection. Context overflow와 무관한 ValueError 전파는 보존해야 한다.
- **Tooling owner:** C1의 uncertain inventory fail-safe, S4의 YAML nonempty validation.
- **Shared tooling owner pending:** #270 F3/#272 H4의 hook Git-local 환경 누수. 이번에도 외부 임시 wrapper로 child boundary에서 Git-local 변수를 전부 제거한다. 영구 hook 수정이 아니다.
- **Existing source/Spec/report owners:** #269 H5/S1, #271 C11 lock symlink, #272 graph policy·누락 THEN·C16 reporter. 각각의 current handoff를 유지하며 이번 full-suite GREEN으로 해결됐다고 주장하지 않는다.

## File Coverage

기존 독립 검토 head `172a6993c8ad0f564f62c1e7674e410dda9834f0`와 통합 head `2665ce7d45c4d74ada3105374123b12e2d2bde70`의 아래 15/15 Git blob이 같다. 기존 전체 본문 검토를 재사용하며, 선행 PR의 변경 테스트 5파일과 최종 통합 증거는 이번 독립 리뷰에서 다시 대조한다.

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
| ✅ Pass | Final full non-resource suite | `2665ce7d45c4d74ada3105374123b12e2d2bde70`에서 새 private `TESTMON_DATAFILE`로 `uv run --no-sync pytest --testmon --testmon-forceselect -q -ra -p no:sugar`: **1,167 passed, 3 skipped, 1 warning / 378.17s**. 총 1,170개를 실행/skip했으며 affected-test cache의 선택 생략 결과가 아니다. 실제 dbt system E2E·Airflow CLI 5경로와 H3 owning 회귀를 포함한다. |
| ✅ Pass | Changed Python | 원 PR 변경 4 Python의 Ruff check/format check와 관련 scope ty check 통과. |
| ✅ Pass | Project-wide type | Classifier의 `full_type=true`에 맞춰 `uv run --no-sync ty check` 전체 실행 통과. |
| ✅ Pass | Git environment isolation | Hostile parent env에서 `git rev-parse --local-env-vars` 전체 제거, private init/add/commit 성공, parent HEAD/index 불변. |
| ✅ Pass | Revision applicability | 기존 검토 target 15/15 blob 동일, source/Spec/shared execution delta 없음. Classifier `full_tests=true`, `full_type=true`. |
| ✅ Pass | Artifact mechanics | rumdl 9파일, native Inbox 7문서, 실제 YAML 필수 nonempty 6문서, local link 목적지와 `git diff --check` 통과. 최종 전달 전 다시 확인한다. |
| ✅ Pass | Current integration CI | [CI Lite 40516350418](https://github.com/mols3131d/hmda-data-reliability/actions/runs/40516350418): **1,167 passed, 3 skipped / 166.38s**. Head `2665ce7d45c4d74ada3105374123b12e2d2bde70`, base `66f6372cc58d34ad469acee56202eed040a9a5d7`, prospective merge `99b7ef9cdd7c8ddffb13a9b00788342233903f3f`. Job log에서 checkout·`FULL_TESTS=true`·`FULL_TYPE=true`, Ruff/format 4파일·전체 ty의 성공을 확인했고 merge parents를 별도 API로 대조했다. |

### Skips And Limits

- Optional Langfuse SDK 부재: [test_langfuse_projection.py](../../tests/review_ai/evaluation/test_langfuse_projection.py)의 media API contract 1개.
- Cached `zizmor@1.30.1` 부재: [test_ci_steps.py](../../tests/scripts/ci/test_ci_steps.py)의 actual audit 1개.
- Windows runtime 부재: [test_commands.py](../../tests/scripts/test_commands.py)의 npm/Node 경로 1개.
- [test_duckdb.py](../../tests/data_platform/test_duckdb.py)의 fork lock 회귀에서 multithreaded fork DeprecationWarning 1개. 통과와 구분해 기록한다.

`memory`/`stress`, 운영 scheduler/distributed executor, 실제 외부 provider·외부 ingestion·사람 rubric 평가는 이 검증의 범위 밖이다. Fixture HTTP나 approval을 실제 서비스·사람의 성공으로 승격하지 않는다. Editor diagnostics 도구가 이 runtime에 없어 별도 editor 검증은 수행하지 않았으며 실행한 lint/type/native 문서 검사를 근거로 삼는다.

## Current Review And Handoff

**Assessment: clear.** 별도 review-lead가 quality/adversarial의 독립 결과를 조정했다. Reviewed base는 `66f6372cc58d34ad469acee56202eed040a9a5d7`, head는 `2665ce7d45c4d74ada3105374123b12e2d2bde70`이며 현재 보고서의 H3 문구까지 대조했다. Confirmed `current_required`와 독립 리뷰 coverage blocker는 없다.

기존 15파일의 전체 본문 리뷰는 동일 blob을 확인해 재사용했다. 이번 adversarial coverage는 7파일 full-body·8파일 targeted이고, 선행 PR의 테스트 5파일은 changed hunk와 관련 fixture/caller를 대조했다. 이번에 15/15 또는 5모듈을 모두 새로 전수 검토했다고 주장하지 않는다. Lead는 전체 suite log와 revision/diff/caller를 직접 확인했고 suite를 재실행하지 않았다. Ruff/type와 문서 검사는 coordinator evidence다.

H3의 accepted evidence는 primitive→caller→E2E와 API fault→evaluator 정적 경로를 구분한다. Lower replay의 action/result를 overwrite 미호출의 직접 계측으로 과장한 문구는 보정했다. 이 보정은 문서에 한정되며 source/test 변경은 없다. 기존 source 후속은 `follow_up / scope_change`로 유지한다.

[Plan](00-plan-cross-domain-tests.md)의 마지막 통합 acceptance까지 충족했다. Integration head push의 기존 hook은 캐시상 changed files 0으로 test 0개를 선택했다. 이 hook 결과를 전체 실행 통과로 세지 않으며, parent HEAD/index/config 불변을 확인했다.

최종 전달은 이 PR의 plan/report/README만 변경한다. `2665ce7d` 대비 실행 대상 전체 blob 동일성을 확인하고 commit/push 후 [PR 본문](https://github.com/mols3131d/hmda-data-reliability/pull/277)에서 exact delivery head·prospective merge CI와 review readiness를 다시 고정한다. 현재 통합 범위에 남은 필수 구현 작업은 없으며, 다음 인간 결정은 review/Ready/approval/merge다. Preserved source follow-up은 별도 owner·write scope를 먼저 정한 후 진행한다.

**Run:** Main Loop Review 1/30 accepted. Finalize는 Inbox-only commit/push와 최종 원격 head/CI 확인에 한정한다.
