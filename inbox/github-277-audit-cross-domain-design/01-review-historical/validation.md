---
type: report
title: Domain Test Design Validation Evidence
description: 고정 revision의 테스트 실행 결과와 테스트 설계 후보에 대한 최소 재현을 구분해 기록합니다.
tags:
  - testing
  - evidence
---

> [!WARNING]
> **Historical snapshot only:** PR #258 (`bdce0f4e`)의 과거 도메인 전체 리뷰/방법/목록/실행 기록입니다. 원래 revision 3ab89910의 결과이며 새 cross-domain 검증 또는 현재 main의 전수 검토 완료를 뜻하지 않습니다. 각 finding은 소유 PR에서 개별 재검증 후 선택 수용합니다.

# Domain Test Design Validation Evidence

검토 revision은 PR #258 브랜치의 `3ab899100fc0b35e23d464bd761f3b144a978ae7`다. 이 묶음은 PR #258이 소유하며 날짜 기반 경로에서 해당 PR Inbox로 이동했다. 실행 대상·결과는 유지했고 아래 실행은 caller가 수행했다. 독립 reviewer의 정적 검토를 reviewer 자체 실행으로 표시하지 않는다. Test 수는 실행 결과이며 설계 품질 점수가 아니다.

후속 문서 전달 commit은 위 실행·검토 revision과 구분한다. 전달 시 source·test·Spec·설정·CI의 변경 없이 검토 대상 94개 Git blob의 동일성을 다시 확인한다. 최종 push와 해당 head의 CI 상태는 PR #258 본문에서 확인한다.

## Test Execution

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | 일반 suite | `pytest --ignore=tests/orchestration/test_airflow_dagrun.py -q -ra -n 2`: **949 passed, 2 skipped / 35.40s** |
| ✅ Pass | 실제 Airflow DAGRun 별도 직렬 실행 | `pytest tests/orchestration/test_airflow_dagrun.py -q -ra`: **5 passed / 106.76s** |
| ⚪ Not Verified | zizmor 실제 audit cache 경로 | [test_ci_steps.py](../../../tests/scripts/ci/test_ci_steps.py)의 `zizmor@1.30.1` cache 필요 사례 1개 skip |
| ⚪ Not Verified | Windows npm/Node 경로 | [test_commands.py](../../../tests/scripts/test_commands.py)의 Windows 전용 사례 1개 skip |

두 명령은 겹치지 않아 합계 **954 passed, 2 skipped**다. 저장소의 `.venv/bin/python -m pytest`로 실행했다. 일반 suite가 종료된 뒤 DAGRun을 별도로 실행해 Airflow 공유 상태 간섭을 피했다. Mocked provider 테스트 통과를 외부 LLM 서비스의 현재 가용성이나 실제 리뷰 품질 증거로 해석하지 않는다.

## Confirmed Counterexamples

다음은 기존 suite의 실패 결과가 아니다. 기존 테스트가 놓친 입력·장애 경로를 새 임시 데이터로 재현한 결과다. Source·test·Spec은 수정하지 않았고, probe의 입력과 DB는 임시 디렉터리와 새 메모리 DB에만 만들었다. 세부 계약·영향·후속 제안은 각 도메인 리뷰가 소유한다.

### A1 Mixed Source Schema

`good_2025.csv`에는 필수 7컬럼과 1행을, `bad_2025.csv`에는 `income`만 없는 나머지 6컬럼과 1행을 쓴다. 두 파일을 함께 public full loader와 partition loader에 각각 새 DB로 전달한다. 두 호출 모두 오류 없이 2행 적재를 반환하고, `bad_2025.csv`의 `income`은 `NULL`이다. 한 파일의 누락이 다른 파일의 schema에 가려진다.

| Loader | Observed Result | Expected Contract |
| --- | --- | --- |
| `load_hmda_loans` | success, 2 rows, bad income=`NULL` | 필수 컬럼이 없는 적재 대상 파일의 validation failure |
| `load_hmda_loans_partition(..., 2025)` | success, 2 rows, bad income=`NULL` | 동일 |

### A2 Synthetic Source Preservation

임시 `cases/row_count_drop/year_2025.csv`를 source로 만들고, `row_count_drop(connection, [source], cases, sample_fraction=1.0)`을 호출한다. 호출 전 source가 존재했으나 호출 후 `SyntheticCaseError`와 함께 source 파일이 삭제됐다. Source와 case output의 경로가 겹치는 입력이다. 기존 case 디렉터리 삭제가 원본까지 포함한다.

### A3 EDA Evidence Pair Cleanup

[write_evidence](../../../scripts/run_actual_source.py)의 기존 JSON·Markdown 쌍을 `row_count=100`으로 만든다. `row_count=200`으로 갱신하면서 해당 `.json.bak` 경로의 `Path.unlink`에만 `OSError`를 주입한다. 두 replace 후 backup 정리 단계가 실패하면 JSON은 100으로 복구되고 Markdown은 200으로 남는다. 반환된 오류는 `OSError`다. 최초 생성 때 두 번째 replace가 실패하는 기존 시나리오와 구분된다.

### B1 Committed Recovery Cleanup

[Backfill fixture helper](../../../tests/reliability/test_approval_backfill_validation.py)의 실제 CSV·proposal·approved request와 [schema executor helper](../../../tests/reliability/test_schema_recovery_executor.py)의 `target_state="before"` request를 각각 새 임시 경로에 만든다. 각 executor module의 `TemporaryDirectory`만 정상 body·정상 실제 cleanup 후 `OSError`를 던지는 context manager로 대체한다. Mutation 후 target을 실제 재조회한 결과는 다음과 같다.

| Executor | Actual State | Returned Failure Evidence |
| --- | --- | --- |
| Backfill | expected-after identity와 같음, 2행 | `BackfillValidationError`, `mutation_state=None`, `reconciliation_action=None`, `context={}` |
| Schema recovery | expected-after table state와 같음, 전체 3행 | raw `OSError`, mutation/reconciliation metadata 없음 |

Schema fixture의 전체 3행 중 observation partition 2025는 2행이다. Temporary staging cleanup은 lock release·connection close 실패와 다른 경계다. 기존 cleanup 회귀가 모든 resource exit를 검증한다고 확대하지 않는다.

### B2 Profile Scope Alignment

동일 helper의 정상 request를 dump하고 `profile_request.partition_column`만 `income`으로 바꾼 뒤 outer request의 `model_validate`로 새 request를 만든다. `model_copy`의 검증 우회에 의존하지 않는다. Partition 값 2025는 유지한다.

| Executor | Validation Result | Profile Result | Actual Target |
| --- | --- | --- | --- |
| Backfill | success, `validation_passed=True` | `profile_snapshot.row_count=0` | expected-after identity, 2행 |
| Schema recovery | success, `validation_passed=True` | `profile_snapshot.row_count=0` | expected-after table state, 전체 3행·2025 partition 2행 |

이 probe는 승인 없이 mutation이 가능하다는 증거가 아니다. 유효한 승인이 있는 recovery에서 관찰해야 할 partition과 다른 predicate의 profile이 성공 증거로 붙는 현상을 확인한다.

### B3 Malformed Lineage Object

[Impact fixture](../../../tests/reliability/test_impact_analysis.py)의 정상 source incident에 manifest `{"nodes":"bad","sources":[]}`와 존재하는 run-results `{}`를 전달한다. JSON 자체는 parse 가능하지만 graph object shape가 잘못됐다. Public analyzer가 오류 대신 success와 `downstream_assets=[]`, `affected_assets=[]`를 반환했다. 기존 invalid JSON·missing run-results 사례와 구분된다.

### C1 Failed Recovery Action Metric

[Schema evaluation helper](../../../tests/reliability/test_schema_drift_evaluation.py)의 정상 source·request·approved callback을 사용한다. Candidate validation은 기존 `DbtBuildResult` fixture를 반환하고, target validation만 `DataOperationError`를 던진다. 실제 evaluator의 결과 세 개를 `build_evaluation_report`에 전달하고 Markdown을 렌더링했다.

| Field | Observed Value |
| --- | --- |
| case name | `recovery_dbt_failure` |
| failure stage / mutation | `after_target_mutation` / `True` |
| required / remediation actions | `[]` / `[]` |
| failed case action passed | `True` |
| aggregate action success rate | `1.0` |
| rendered failed-case action | `PASS` |

Markdown에는 failure stage와 reconciliation도 남아 있다. 오류 정보가 모두 사라진다는 주장이 아니라, 실패한 recovery의 action 성공 집계가 잘못되는 현상을 확인한 것이다. Dbt target 실패는 callback으로 주입했으며 외부 dbt 장애를 일으키지 않았다.

### D1 Per-Evidence Preflight Limit

[Review service fixture](../../../tests/review_ai/test_service.py)와 정상 null-spike material에 table-metadata evidence를 추가한다. 허용된 `table_name`, `columns`, `column_types`, `partition_column`, `schema_hash` 다섯 payload key에 각각 `한` 333개, UTF-8 **999 bytes**의 값을 둔다. Incident·draft refs를 두 evidence ID에 맞추고 `Evidence`, incident/draft, `AgenticReviewInput`의 정상 validation을 먼저 통과시킨다.

Public `review_null_spike`는 `input_rejected` 결과 대신 `BoundedReviewEvidence`의 raw `ValidationError`를 노출했다. 메시지는 `bounded evidence facts exceed the per-evidence limit`이며 provider 호출 **0회**, store record **0개**다. 각 값의 제한은 만족하지만 합쳐진 evidence facts가 4,096-byte 경계에 걸리는 사례다.

Refs를 갱신하지 않은 최초 입력은 upstream에서 `invalid_review_input`으로 정상 거부됐다. 최종 반례는 이 safeguard를 우회하지 않고 참조를 정렬한 유효 입력이다. 전송·저장 부작용은 없으며 typed preflight 결과의 계약을 놓치는 문제다.

### D2 Service Handoff Negative Controls

원본 source 대신 임시 source·test 복사본에서 service 한 곳씩 바꿨다. Autouse import guard가 매 test에서 `service.__file__`이 격리 복사본임을 확인했다. 매 mutant는 정상 원본에서 다시 시작했고 bytecode 재사용을 끈 새 pytest process에서 실행했다.

기존 대상은 [service](../../../tests/review_ai/test_service.py)·[context](../../../tests/review_ai/test_context.py)·[prompt/provider](../../../tests/review_ai/test_prompt_provider.py)·[validator](../../../tests/review_ai/test_validator.py) 4개 module이다. 별도 witness 두 개는 실제 provider 메시지를 capture하는 검사와, 정상 references의 evidence 9개 중 prompt에서 제외된 ID를 응답이 인용할 때 거부하는 검사다.

| Isolated State | Existing Tests | Two Witnesses |
| --- | --- | --- |
| baseline | 58 passed | 2 passed |
| `invoke(rendered.messages[:1])`로 user message 누락 | 58 passed | 1 failed, 1 passed: 실제 전달 tuple에 user message 없음 |
| validator의 selected evidence allowlist keyword 제거 | 58 passed | 1 failed, 1 passed: 제외된 ID의 응답이 `accepted` |

두 변경은 **현재 production의 결함이 아니라 잘못된 구현을 기존 테스트가 통과시키는 반례**다. Baseline witness는 모두 통과했다. 원본 service SHA-256은 실행 후에도 `315948a11d90f1b8c3ed03c8a4a99dc018a65cc99aaf7e3a9bf8cc20bedcf62f`로 보존됐다. 격리 경로의 Git metadata 진단과 달리 실패는 위 두 assertion에서 발생했으며 collection/setup 실패가 아니다.

이 focused pass 수는 전체 954에 다시 합산하지 않는다. Rubric criterion permutation은 이 실험에 포함하지 않았다.

### E1 Bootstrap And Workflow Negative Controls

임시 복사본에 [bootstrap 테스트](../../../tests/scripts/test_bootstrap.py)와 [CI workflow 테스트](../../../tests/scripts/ci/test_ci_workflow.py), 실제 scripts·workflow·source를 배치했다. Autouse guard가 bootstrap script path와 CI helper의 repository root가 모두 격리 경로인지 검사한다. 두 witness는 bootstrap `main()`의 첫 실패 exit·후속 미실행, CI의 main PR entry·무경로필터·prospective merge checkout 정책을 관찰한다.

| Isolated State | Existing Two Modules | Two Witnesses |
| --- | --- | --- |
| baseline | 58 passed | 2 passed |
| bootstrap의 nonzero 즉시 반환 제거 | 58 passed | 1 failed, 1 passed: `main()`이 17 대신 0 반환 |
| PR trigger에 `paths-ignore: ['src/**']` 추가 | 58 passed | 1 failed, 1 passed: 경로 필터 구조 위반 |
| checkout에 PR head의 `ref` 명시 | 58 passed | 1 failed, 1 passed: prospective merge 정책 위반 |

실제 GitHub 이벤트를 생성한 결과가 아니다. YAML과 entrypoint의 잘못된 변경이 기존 assertions를 통과하는지 확인한 실험이다. Bootstrap 외부 명령은 fake step이므로 설치·sync·hook 변경을 실행하지 않았다. Source 두 파일의 SHA-256은 실행 전후 동일하다.

- Bootstrap: `e407bc871e1d7c1719d8e5cfc13290f8eebdb58bf8228e42e96b259613ee0814`.
- CI workflow: `f82f50d40765b9e1475d7813adbf292a0cb8e382dd266c60952615c449fc16d7`.

Lead는 caller의 raw script/log와 import/path guard·assertion 실패를 읽어 확인했다. Lead 자체 pytest 실행으로 표시하지 않는다. 이 58개는 D2의 58개와 다른 대상이며 어느 쪽도 전체 954에 합산하지 않는다.

### E2 Uncertain OpenSpec Routing

이 probe는 **review lead가 직접 실행**했다. Caller의 E1 mutation 실험이나 specialist 자체 실행과 구분한다. 실제 [classifier](../../../scripts/ci/classify_changes.py)를 `/usr/bin/python3`와 `--stdin`으로 실행하고 `openspec/specs/example-capability/spec.md`를 입력했다. Cwd는 valid-name canonical capability directory가 있는 자동 정리 임시 fixture였다.

| Fixture Condition | Exit | OpenSpec Selection | Python Selection |
| --- | --- | --- | --- |
| active Change inventory 부재 | 0 | bulk false, Spec `example-capability`, Change targets 빈 값 | full tests/type true |
| active Change가 symlink | 0 | 동일 | 동일 |
| 관련 capability path가 directory 대신 file | 0 | 동일 | 동일 |

실행 파일의 command·selector output을 확인했으며 실제 OpenSpec validator/npm이나 hosted Actions를 실행한 결과가 아니다. 실제 runner는 이 flags에서 선택된 Spec만 검증한다. 현재 원본 classifier를 바꾸지 않은 입력 경계의 반례다.

### E3 Inbox Required Scalar

Lead가 system Python의 `runpy.run_path()`로 실제 [Inbox validator](../../../scripts/validate_inbox_artifacts.py)를 로드해 세 임시 artifact를 `validate_changed_paths()`에 전달했다. 정상 description, `description: # TODO`, `description: "" # TODO`가 모두 `errors=[]`였다. Native validator의 required nonempty 판정에 관한 결과이며 문서 의미나 CI merge 여부의 실험이 아니다.

## Artifact And Snapshot Checks

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | 전체 문서 metadata | 실제 YAML parser의 required `type/title/description` 검증, **27/27** |
| ✅ Pass | Inbox bundle contract | repository native validator exit 0, 날짜·시각·type·root README |
| ✅ Pass | Markdown·heading·링크·fragment | repository rumdl config로 **27파일, issue 0** |
| ✅ Pass | Editor diagnostics | 보고서 묶음의 `problems`: `No errors found` |
| ✅ Pass | 검토 대상 동일성 | frozen HEAD·branch 유지, target **94/94 Git blob** 동일, source/test/Spec/dependency/CI 변경 없음 |
| ✅ Pass | Inventory 완전성 | tracked tests에서 guidance 1개를 제외한 94파일과 일치, full-read row 94개 |
| ✅ Pass | 산출물 구성 | 제품 domain 7개·공통 지원 1개·별도 하위 리뷰 15개; review 24개 + plan/inventory/validation = **27문서** |
| ✅ Pass | 도메인 finding 집계 | 요약 중복을 제외한 **Major 12개·Minor 14개**, 현재 반례·mutant·정적 공백 포함 |

Finding 수와 pass 수는 설계 품질 점수가 아니다. Source·test·Spec·설정·CI를 고치지 않고 보고서에 영향·최소 후속 작업을 남겼다. PR #258 귀속 경로와 탐색 링크를 정정했으며 현재 저장된 문서를 기준으로 세션을 이어갈 수 있다.

## Evidence Limits

모든 review batch를 완료했다. 정적 도출만 한 gap을 runtime 재현으로 표시하지 않는다. 전체 mutation testing, 모든 OS·의존성 조합, 운영 데이터·운영 Airflow 배포 검증은 수행하지 않았다. 관련 source·Spec 대조는 테스트 설계와 material candidate에 필요한 경로에 한정했다.
