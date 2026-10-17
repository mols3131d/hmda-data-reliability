---
type: report
title: Domain Audit Remediation Loops
description: PR 252 결함 수정 루프의 실행 근거, 검토 결과와 다음 전이를 기록합니다.
---

# Domain Audit Remediation Loops

## Current State

Phase: Finalize. Loops used: 5/30. Acceptance: open. Candidate exit: BLOCKED on detector 0 contract choice. Bounded finishing work: preserve/publish reviewed checkpoints and current PR description.

Starting revision과 scope는 [11](11-plan-remediation-execution.md), 실행할 항목은 [03](03-plan-audit-completion-checklist.md)을 따른다. 아래 실행은 실제 수행 후 결과와 검토 근거를 기록한다. 과거 [08](08-report-cloud-validation.md)의 수치를 이번 실행으로 표현하지 않는다.

## Loop 1 — HMDA Source Column Mapping

- Research: `_replace_partition_rows`는 staging의 column order대로 insert했고 input union의 BY NAME은 target order를 보호하지 않았다. 원천 값 보존과 transaction rollback의 기존 계약을 적용했다.
- Plan/Work: 기존 partition test에 CSV header 재정렬과 exact values·다른 연도 partition 전체 row 보존 oracle을 추가했다. Production 변경은 `INSERT ... BY NAME` 한 곳이다.
- RED: `tests/hmda_data/test_ingestion_partition.py::test_partition_reload_preserves_values_after_source_columns_are_reordered -q` → 1 failed, 값 `(95, 420000)`이 기대 `(350000, 120)` 대신 나타난 assertion 실패. 환경/collection 오류가 아니다.
- GREEN: 같은 module 14 passed; `tests/hmda_data -q` 77 passed. `.venv/bin/python -m pytest`로 실행했고 기본 memory/stress 제외 정책을 유지했다.
- Review: public load result의 값과 unrelated partition을 직접 검증한다. 기존 stale-state·rollback 회귀가 통과했다. 내부 SQL 문자열을 고정하지 않는다. 독립 최종 리뷰는 아직 남아 있다.
- Dispatch: I1 local implementation/validation 완료, 다음 R-REV-01. 이 상태를 최종 PR 완료로 표현하지 않는다.

## Loop 2 — Review Parser Failure Provenance

- Research: output byte limit 안의 deep JSON(20,001 bytes)와 큰 정수 JSON(5,006 bytes)이 `json.loads`의 RecursionError/ValueError로 evidence 저장을 우회한다. 기존 response-schema-invalid 경로와 저장 정책을 재사용한다.
- Work: public review service test 두 case에서 typed failure, provider 1회, invocation path와 load된 record metadata, raw output 미저장을 확인한다. Parser/model validation의 좁은 try에서 ValueError(JSON/Pydantic validation 포함), TypeError, RecursionError만 처리한다.
- RED: 새 parameterized test 2 failed, 실제 RecursionError와 integer conversion ValueError. GREEN: service module 18 passed, `tests/review_ai -q` 159 passed.
- Review: input rejection·provider unavailable·accepted review·provenance failure의 기존 회귀가 유지됐다. MemoryError 같은 process failure를 무차별 catch하지 않는다. Provider stub이므로 live model evidence가 아니다.
- Dispatch: I2 local implementation/validation 완료. 다음 schema executor/evaluator의 commit 이후 실패 상태와 안전한 replay.

## Loop 3 — Schema Recovery Cleanup Failure

- Research: executor의 with 종료에서 unlock 또는 DuckDB close가 실패하면 이미 commit된 결과까지 before-target failure로 분류했다. Evaluator는 recovery 예외를 무조건 `target_mutated=False`로 기록했다.
- Plan/Work: 완료한 typed result를 resource 종료까지 보존하고 해당 cleanup 예외에 after-target/replay stage, mutation state, actual state와 resume-verification을 연결한다. 아직 완료 결과가 없는 lock 획득·검증 실패는 기존 의미를 유지한다. Evaluator는 해당 예외의 table-replaced evidence를 읽는다.
- RED: executor의 before/after state × unlock/close 4 cases가 실제 DB after-state와 metadata 불일치로 실패. Actual executor를 거치는 evaluator unlock case도 RED였다. Executor 수정 뒤 evaluator의 target-mutated assertion이 추가로 RED여서 projection 누락까지 확인했다.
- GREEN: candidate/executor/schema-drift evaluator 3 modules, `-q -n 2` → 36 passed. Fault 제거 후 동일 승인 replay는 already-restored이고 executed actions는 profile 재실행뿐이다.
- Review: approval mismatch·diverged state·rollback 경계는 기존 회귀를 유지한다. Test는 OS lock/connection 종료 boundary만 제어하고 actual DB mutation과 identity를 사용한다. 완료 결과가 없는 오류를 commit됐다고 추정하지 않는다.
- Dispatch: I3 local implementation/validation 완료. 전체 runtime validation과 independent assessment는 아직 남아 있다.

## Loop 4 — SDK Boundary Detection Strength

- Research: 기존 RecordingTransport는 actual SDK adapter를 대체하므로 SDK kwargs의 model mapping 오동작을 검출하지 못했다.
- Work: OpenAI SDK와 `_OpenAIChatCompletionTransport`를 그대로 통과시키고 httpx MockTransport에서만 네트워크를 대체한다. 독립된 고정 payload 전체, normalized output/usage/request ID, 400/500/connection error와 hidden retry 부재를 확인했다. Production 변경 없음.
- GREEN: `tests/runtime_ai -q` → 35 passed.
- Negative control: 임시 directory에 src·Runtime AI tests·pyproject를 복사하고 해당 provider의 `model=request.model`만 `model="audit-wrong-model"`로 바꿨다. Autouse fixture로 실제 provider import가 복사본인지 검증했다. 새 SDK payload test 1 failed / 나머지 34 passed; assertion에 잘못된 model이 표시됐다. 원본에는 mutation을 적용하지 않았다.
- Experiment limits: 처음 격리 시도들은 pytest config의 원본 `pythonpath` 때문에 import guard에서 35 errors였다. 이 결과를 검출 성공으로 계산하지 않았다. Config도 복사본에 고정하고 editable import hook을 제외한 interpreter에서 위 결과를 얻었다. 실제 외부 SDK 서버 호출은 없었다.
- Review/Dispatch: I4 완료. Actual adapter response/error 경계를 검증하며 production request를 테스트 double로 재구현하지 않았다. 다음 Airflow 정상 환경 재검증.

## Loop 5 — Integration Validation And Independent Review

Tested implementation revision: `e49eee7352b0deab87f8c507f21606afc42e64c9`. 다음 결과는 동일 구현 tree에서 실행했다. 아래 doc-only 갱신은 source/test를 바꾸지 않는다.

| Check | Result | Command / scope |
| --- | --- | --- |
| Full non-resource suite except separately run DAGRun | 926 passed / 2 skipped, 42.51s | `.venv/bin/python -m pytest --ignore=tests/orchestration/test_airflow_dagrun.py -q -ra -n 2` |
| Actual Airflow DAGRun | 5 passed, 104.00s | `.venv/bin/python -m pytest tests/orchestration/test_airflow_dagrun.py -q -ra` |
| Type check | Pass | `.venv/bin/python -m ty check` |
| Ruff | Pass | changed 9 source/test files, `ruff check` |
| Dependency boundaries | Pass | `.venv/bin/tach check`; negative-path/AST 회귀도 full suite에 포함 |
| Wheel | Pass | `uv build --wheel --offline`; uv 0.12.5와 backend requires 범위의 경고가 있었으나 build 성공 |
| Inbox metadata | Pass | native `scripts/validate_inbox_artifacts.py`, changed artifacts |

Focused test는 full suite와 중복되므로 합산하지 않는다. 926개와 별도 DAGRun 5개는 중복되지 않는다. Skip은 zizmor cached audit 부족과 Windows npm/Node prerequisite 각 1건이며 domain assertion failure가 아니다. 외부 LLM/Langfuse live proof는 실행하지 않았다.

Local `origin/main`의 추가 commit은 agent review workflow 이동 1건이며 runtime/source/tests 변경은 없다. 현 head 검증은 최신 main과의 prospective merge CI를 자동으로 대표하지 않는다.

Review: [13](13-review-remediation-implementation.md)의 independent lead·quality·adversarial assessment는 네 구현 단위에 대해 clear다. 현재 acceptance gap은 detector 계약 선택이며 범위 밖 변경을 추측으로 구현하지 않는다. Dispatch: 넓은 추가 조사 없이 현재 blocker를 보존하고 Finalize에서 bounded delivery와 재개 상태를 검증한다. Loop count를 5로 증가시켰으며 Finalize는 새 loop로 계산하지 않는다.
