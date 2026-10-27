---
type: review
title: Current Reliability Evaluation Test Design Audit
description: 현행 evaluation 테스트와 설계를 전수 검토하고 E1 기해결, E2 및 빈 집계 회귀 보강의 검출력을 기록합니다.
---

# Current Reliability Evaluation Test Design Audit

기존 E1은 #265에서 해결됐으며 현행 회귀가 실패 case에서 property·집계·Markdown까지 연결한다. E2는 여전히 유효한 테스트 gap이어서 다중 항목의 부분 충족 반례를 추가했다. 정본의 빈 case 목록 시나리오에도 최소 oracle을 추가했다. Production 결함은 이번 evaluation 조사에서 새로 확정하지 않았다.

- **Target:** Reliability evaluation의 case/report와 volume/null/schema/freshness 평가.
- **Revision:** `b16ad5734b4a5a35c1db3d12fe03124438e71348` + 이 PR의 test-only working diff. 해당 commit은 `main@ea39a4fd6c8f483509cf00a1d1114feb4ef3b686`을 포함한다.
- **Scope:** 아래 4개 test module 전체 59개 test function과 freshness design 전체. Parameter 확장 후 focused 실행은 77개다.
- **Authority:** 현재 [plan](../00-plan-reliability-tests.md), [evaluation Spec](../../../openspec/specs/reliability-evaluation-report/spec.md), [backfill Spec](../../../openspec/specs/reliability-recovery-backfill/spec.md), [schema recovery Spec](../../../openspec/specs/reliability-schema-recovery/spec.md).
- **Method:** 정상·경계·실패·replay의 observable contract와 oracle, mock이 대체하는 경계를 파일 전체에서 확인했다. 이 문서는 implementation 담당자의 설계 audit이며 독립 review gate는 상위 작업에서 별도로 수행한다.

## File Inventory And Coverage

| File | Review | Contract And Independent Oracle | Boundary And Disposition |
| --- | --- | --- | --- |
| [test_evaluation_report.py](../../../tests/reliability/test_evaluation_report.py) | 전체 14개 function, fixture·callback 포함 | 공개 export, normal/incident·다중 항목·빈 목록 집계, `2/3` 고정 성공률, literal Markdown row·실제 파일 write, deterministic volume fixture→defect→approval→recovery→replay, selected source scope, stale/incomplete/invalid gate, dbt·promotion failure의 mutation/artifact evidence | 단순 renderer 자기 비교 외에 literal row oracle이 있다. Volume 성공 경로의 dbt subprocess는 stub이지만 실제 DuckDB 상태를 검사하고 실제 artifact 생성·promotion을 연결한다. E2 및 빈 집계 test만 추가했다. |
| [test_null_spike_evaluation.py](../../../tests/reliability/test_null_spike_evaluation.py) | 전체 22개 function, fixture·helper 포함 | 실제 row count 보존·단일 null incident, exact candidate/proposal/approval binding, clean content/null rate 복원, existing/alias/dangling path의 무부작용, zero/multiple/unrelated incident 집합 거부, 20행 중 residual null `0.05` 거부, exact `0.0` baseline/recovery/replay evidence, content/null acceptance 실패와 callback 차단, replay/profile/lifecycle/artifact lock/ValueError/dbt/promotion 실패 분류 | 성공 경로는 실제 CSV·DuckDB·profile·detector·recovery를 사용한다. Ambiguity는 lifecycle 결과를 통제하여 evaluator의 cardinality gate만 검증한다. Quality failure 일부는 executor 반환값을 바꾸므로 실제 손상 상태를 만드는 executor test의 대체 증거가 아니다. 변경 없이 유지했다. |
| [test_schema_drift_evaluation.py](../../../tests/reliability/test_schema_drift_evaluation.py) | 전체 10개 function, fixture·helper 포함 | actual `loan_amount: VARCHAR` 물리 schema, 2024 sentinel을 포함하는 complete population, restoration 뒤 실제 최종 table state와 baseline 일치, replay `already_restored`, incomplete candidate 승인 전 거부, schema/content stale, unlock 뒤 committed state, rollback/diverged replay/dbt 실패, E1 Action FAIL·`2/3` 집계·literal Markdown | dbt callback은 합성 성공 evidence다. Replacement rollback test는 structured executor exception을 주입해 evaluator mapping을 검사한다. 실제 transaction rollback/state 보존은 recovery executor test 소유다. #265 회귀를 그대로 보존했다. |
| [test_freshness_delay_evaluation.py](../../../tests/reliability/test_freshness_delay_evaluation.py) | 전체 13개 function, fixture 포함 | fixed `09:00` clean/`07:00` delayed timestamp, content identity 보존, 단일 freshness incident, bound approval, `partition_changed`→`already_recovered`, 기존/alias path·delay 하한, inexact timestamp·validation 중 candidate 변경, temporal target drift, 정확히 60분 뒤 만료 replay, failed freshness validation·unresolved incident 시 target callback 차단, lifecycle/target failure 뒤 observation 보존 | 실제 compound recovery를 사용하며 downstream callback은 합성 ID다. Expired replay test의 직접 oracle은 failure 분류·재승인 필요성이다. Timestamp/age/threshold 세부 error context 전체와 모든 no-write side effect를 이 test가 독립적으로 입증하지는 않는다. 변경 없이 유지했다. |
| [test_freshness_delay_evaluation.design.md](../../../tests/reliability/test_freshness_delay_evaluation.design.md) | 전체 contract·11개 scenario row·exclusions | 각 row가 현행 function에 연결되며 timestamp, candidate 재측정, temporal drift, expired replay, failed validation, unresolved incident, downstream observation preservation을 반영한다 | source publication/download/scheduling·production DB mutation 제외와 partition-loader/executor race ownership이 적절하다. 새 변경은 report 집계에만 있으므로 freshness design 수정은 필요 없다. |

[공통 conftest](../../../tests/reliability/conftest.py) 전체도 읽었다. 이 4개 module은 각 module의 local fixture로 disposable DB와 artifact를 만들며 해당 공통 synthetic fixture를 사용하지 않는다. Shared fixture·config·source·Spec은 수정하지 않았다.

## Contract And Scenario Assessment

| Contract Group | Normal And Boundary | Failure And Recovery | Coverage Decision |
| --- | --- | --- | --- |
| Aggregation/report | Normal empty expectations, incident success, exact count/rate, report write | Partial detection만 실패·partial action만 실패하는 독립 case, 완전 충족 대조 case, 빈 목록의 zero count/rate | E2와 신규 E3을 최소 unit에서 보강했다. Production subset 수학을 test 안에 재구현하지 않는다. |
| Volume slice | 같은 fixture 반복의 stable identity, clean/defect/post 결과, selected source file | Invalid source·incomplete approval·stale/diverged target, replay profile 실패, target dbt failure, post-promotion actual projection | 기존 integration을 유지한다. Raw target `RuntimeError`의 전파는 현행 test의 의도적 계약이며 null-spike `ValueError` 규칙을 복제하지 않는다. |
| Null slice | 정확한 clean state와 null rate, 단일 incident, replay stable content/null state | Path preflight, unachieved defect, residual candidate, ambiguous incidents, content/null quality gate, lifecycle/replay/callback/dbt/promotion 실패 | 고정 SQL 관측과 exact baseline 값이 domain algorithm을 복제하지 않는다. Side-effect journal은 callback 차단과 실행 경계를 보완한다. |
| Schema slice | Numeric→VARCHAR 물리 변화, complete candidate·sentinel, exact restoration와 replay | Incomplete population, stale schema/content, committed unlock failure, rollback mapping, diverged replay, post-restoration dbt failure | Schema equality만으로 통과하는 false green과 E1 Action false green을 기존 oracle이 차단한다. |
| Freshness slice | Content 유지·timestamp만 지연, exact bound candidate, compound acceptance와 replay | Path/input preflight, wrong timestamp/candidate mutation, unavailable measurement, temporal drift/expired replay, failed acceptance, unresolved incident, downstream 실패 | 관측 보존과 mutation 분류는 검사한다. Race와 exact no-overwrite 실행은 owning loader/executor test 및 최종 통합 검토에서 대조한다. |
| Read-only lifecycle separation | Evaluation API는 명시적으로 호출된다 | Lifecycle에서 approval/recovery/report write가 자동 발생하지 않는 계약 | Lifecycle owner의 test가 직접 소유한다. 이 evaluator suite 실행만으로 해당 독립 side-effect 부재를 새로 입증했다고 해석하지 않는다. #277 접점 검토 대상이다. |

## Historical Finding Dispositions

[이전 evaluation review](../01-review-historical/reliability/evaluation.md)의 findings는 `3ab8991` code 및 `bdce0f4e` 전달 snapshot의 근거다. 아래 판정은 위 현재 revision에서 다시 확인한 결과다.

| ID | Disposition | Current Evidence | Action |
| --- | --- | --- | --- |
| E1 | obsolete | #265 commit `e0eb99bfbf92147b8691c491226191b879f7afb6`이 [schema failure adapter](../../../src/hmda_reliability/reliability/evaluation/schema_drift.py)에 미충족 `complete_recovery`를 추가했다. 기존 schema failure 6개 test가 Action FAIL을 검사하고 target dbt 실패는 count/rate·literal Markdown FAIL까지 연결한다. 성공 case도 3/3을 보존한다. | 이미 해결된 production 결함으로 처리하고 기존 회귀를 유지한다. |
| E2 | accepted | [case result](../../../src/hmda_reliability/reliability/evaluation/case_result.py)의 `issubset`은 옳지만 기존 직접 집계 test는 singleton만 사용했다. 두 항목 중 하나만 맞아도 성공하는 오구현이 기존 성공률 test를 통과했다. | `test_evaluation_report_requires_all_expected_incidents_and_actions` 추가. Partial detection·partial action·complete의 3개 고정 case에서 property·2/3 집계·literal FAIL/PASS row를 검사한다. |
| D1 cross-reference | deferred | 두 dbt artifact를 함께 바꾸는 volume/null promotion test는 results-only projection 민감도까지 입증하지 않는다. Operations D1의 현행 해결 여부는 이 lane에서 재현하지 않았다. | 현재 결함으로 단정하지 않고 #277에서 owning artifact/projection 회귀와 연결한다. |
| R1 cross-reference | deferred | 현행 backfill/schema Spec은 commit/replay 뒤 staging cleanup failure의 구조화된 mutation evidence를 명시한다. Schema evaluator의 실제 unlock failure test도 committed after-state와 resume action을 확인한다. | R1 자체의 현재 root-cause 판정은 recovery lane에 결합한다. 이 evaluator batch가 volume/null/freshness 전체 cleanup propagation을 모두 실행했다고 주장하지 않는다. |
| Raw RuntimeError normalization candidate | rejected | Volume test는 post-promotion raw `RuntimeError` 전파와 실제 projection 변경을 명시적으로 기대한다. Null callback `ValueError` 정책을 모든 evaluator에 적용할 정본 근거가 없다. | Production exception contract 확장은 하지 않는다. |

## Added Gap And Validation

**E3 — Empty aggregate boundary, accepted:** 정본의 `Empty case list`는 detection/action rate `0.0`을 요구하지만 기존 report module에는 해당 scenario가 없었다. `test_evaluation_report_handles_empty_case_list`는 total/pass count `0`과 두 rate `0.0`만 검사한다. Renderer formatting 확장이나 입력 모델 재설계는 포함하지 않는다.

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | New focused tests | `uv run --no-sync pytest -q`에 새 node ID 2개를 명시, **2 passed in 0.37s** |
| ✅ Pass | Evaluation modules | 아래 command, **77 passed in 22.93s** |
| ✅ Pass | Ruff lint / format | `uv run --no-sync ruff check tests/reliability/test_evaluation_report.py`, `uv run --no-sync ruff format --check tests/reliability/test_evaluation_report.py` |
| ✅ Pass | Whitespace | `git diff --check` |
| ✅ Pass | Markdown | `uv run --no-sync rumdl check inbox/github-272-audit-reliability-design/02-review-current/evaluation.md` |
| ✅ Pass | Detection-any negative control | 원래 singleton success-rate test는 PASS, 새 E2 test는 `missing_incident.detection_passed`가 True라서 assertion FAIL. **1 passed, 1 failed**, pytest exit `1` |
| ✅ Pass | Action-any negative control | 원래 singleton test는 PASS, 새 E2 test는 `missing_action.action_passed`가 True라서 assertion FAIL. **1 passed, 1 failed**, pytest exit `1` |
| ✅ Pass | Empty-rate-one negative control | 원래 singleton test는 PASS, 새 empty test는 detection rate `1.0 != 0.0`에서 assertion FAIL. **1 passed, 1 failed**, pytest exit `1` |

```bash
uv run --no-sync pytest -q \
  tests/reliability/test_evaluation_report.py \
  tests/reliability/test_null_spike_evaluation.py \
  tests/reliability/test_schema_drift_evaluation.py \
  tests/reliability/test_freshness_delay_evaluation.py
```

Negative control은 별도 Python subprocess에서 class property 또는 reporter의 rate 함수를 메모리상 치환하고 `pytest.main`으로 기존 test와 새 test를 함께 실행했다. Detection/action control은 빈 기대 목록의 기존 의미를 보존한 채 nonempty 목록만 `any` intersection으로 바꿨다. Empty control은 total `0`일 때만 `1.0`을 반환하도록 바꿨다. Source file은 쓰지 않았고 각 subprocess가 종료되면 주입이 사라진다. Collection/import 실패가 아닌 observable assertion 실패다. Import 후 pytest를 호출해 발생한 rewrite warning과 Tach impact-analysis 안내는 검출 실패의 원인이 아니다. `--tach` skip은 사용하지 않았다.

**Validated changed-file SHA-256:** [test_evaluation_report.py](../../../tests/reliability/test_evaluation_report.py) = `541da6d0481e548d34dc2ad520e25354eef039cb765d77566413693b163d03af`.

## Limits And Handoff

- 실제 승인자는 fixture의 문자열이며 사람 승인 완료를 입증하지 않는다. Live provider/AI utility 평가는 이 deterministic evaluation의 계약 밖이다.
- Focused GREEN은 local working diff의 증거다. 원격 PR head·prospective merge CI·독립 review·인간의 Ready/approval/merge 판정은 이 결과에서 파생하지 않는다.
- #277에서는 operations/lifecycle→evaluation의 read-only 분리, results-only artifact projection 민감도, recovery cleanup failure의 각 evaluator 전달 경로를 owning regression과 대조한다. 이번 lane에서는 새 source defect나 공유 설정 변경 필요를 확정하지 않았다.
- Schema evaluation Spec의 `Existing or aliased evaluation database` scenario에는 현행 `THEN` 문장이 빠져 있다. 기존 테스트는 disposable preflight의 무부작용 거부를 검사하고 다른 evaluator와 같은 안전 경계를 사용한다. 이 정본 형식/문구 보완은 #277로 전달하며 현재 GREEN을 새로운 Spec 요구의 승인으로 해석하지 않는다.
