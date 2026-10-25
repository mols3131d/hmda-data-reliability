---
type: review
title: Data Operations Test Audit and Adoption
description: 현행 도메인 6파일의 테스트 설계 검토, historical finding 수용과 회귀 보호 및 PR 277 인계 근거를 기록합니다.
---

# Data Operations Test Audit and Adoption

> [!NOTE]
> 도메인 tracked 6파일을 전수 검토하고 exclusive test 2파일을 보강했습니다. 독립 검토는 `clear`이며, 최신 main과 합친 CI의 도메인 57개 및 Git 환경을 격리한 로컬 hook의 1,084개가 통과했습니다. 아래 snapshot의 human review readiness는 `ready`입니다. 공유 tooling F3는 #277의 우선 후속 항목으로 남깁니다.

- **Target:** [PR #270](https://github.com/mols3131d/hmda-data-reliability/pull/270)의 Data Operations 테스트 설계 검토·수용.
- **Revision:** 최신 main `ea39a4fd6c8f483509cf00a1d1114feb4ef3b686`, 조사 merge `c0306551abe289fbe1838af114059059e7ba00b5`, 테스트 보강 `29bfc14f8fe4598cc9bc03b943219c809f6047e8`.
- **Scope:** tracked test/support/design 6파일 전체. 수정은 exclusive test 2파일과 이 PR 소유 Inbox에 한정합니다. Source/Spec/config와 #277 예약 파일은 수정하지 않았습니다.

## Findings

도메인 production defect를 확인한 항목은 없습니다. D1은 테스트 oracle gap으로 수용해 보강했습니다. 아래 항목은 예약된 cross-domain/공유 tooling 범위의 후속 작업이며 이번 PR의 수정 범위를 넓히지 않습니다. F3는 실제 전달 과정에서 재현된 공통 Git fixture 결함입니다.

| ID | Severity | Finding | Action |
| --- | --- | --- | --- |
| F1 | Minor | 예약 E2E의 logical content identity가 `ingested_at`만 바뀌는 mutation을 검출하지 못함 | `follow_up`: #277에서 ordered raw-row snapshot으로 안전성 oracle 보강 |
| F2 | Note | 예약 E2E의 DB·artifact는 격리되지만 dbt 기본 log 경로는 공유 가능 | `follow_up`: #277에서 test별 `DBT_LOG_PATH` 격리 검토 |
| F3 | Major | Pre-push의 Git 환경이 임시 fixture에 전파되어 실제 local ref/index/config를 변경함 | `scope_decision`: 공유 fixture/hook 수정은 #277 소유. 이번 전달은 환경을 격리한 동일 hook으로 검증 |

## Inventory And Coverage

`git ls-files tests/data_operations`의 6개를 모두 읽었습니다. main과 조사 기준의 inventory는 같고, 별도 domain conftest·fixture 파일은 없습니다. Test 내부 helper도 검토에 포함했습니다. 두 exclusive Python 파일에 대응하는 기존 design 문서는 없습니다.

| File | Review And Oracle | Disposition |
| --- | --- | --- |
| [test_dbt_runner.py](../../tests/data_operations/test_dbt_runner.py) | 전체 31 test functions / 34 cases와 helper 2개. 실패 context, 실제 artifact bytes, lock·rollback·commit 후 pair 상태를 비교 | 수정·검증 완료. subprocess는 fake boundary |
| [test_incident_lifecycle.py](../../tests/data_operations/test_incident_lifecycle.py) | 전체 8 functions / 9 cases와 helper 3개. 실제 DuckDB→profile→detector→impact→draft, literal count/ID/evidence/action, row·artifact 보존 | 수정·검증 완료. dbt artifact는 fixture |
| [test_quality_gate.py](../../tests/data_operations/test_quality_gate.py) | 전체 8 functions / 9 cases. 실제 DB·profile·policy로 허용/차단·reason·오염 partition 확인 | #277 예약. 읽기 전용 검토·실행 완료 |
| [test_system_recovery_e2e.py](../../tests/data_operations/test_system_recovery_e2e.py) | 전체 5 cases. 실제 dbt 2경로와 승인 거부·stale state·missing action 3경로 | #277 예약. 읽기 전용 검토·실행 완료, F1/F2 인계 |
| [test_system_recovery_e2e.design.md](../../tests/data_operations/test_system_recovery_e2e.design.md) | S0–S7, evaluator와 안전성 3종의 함수 연결을 대조. Airflow/live AI/실제 사람 승인/다중 partition 제외와 일치 | #277 예약. 읽기 전용 검토 완료 |
| [__init__.py](../../tests/data_operations/__init__.py) | package docstring만 존재하며 실행·등록·shared state 없음 | support 검토 완료. 변경 필요 없음 |

### dbt Execution And Promotion

계약은 [stage execution Spec](../../openspec/specs/data-operations-stage-execution/spec.md), [Data Operations guide](../../docs/domains/data-operations.md), [Architecture](../../docs/ARCHITECTURE.md)와 public source에 대조했습니다.

| Contract | Scenario And Independent Oracle | Cases |
| --- | --- | ---: |
| Independent request | environment override/default, invalid year, empty DB/source path의 정확한 값·validation error | 5 |
| dbt failure | missing/stale artifact, timeout, process 시작 실패, nonzero stderr, target 준비·artifact read 실패의 domain error/context | 7 |
| Build/configuration | run-scoped result, alternate CWD의 canonical bundle, configurable project/profile, exact argv | 4 |
| Serialized mutation and gate | subprocess 중 lock, lock 실패 시 process 미시작, gate 차단, 같은 lock의 gate→process 순서, noncanonical project/profile 거부 | 6 |
| Candidate/current separation | candidate build 후 old current 보존, A/B build 뒤 A를 승격하면 정확한 A pair | 2 |
| Projection integrity | manifest/results 각각의 drift, pair boundary collision, lock 대기 중 drift 거부 | 4 |
| Promotion failure/recovery | read·lock 실패, unlock/cleanup 실패 후 committed pair, 두 번째 replace 실패 시 old pair 복구 | 5 |
| Concurrent promotion | 실제 projection lock·I/O에서 최종 pair가 A/A 또는 B/B이며 혼합되지 않음 | 1 |

Fake gate는 호출 순서·동일 lock의 조합 경계를 검증합니다. 실제 policy 연결은 예약 quality gate/E2E가 보완하며 실제 HMDA/recovery writer와의 교차 직렬화 검증은 #277 범위입니다. Candidate writer와 copy 사이 변경에 대한 source의 기존 제약을 이번 테스트로 해결했다고 주장하지 않습니다.

### Lifecycle And Reserved Integration

[lifecycle Spec](../../openspec/specs/data-operations-incident-lifecycle/spec.md)의 실제 profile, incompatible baseline, 모든 detection 분석, no-detection, read-only, result/recovery inputs, threshold 요구사항을 각 기존 scenario에 연결했습니다.

- 다른 연도 row를 추가해 metadata `5`, target current `4`, baseline `8`을 비교합니다. Table 전체를 current로 사용하는 잘못된 조합은 count oracle과 다릅니다. Target table/year/count와 incident ID·evidence·assets·actions의 정확한 값도 확인합니다.
- No-detection은 빈 결과와 recovery 입력 부재를 확인하고 impact가 호출되면 실패하는 sentinel을 유지합니다. Baseline asset/partition 불일치는 각각 domain error와 비교 context를 확인합니다. Explicit freshness와 default 판정은 같은 실제 profile에서 구별합니다.
- Read-only scenario는 `SELECT * ... ORDER BY ALL`로 `ingested_at`을 포함한 모든 row 값, dbt artifact exact bytes, 신규 파일 부재와 scratch 부재를 확인합니다. 읽기 과정의 projection lock file만 허용합니다. Synthetic 2026 scenario는 별도 main DB의 2025/2026 count도 보존합니다.
- 예약 quality gate는 전체 Bronze, 요청 외 dirty partition, canonical source/partition 제한, 없는 요청 partition과 NULL discriminator를 검증합니다. 정확 baseline·delta 경계는 [Reliability quality gate tests](../../tests/reliability/test_quality_gate.py)가 별도로 보호하므로 이곳에 중복 구현하지 않았습니다. Airflow source 문자열 검사는 module의 lexical dependency만 입증합니다.
- 예약 E2E는 10행, null rate `50%→0%`, staging 10행·mart 2행, dirty/clean/recovered content identity와 replay timestamp 보존을 사용합니다. 실제 approval은 fixture이며 직접 API 통합 성공은 Airflow DAG runtime 또는 사람 승인 근거가 아닙니다.

## Historical Adoption

[이관본](01-review-historical/data-operations/README.md)은 historical evidence로 보존합니다. `3ab899100fc0b35e23d464bd761f3b144a978ae7`부터 최신 main까지 도메인 6파일, Data Operations source, artifact primitive와 두 Data Operations Spec은 diff가 없습니다. #263–#268 병합도 확인했으며 아래 항목을 자동으로 기해결 처리하지 않고 현재 파일을 직접 대조했습니다.

| Historical Item | Decision | Current Evidence And Action |
| --- | --- | --- |
| D1: results-only projection drift | `accepted` — oracle gap 해결 | drift test를 두 artifact로 parameterize. 거부와 기존 JSON pair의 exact bytes, `.next`/`.previous` 부재 확인. 현재 production identity는 원래 두 파일을 모두 포함 |
| Timeout fake가 실제 timeout 전달을 입증하지 못함 | `accepted` — 보강 | subprocess keyword `timeout == 300`과 domain error의 `timeout_seconds == 300` 확인. 실제 process 종료 시간 측정은 제외 |
| Fake-process request가 repository 기본 DB lock을 사용 | `accepted` — 격리 | 공통 local helper의 DB를 `tmp_path / warehouse.duckdb`로 지정 |
| Lifecycle 단독 row-count/scratch oracle 한계 | `accepted` — 보강 | 전체 row·artifact bytes·신규 파일 검사로 같은 count의 데이터 변경도 검출. 예약 E2E의 timestamp 범위는 F1로 구분 |
| 실제 사람 승인·운영 배포·Airflow 증거 없음 | `deferred` — 명시적 제외 유지 | fixture 승인/직접 API 결과를 사람·DAG 검증으로 승격하지 않음. 교차 도메인 실행은 #277 소유 |

### D1 Detection Evidence

정상 구현에서 두 artifact drift case가 통과했습니다. 별도 process-local pytest plugin이 `runner.artifact_projection_id`를 manifest-only SHA256로 대체하고 같은 두 case만 실행했습니다. Production 파일은 변경하지 않았습니다.

결과는 **1 passed / 1 failed, expected exit 1**입니다. Manifest drift case는 그대로 통과하지만 `run_results_path` case가 `DID NOT RAISE DataOperationError`로 실패했습니다. 따라서 기존 scenario를 통과하는 이 특정 잘못된 구현을 새 scenario가 구별합니다. 모든 가능한 identity 회귀의 검출력으로 일반화하지 않습니다.

재현 시 pytest의 `pytest_runtest_setup`에서 runner의 `artifact_projection_id(manifest_path, run_results_path)`를 manifest 경로의 `read_bytes()`만 SHA256으로 계산하고 `sha256:` prefix를 붙여 반환하는 함수로 대체합니다. `test_promotion_rejects_artifacts_changed_after_verification`만 선택하며, runner import 경로가 worktree 내부인지도 확인했습니다. 임시 probe는 repository 산출물로 보존하지 않습니다.

## Follow-up For PR 277

### F1 — Minor: Timestamp Mutation Oracle

#### F1 Locations

- [Reserved system recovery E2E](../../tests/data_operations/test_system_recovery_e2e.py)
  - `_assert_pre_approval_zero_mutation`과 첫 E2E의 lifecycle 전후 identity 비교.
- [Content identity](../../src/hmda_reliability/hmda_data/ingestion/identity.py)
  - `ingested_at`은 logical-content digest에서 제외됩니다.

#### F1 Evidence

예약 helper는 content identity/null rate를 비교하므로 timestamp만 바꾸고 예상 error를 반환하는 잘못된 구현을 구별하지 못합니다. Replay scenario는 별도 timestamp 비교가 있어 이 한계와 구분됩니다. 현재 source는 승인 우선 검사와 read-only connection을 사용하며 production defect를 재현한 항목은 아닙니다.

#### F1 Action

[PR #277](https://github.com/mols3131d/hmda-data-reliability/pull/277)에서 승인 실패 3종과 lifecycle 실행 전후에 `ingested_at`을 포함한 ordered raw-row snapshot을 비교합니다. 이번 PR의 단독 lifecycle 보강과 예약 E2E 보강은 수정 소유권이 다릅니다.

### F2 — Note: dbt Log Isolation

예약 E2E request는 DB/run/current 경로를 격리하지만 canonical dbt project/profile과 inherited logging 환경을 사용합니다. [runner](../../src/hmda_reliability/data_operations/runner.py)는 `--target-path`를 지정하며 기본 log 경로의 test별 격리를 제공하지 않습니다. Shared default log를 쓰는 concurrent 실행은 log 충돌 가능성이 있으므로 #277에서 test별 `DBT_LOG_PATH`를 검토합니다. 이번 E2E는 직렬 실행했으며 실제 충돌을 재현했다고 주장하지 않습니다.

### F3 — Major: Hook Git Environment Escapes Temporary Repositories

#### F3 Locations

- [CI test Git helper](../../tests/scripts/ci/helpers.py)
  - `git`는 `cwd=repo`만 지정하고 inherited Git 환경을 제거하지 않습니다.
- [CI test fixtures](../../tests/scripts/ci/conftest.py)
  - `repo`는 helper를 통해 init/config/commit하며 `tool_env`는 `os.environ`을 복사합니다.
- [Existing pre-push](../../lefthook.yml)
  - `pytest-affected`가 hook 환경에서 임시 Git fixture를 실행합니다.

#### F3 Evidence

2026-10-26 첫 push의 cold-cache hook은 1,086개를 수집해 **10 failed / 1,074 passed / 2 skipped / 306.64s**였습니다. CI fixture의 Git 명령이 hook의 `GIT_DIR`를 물려받아 실제 작업 branch에 `base`/`test change` commit을 추가하고 index를 fixture tree로 바꿨습니다. Common local identity도 fixture 값으로 바뀌었으며 Git 환경을 주입한 최소 throwaway 재현에서 같은 ref/index/config 변경을 확인했습니다. Push는 실패했고 원격 head `762870ac`는 보존됐습니다. 이후 ref 오염에 따른 파일 선택에서 TOML 도구 미설치 실패도 발생했으며 해당 실패를 도메인 테스트 결함으로 해석하지 않습니다.

이는 [PR #258의 기존 전달 예외](../github-258-cover-sdk-retry-classification/05-report-review-readiness.md#local-delivery-exception)에서도 기록한 미해결 공유 tooling 문제입니다. 이번 domain test 변경이 도입한 회귀가 아닙니다.

#### F3 Action

[PR #277](https://github.com/mols3131d/hmda-data-reliability/pull/277)에서 임시 Git repository를 만드는 모든 subprocess와 script environment의 local Git 변수 전파를 차단하고, 상위 저장소 ref/index/config 불변을 독립 oracle로 검증해야 합니다. 이 PR은 공유 fixture/hook을 수정하지 않습니다.

복구는 fixture commit을 `agent/test/audit-data-operations-hook-failure` ref와 기존 worktree에 보존하고, 검토된 `29bfc14f`에서 새 worktree를 생성한 뒤 PR 소유 branch 이름과 upstream을 연결하는 방식으로 수행했습니다. Reset, force-push 또는 공개 history rewrite는 수행하지 않았습니다. 현재 active worktree는 `hmda-data-reliability.worktrees/pr270-data-operations-delivery`입니다. 기존 worktree와 fixture ref는 실행 근거로만 남기며 작업을 재개하지 않습니다.

이후 push에는 외부 임시 wrapper를 command-local `core.hooksPath`로 지정했습니다. Wrapper는 `git rev-parse --local-env-vars`가 열거한 변수만 unset한 뒤 기존 pre-push를 그대로 exec합니다. Hook의 argv/stdin과 실제 검증 단계는 유지하고 shared hook/config 파일은 변경하지 않았습니다. 동일 방식의 throwaway push는 source HEAD/identity 불변과 exact head 전달을 확인했습니다.

실제 재실행은 **1,084 passed / 2 skipped / 309.56s**였고 3 Python 파일의 Ruff 검사도 통과해 `29bfc14f`를 non-force push했습니다. 실행 중 확보한 HEAD `29bfc14f`, index tree `8cca837393fc038e3f26bafba0754b33b674ea5c`, common config SHA256 `c2feb9ec9d806db52008d2ab26b52b3eab28ab65f322a2c9f04bd88005bd7d54`가 종료 후에도 일치했습니다. 여기서 config hash는 관찰 구간의 보존 근거이며 사고 전 identity 복원을 뜻하지 않습니다. Common identity는 기존 전역 user 설정을 commit별로 명시하는 방식으로만 처리하며 공유 config를 추정해 덮어쓰지 않습니다.

## Validation

모든 실행 cwd는 이 PR 전용 worktree입니다. 기존 `.venv`를 `UV_PROJECT_ENVIRONMENT`로 지정하고 `uv run --no-sync`를 사용했으며 dbt runner worker는 같은 interpreter의 `python -m pytest`를 사용했습니다. Pytest의 repository 설정 `pythonpath = ["src"]`가 해당 worktree source를 선택합니다. 공유 environment는 동기화·수정하지 않았고 DB/artifact/cache는 worktree 또는 `tmp_path`에 둡니다.

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | dbt runner module | 변경 전 32 passed / 1.50s, 변경 후 `pytest tests/data_operations/test_dbt_runner.py -q`: 34 passed / 1.34s |
| ✅ Pass | lifecycle module | `pytest tests/data_operations/test_incident_lifecycle.py -q`: 9 passed / 1.98s |
| ✅ Pass | reserved modules | `pytest tests/data_operations/test_quality_gate.py tests/data_operations/test_system_recovery_e2e.py -q`: 14 passed / 55.72s, real dbt 포함 |
| ✅ Pass | related artifact primitive | `pytest tests/data_platform/test_artifacts.py -q`: 3 passed / 0.35s |
| ✅ Pass | specific negative control | manifest-only identity에서 1 passed / 1 expected failure / 2.20s |
| ✅ Pass | changed Python static checks | 두 파일 Ruff check/format, `ty check --python <existing .venv> <two changed tests>` 통과 |
| ✅ Pass | independent review | 별도 `review-lead`가 quality/adversarial specialist의 격리된 검토를 조정. `c0306551..29bfc14f`의 두 test 변경은 `clear`, material finding 없음 |
| ✅ Pass | Inbox mechanics | 4 Markdown 파일 rumdl, native Inbox validator, YAML frontmatter required scalar 검사와 `git diff --check` 통과 |
| ❌ Fail | initial inherited-environment hook | 10 failed / 1,074 passed / 2 skipped. F3 Git fixture 누수와 local metadata 오염. 해당 실패 및 이후 TOML 선택 실패로 push 차단 |
| ✅ Pass | isolated-environment same hook | 기존 pre-push/Lefthook을 그대로 실행해 1,084 passed / 2 skipped / 309.56s, Python 3파일 정적 검사 통과. Ref/index와 관찰 구간 common config hash 보존 |
| ✅ Pass | refreshed remote CI | [CI Lite 40206109379](https://github.com/mols3131d/hmda-data-reliability/actions/runs/40206109379/job/121207271446): prospective merge `40847f65c6d98c3fe2134de9e56659304491f380`에서 `tests/data_operations`, 57 passed / 41.19s; changed Python Ruff/format·도메인 type check 통과 |

도메인 57개는 34+9+14를 합한 disjoint module 결과이며 하나의 단일 실행 결과로 표현하지 않습니다. Reserved tests는 조사 merge에서 실행했으며 이후 production·예약 test·환경 입력이 바뀌지 않았습니다. 초기 ty 실행은 system environment 때문에 pytest import를 찾지 못했고, 동일 `.venv`를 명시한 뒤 통과했습니다. 넓은 hook의 최초 실패와 격리 후 성공은 별도 기록하며 도메인 수치와 합산하지 않습니다. Hook의 Airflow/dbt runtime fixture 성공은 실제 운영 배포나 사람 승인 증거가 아닙니다. Live AI와 사람 평가는 실행하지 않았습니다.

독립 검토의 reviewed blob은 dbt runner `a3c5e0fc922a5d099b73e17e3e42c0cc071fd101`, lifecycle `ba27637733f83916b171e65a6c43010a4f07a5c9`입니다. Reviewer는 diff·Spec·연결된 source·blob을 대조했으며 보고받은 실행 결과를 반복하지 않았습니다. 예약 4파일과 실제 dbt SQL, #277 완료 여부는 이 bounded 독립 검토의 범위 밖이며 위 inventory 검토와 실행 범위로 따로 기록했습니다.

CI checkout log와 merge object의 부모는 base `ea39a4fd6c8f483509cf00a1d1114feb4ef3b686` / head `29bfc14f8fe4598cc9bc03b943219c809f6047e8`에 일치합니다. Source boundary/build/OpenSpec 등 생략된 CI step을 검증 성공으로 세지 않습니다. 이 문서와 계획의 후속 전달 commit은 Inbox만 변경하며 reviewed test blob을 유지합니다. 그 최종 head의 required check와 최신 base/head는 PR 본문·check에서 다시 확인합니다.

## Review Readiness

2026-10-26 source-CI snapshot은 open/Draft/mergeable, approvals 0, review threads/comments 0입니다. 동일한 변경 목적, 전수 inventory/disposition, 필요한 oracle 보강, 독립 검토와 현재 base/head의 CI를 확인했습니다. F1/F2는 예약 통합 테스트의 후속 보강, F3는 공유 fixture 결함과 검증된 전달 격리 방식으로 분리했습니다. 도메인 변경의 필수 수정이나 미완료 exclusive scope는 남지 않았습니다.

따라서 위 exact pair의 **review readiness는 `ready`**입니다. 이는 correctness approval이나 merge permission이 아닙니다. Base/head, reviewed test blob, description 또는 applicable feedback이 바뀌면 필요한 근거를 다시 확인합니다. 원래 준비 head `762870ac`의 CI를 현재 성공 근거로 사용하지 않습니다.

## Continuation

- 다음 사람의 행동은 이 PR의 test diff와 현재 검증 근거를 검토하고 Ready 전환 여부를 결정하는 것입니다. 추가 in-scope test 수정은 필요하지 않으며 원격 mutable state가 달라지면 재확인합니다.
- #277 담당자는 F1/F2의 예약 파일 oracle·격리와 F3의 공유 Git fixture 환경 격리를 자기 branch에서 검토합니다. F3는 실제 local metadata를 변경하므로 wrapper 없이 hook을 재실행하기 전에 우선 처리할 항목입니다. 이번 PR에서 타 PR branch 또는 공유·예약 파일을 수정하지 않습니다.
- Draft→Ready, approval, merge는 사람의 별도 결정입니다. 이 문서는 해당 lifecycle action을 승인하지 않습니다.
