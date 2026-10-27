---
type: review
title: Reliability Recovery Current Test Design Review
description: 승인·candidate·partition 및 table 복구의 현행 테스트를 전수 대조하고 과거 finding의 처리와 schema replay 검출력을 기록합니다.
---

# Reliability Recovery Current Test Design Review

> [!NOTE]
> 과거 R1·R2는 #266·#267의 구현과 기존 회귀 테스트로 기해결됐다. R3의 유효한 관측 공백은 기존 schema replay 테스트 한 개를 보강해 닫았다. 네 모듈 79개 사례가 통과했고, 잘못된 replacement 구현은 보강한 oracle에서 실패했다. 새 production 결함은 발견하지 않았다.

- **Target:** Reliability recovery의 approval, staged candidate, content/temporal gate, mutation evidence와 replay.
- **Revision:** `b16ad5734b4a5a35c1db3d12fe03124438e71348`에 이 문서와 아래 한 테스트의 미커밋 변경을 적용한 로컬 검증. 이 baseline은 `main@ea39a4fd6c8f483509cf00a1d1114feb4ef3b686`를 포함한다. 결과는 원격 CI나 최종 PR head의 검증을 대신하지 않는다.
- **Scope:** 아래 네 테스트 파일의 모든 test·parameter·helper를 읽고, [partition Spec](../../../openspec/specs/reliability-recovery-backfill/spec.md), [schema Spec](../../../openspec/specs/reliability-schema-recovery/spec.md), [domain guide](../../../docs/domains/reliability.md) 및 대응 [recovery 구현](../../../src/hmda_reliability/reliability/recovery/)과 대조했다.

## Findings

해결 후 남은 recovery 내부 finding은 없다. 이전 finding과 보강 내역은 다음과 같다.

| ID | Severity | Finding | Action |
| --- | --- | --- | --- |
| R3 | Minor | 반환 label·동일 state만 확인하면 schema replay의 불필요한 replacement를 놓친다 | 기존 replay 테스트에서 replacement 진입을 차단하고 실제 DB와 profile 검증을 유지했다. |

## Inventory And Coverage

실행 사례 수는 parameter 확장 후 수다. 새 test function을 늘리지 않고 기존 function 하나의 oracle만 강화했다.

| File | Cases | Contracts And Scenarios | Independent Oracle And Exclusions |
| --- | ---: | --- | --- |
| [test_approval_backfill_validation.py](../../../tests/reliability/test_approval_backfill_validation.py) | 45 | 미승인·action·proposal·target scope 차단, nested/copy 변조, 정상 year/file 복구, content/temporal CAS, staged 원본 변경, profile·cleanup 실패, before/after/diverged·expired replay, writer 직렬화 | 실제 CSV/Parquet와 DuckDB의 content identity·timestamp·행·schema·sentinel 및 typed failure context. 승인 결정은 fixture다. 실제 human approval와 dbt build는 이 모듈의 범위 밖이다. |
| [test_schema_recovery_candidate.py](../../../tests/reliability/test_schema_recovery_candidate.py) | 8 | schema/content/누락 population 거부, 실패한 dbt evidence 거부, immutable evidence·artifact, 승인 뒤와 export 중 candidate 변경 | 실제 DB로 만든 expected state와 candidate state, 누락 연도, staging artifact의 존재/부재, frozen model의 거부. dbt result는 경계 fixture이며 실제 dbt 성공을 증명하지 않는다. |
| [test_schema_recovery_executor.py](../../../tests/reliability/test_schema_recovery_executor.py) | 25 | exact approval, table 전체·sentinel 복원, year alias/population, before/after/diverged, transaction rollback, cleanup/retry, HMDA writer·dbt lock 직렬화, replacement 없는 replay | 다시 연 DB의 complete state, before-state 보존, profile row count, mutation/stage/action과 thread outcome. dbt subprocess는 통제하며 운영 프로세스 장애 전체를 다루지 않는다. |
| [test_recovery_runtime_evidence.py](../../../tests/reliability/test_recovery_runtime_evidence.py) | 1 | storage 실패 전 overwrite-attempt 로그에 incident/approval/year/table context를 남긴다 | caplog의 한 event와 exact context. staging·identity·approval·loader는 fake이므로 실제 mutation 안전성이나 rollback evidence로 해석하지 않는다. |

### Scenario And Oracle Map

| Contract | Normal And Boundary | Failure And Replay | Oracle |
| --- | --- | --- | --- |
| Exact approval | 정상 승인·required actions, immutable action set | 미승인·다른 action·copy 우회·proposal/target 불일치; schema는 candidate path 접근 전 거부 | domain error와 missing candidate/source 접근 순서. Model 세부 invariant는 [contracts 테스트](../../../tests/reliability/contracts/)가 별도로 소유한다. |
| Candidate identity | complete state와 dbt projection, immutable staged Parquet | equal-count content mismatch, schema mismatch, 누락 partition, 승인 뒤/export 중 변경 | exact complete state와 missing-year evidence, 실패 시 staged artifact 부재 |
| Partition mutation | year 전체와 file-scoped overwrite, 다른 file sentinel, 다른 activity year | diverged target 차단, content/temporal race, 변경된 원본 대신 staged source 사용 | 실제 content identity·ingested timestamp·sentinel 행; file mutation 뒤 profile은 year 전체 3행 |
| Freshness acceptance | content가 같아도 stale before-state는 실제 교체, measured after-state는 독립 content/freshness 성공 | candidate timestamp mismatch/unavailable, max-age와 같은 60분은 replay 거부, temporal race와 profile 실패 | exact timestamp·content, 독립 validation field, 재승인 요구와 completed mutation evidence |
| Profile alignment | source/activity year alias와 숫자상 동등한 DECIMAL(6,0), year observation | 다른 discriminator와 DECIMAL(6,1)의 문자열 population 불일치는 before/replay 모두 거부; empty target/candidate 표현 차이도 거부 | 실제 numeric population과 문자열 population의 2행/0행 차이, mutation 전 행/schema 보존 |
| Mutation evidence | 정상 partition/table 복구의 exact after-state와 profile | profile 실패, target unlock/close 또는 staging cleanup 실패; after-state에서는 replay로 재개 | partition commit은 유지하고 schema transaction 실패는 exact before-state로 rollback. Stage·mutation·reconciliation과 재시도 결과를 실제 DB와 함께 확인 |
| Writer serialization | managed file writer가 profile과 actual identity 산출 뒤에 진행 | profile population이 바뀐 후 replay 거부; schema commit 뒤 stale partition writer 거부; dbt lock 중 target 측정 불가 | event로 경계를 맞추고 thread 종료/error·DB state·profile population을 확인. 분산 writer나 우회 SQL까지 보호한다고 주장하지 않는다. |
| Schema replay | exact after-state에서 profile 2행·partition 2025, exact complete state | `_replace_table` 진입 자체가 실패하도록 하여 동일 내용 재생성을 구별 | replacement 부재의 관측과 다시 연 DB의 state를 결합; 반환 label만으로 판정하지 않는다. |

## Historical Dispositions

[과거 recovery 검토](../01-review-historical/reliability/recovery.md)의 R1–R3와 추가 관찰을 모두 현행 baseline에 대조했다. 과거 재현을 현재 결함으로 재사용하지 않았다.

| Historical Item | Disposition | Current Evidence And Decision |
| --- | --- | --- |
| R1 — staging 종료 후 mutation evidence 소실 | `obsolete` | [#266](https://github.com/mols3131d/hmda-data-reliability/pull/266), commit `08efd160` 반영. Partition의 `test_backfill_preserves_committed_state_on_staging_cleanup_failure`는 before/after × profile 정상/실패 4개 사례에서 commit된 actual state·cause·resume·재시도를 확인한다. Schema의 `test_schema_recovery_preserves_completed_state_on_cleanup_failure`는 before/after × staging/unlock/close 6개 사례에서 exact actual state와 stage·resume·재시도를 확인한다. 두 기존 회귀 모두 이번 79개 실행에 포함됐다. |
| R2 — 다른 profile population의 성공 evidence | `obsolete` | [#267](https://github.com/mols3131d/hmda-data-reliability/pull/267), commit `0725ac14` 반영. 두 API 모두 요청을 source_year로 정렬하고 다른 discriminator를 실행 경계에서 거부한다. Activity year 불일치, file mutation/year profile, DECIMAL population mismatch/동등성, before/replay, writer 직렬화 기존 사례를 확인하고 이번 실행에 포함했다. |
| R3 — schema replay no-replacement 관측 부족 | `accepted` | 아래 기존 replay 테스트 보강으로 처리했다. 올바른 현행 구현은 GREEN, 실제 replacement 뒤 replay label을 반환하는 잘못된 구현은 RED다. |
| Approval/backfill: source 접근 전 차단·copy 재검증 | `accepted` | 기존 정상/불일치/copy 거부 사례를 유지했다. Production 동작을 재구현하는 helper는 추가하지 않았다. |
| Content/temporal CAS: 승인된 staged source·stale/expired 차단 | `accepted` | content와 timestamp를 분리해 확인하는 기존 사례를 유지했다. CAS loader fault는 stale error 번역, 별도 real temporal change는 transaction gate를 검증한다. |
| Post-mutation failure: 실제 identity와 reconciliation 보존 | `accepted` | profile 실패 후 expected/diverged 상태와 retry를 확인한다. R1의 종료 오류 coverage도 합쳐 보되 다른 fault를 동일 원인으로 세지 않았다. |
| Schema candidate: complete population·export 경쟁·immutable evidence | `accepted` | 실제 DB/thread/Parquet 기반 검사를 유지했다. Preflight의 `approval_calls`와 존재하지 않는 target path는 fixture 흐름의 보조 assertion이며 실제 callback/target 접근 instrumentation은 아니다. Preflight API 자체에는 target/approval callback 인자가 없고, 상위 callback 순서는 evaluation이 소유한다. |
| Schema executor: 전체 table·sentinel·rollback·shared lock | `accepted` | 실제 complete state와 rollback 전후 equality를 주 oracle로 유지했다. Profile/identity/파일 실패는 해당 경계에서만 주입한다. |
| Replay: partition no-write의 교차 E2E 보완 | `deferred` | [외부 E2E](../../../tests/data_operations/test_system_recovery_e2e.py)의 before/after ingested timestamp 관측을 읽어 확인했다. 이 PR에서는 수정·실행하지 않았으며 #277의 최종 통합 검증 범위로 남긴다. Partition 전체에 no-write gap이 있다고 확대하지 않는다. |
| Runtime evidence: 로그 unit의 제한 | `accepted` | fake을 사용한 로그 검증임을 inventory에 명시했다. 실제 복구 안전성은 다른 세 모듈의 real local boundary가 증명한다. |

## Adopted Regression

[test_schema_recovery_replays_exact_after_without_replacement](../../../tests/reliability/test_schema_recovery_executor.py)은 다음을 함께 관측한다.

1. target이 exact after-state인 유효 요청에서 `_replace_table`에 진입하면 `pytest.fail("schema replay must not enter table replacement")`로 실패한다. Domain 결과를 반환하는 fake은 사용하지 않는다.
1. 정상 recovery API가 반환한 뒤 별도 DB connection으로 actual complete state를 다시 계산한다.
1. 실제 state, result state와 approved expected after-state가 같고, validation 성공·profile 2행/2025·replay state/action이 유지되는지 확인한다.

검출력은 production 파일을 바꾸지 않는 두 별도 Python process에서 확인했다. 같은 잘못된 public API wrapper는 유효 request와 candidate staging·lock·실제 `_replace_table`을 사용해 target을 재생성한 뒤 result label/action만 `already_restored`·`resume_verification`·profile-only로 바꾼다.

- `git show b16ad5734b4a5a35c1db3d12fe03124438e71348:tests/reliability/test_schema_recovery_executor.py`에서 원래 replay function을 로드해 같은 fixture helper와 실행했다. 원래 assertions가 통과했고 실제 replacement가 1회 완료됨을 별도 counter로 확인했다.
- 보강 후 동일 wrapper를 process 안에서만 대입하고 해당 pytest selector를 실행했다. import/fixture 오류 없이 replacement guard의 명시적 메시지에서 `1 failed`로 실패했다. Driver는 이 의도한 pytest failure를 확인했다. Wrapper와 임시 DB는 저장하지 않았다.

## Validation

독립 worktree의 locked 환경에서 `uv run --no-sync`로 실행했다. Tach impact hint가 표시됐지만 `--tach`를 사용하지 않아 아래 선택 사례를 모두 실행했다.

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | 보강한 replay selector | `uv run --no-sync pytest tests/reliability/test_schema_recovery_executor.py::test_schema_recovery_replays_exact_after_without_replacement` — `1 passed in 0.47s` |
| ✅ Pass | 네 recovery module | `uv run --no-sync pytest tests/reliability/test_schema_recovery_executor.py tests/reliability/test_schema_recovery_candidate.py tests/reliability/test_approval_backfill_validation.py tests/reliability/test_recovery_runtime_evidence.py` — `79 passed in 12.22s` |
| ✅ Pass | 기존 oracle의 알려진 검출 한계 확인 | 잘못된 구현이 실제 table replacement 1회 후 원래 test function의 assertions를 통과 |
| ✅ Pass | 보강 oracle의 negative control | 잘못된 구현에서 pytest `1 failed in 0.44s`, 실패 이유가 `schema replay must not enter table replacement`임을 확인 |
| ✅ Pass | Python 정적 검사 | 변경한 [test_schema_recovery_executor.py](../../../tests/reliability/test_schema_recovery_executor.py)에 Ruff check와 format check 통과 |
| ✅ Pass | 문서·diff 형식 | 이 문서의 `rumdl check`와 담당 변경의 `git diff --check` 통과 |
| ⚪ Not Verified | 외부 E2E·live 환경·원격 CI | 이 담당 범위에서 실행하지 않음. 상위 PR validation과 #277이 별도 소유 |

## Risks And Limits

로컬 관리 writer와 통제된 fault가 검증 범위다. 실제 filesystem 장애 빈도, 모든 cleanup 동시 실패 조합, replay profile 실패 분류 전체, 프로세스 강제 종료·분산 writer·운영 승인 절차를 검증하지 않았다. 내부 replacement helper에 대한 guard는 해당 mutation 진입점을 지키는 회귀 관측이며, 임의로 새 SQL mutation 경로를 추가하는 모든 잘못된 구현의 부재까지 증명하지 않는다.

새 production 수정 인계 항목은 없다. #277에는 예약된 외부 E2E의 실제 integration 실행과 기존 timestamp·quality gate·dbt/replay contract의 통합 보존 확인을 남긴다. 이 report는 해당 E2E가 현재 head에서 통과했다고 주장하지 않는다.
