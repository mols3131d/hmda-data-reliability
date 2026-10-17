---
type: plan
title: PR 252 Completion Checklist
description: PR 252의 완료된 수정과 남은 규칙별 판단, 구현, 검증, 독립 리뷰 및 전달 조건을 추적합니다.
tags:
  - reliability
  - testing
  - review
---

# PR #252 Completion Checklist

**Status: Remediation in progress; not_ready.** 세 major 결함 수정과 SDK 테스트 보강은 구현·로컬 검증·[독립 리뷰 clear](13-review-remediation-implementation.md)를 확보했다. 남은 핵심은 탐지 규칙별 의미를 확정하고 필요한 경계 수정을 검증한 뒤 전체 완료를 판정하는 일이다. `0`의 일괄 허용·금지를 먼저 결정하지 않고, 사용자가 지적한 사례별 차이를 검토한다.

## Current Evidence

2026-10-17 확인 기준이다. 아래 head는 이 체크리스트 갱신 전의 조사 대상이며 이후 head/base의 CI 결과로 자동 확장하지 않는다.

| Item | Verified State |
| --- | --- |
| PR | Open / Draft / mergeable; head `26068fa5e159e4035e2c6f6a2e07ddc9c935c8cc`, GitHub가 반환한 base SHA `8bc62fa6ec995f2e57456d55712b36ff11b1f1d9` |
| Existing implementation | `e49eee7352b0deab87f8c507f21606afc42e64c9`와 조사 대상 head의 source/test/spec 및 dependency 파일 차이 없음 |
| Local validation | 기존 실행 926 passed / 2 skipped 및 별도 실제 Airflow DAGRun 5 passed; 이번 정리에서 재실행하지 않음. [12](12-report-remediation-loops.md) 참조 |
| Remote CI | 해당 head의 [CI Lite 39019803074](https://github.com/mols3131d/hmda-data-reliability/actions/runs/39019803074) completed / success. Prospective merge checkout·dependency boundary·build·Python·selected tests step이 실제 성공 |
| Review | 기존 네 수정 단위의 independent clear. 현재 human approval 0, changes requested 없음, review thread 없음. 전체 PR 완료 판정은 미완료 |

## Remaining Completion Path

다음 C1–C6이 현재 남은 실행 순서다. 아래 I5/I8의 상세 완료 조건이며 별도의 경쟁 계획이 아니다. 이번 정리로 제품 동작이나 계약 선택을 확정하지 않았다.

- [ ] **C1 — 규칙별 판정표와 사용처 대조.** 직전 상태 대비 변화, 고정 정상 기준 대비 차이, 현재 데이터의 절대 상태를 구분한다. 무변화·악화·개선·양수 기준과 정확히 같은 값·비교 기준 부재·baseline 행 수 0·freshness 측정 불가를 포함한다. 각 사례에 예상 경보 종류와 근거를 쓰고, 현재 detector와 quality gate가 무엇을 검사하는지 대조한다. 무변화가 데이터 전체의 정상 판정을 뜻하지 않도록 한다.
- [ ] **C2 — 계약과 수정 범위 확정.** 판정표를 바탕으로 volume/null의 `0` 의미와 양수 경계값을 정하고 현재 caller에 미치는 영향을 기록한다. ‘실제 악화가 있어야 한다’는 조건의 적용 대상을 구분한다. 명세의 `초과`/`이상` 문구도 맞춘다. Spec-level 동작을 변경하면 [OpenSpec 경계](../../openspec/README.md)에 따라 delta Spec에서 먼저 다룬다. 아직 선택되지 않은 권장안을 확정된 요구사항으로 구현하지 않는다.
- [ ] **C3 — 회귀 테스트와 최소 구현.** 확정된 각 사례의 기대 결과를 독립적으로 검사한다. 현 동작과 달라져야 하는 사례는 수정 전 실패를 확인한 뒤 최소 수정으로 통과시킨다. Volume/null 중 하나만 악화되는 경우도 검사해 다른 경보가 섞이지 않게 한다. Schema와 freshness의 기존 계약을 보존한다.
- [ ] **C4 — 변경 revision의 영향 검증.** Detector·quality gate의 focused 테스트부터 실행하고 필요한 전체 suite·정적 검사·OpenSpec 검사 및 CI를 완료한다. 기존 926개와 Airflow 5개의 근거는 유효 범위에서 재사용하고, 새 변경의 근거로 무조건 대체하지 않는다. 최종 base/head 또는 대응 prospective merge의 required check를 확인하며 실패·skip·미검증은 구분한다.
- [ ] **C5 — 독립 리뷰와 전체 acceptance.** Detector 변경의 정상 동작과 실패·경계 사례를 독립 검토하고 발견된 필수 항목을 처리한다. 기존 네 단위의 clear는 해당 구현과 전제가 같을 때 재사용한다. 남은 finding을 단순 후속 작업으로 적었다는 이유만으로 해결 처리하지 않는다.
- [ ] **C6 — 근거 전달과 readiness 재판정.** 체크리스트·세션 재개 지점·PR 본문을 최종 변경과 검증 revision에 맞춘다. 알려진 필수 미완료가 없고 현재 base/head에 근거가 유효할 때 review readiness를 판정한다. 기술적 준비 완료와 사람의 승인·병합을 구분해 전달한다.

C1과 C2의 초안 조사는 현재 계약 선택 없이 진행할 수 있다. 동작을 바꾸는 C3은 해당 사례의 계약이 정해진 뒤 진행한다. Ready 전환·approval·merge는 별도의 인간 결정 단계이며 자동 수행 항목이 아니다.

새 컬럼별 정책 엔진, 별도 절대 품질 검사와 R-DET-02의 baseline 누락 정책은 자동으로 이번 PR 필수 범위에 추가하지 않는다. 필요성이 확인되면 별도 요구사항으로 기록하되, 이번 수정의 필수 선행조건이라면 먼저 범위와 완료 조건을 조정한다. 외부 LLM/Langfuse live 호출은 이 bounded detector 수정의 완료 조건이 아니다.

## Historical Audit Work Packages

아래 L1–L14는 감사 이력이며 구현 완료 항목이 아니다. 실제 수정 진행과 미완료 gate는 다음 Implementation Work Packages에서 추적한다.

- [x] L1 — 고정 tree의 187개 source/test/spec inventory 확인.
- [x] L2 — Reliability 전수 정적 감사; detector·schema recovery 결함과 기존 safeguard 대조.
- [x] L3 — Data Operations 전수 정적 감사; quality gate, dbt lock, promotion/failure boundary.
- [x] L4 — HMDA Data 전수 정적 감사; source validation, partition re-ingestion 및 값 손상 재현.
- [x] L5 — Data Platform 및 dbt 전수 정적 감사; locks, transaction, artifact pair, SQL/dbt contracts.
- [x] L6 — Review AI 전수 정적 감사; evidence binding, structured outputs, advisory/evaluation/projection boundary.
- [x] L7 — Runtime AI 전수 정적 감사; settings, provider, normalization 및 SDK test gap 검증.
- [x] L8 — Orchestration 전수 정적 감사; DAG dependencies, blocking, config/re-execution. 실제 DAGRun 통과는 미검증.
- [x] L9 — 고정 revision의 focused/full domain pytest 실행 및 pass/fail/skip 기록. 실행 완료이지 통과 판정이 아님.
- [x] L10 — detector, HMDA, Review AI, schema unlock 경계 실제 재현 및 safeguard 반증 확인.
- [x] L11 — 격리 copy의 SDK negative control 및 temporary DuckDB unlock fault injection.
- [x] L12 — 미해결 결함·test gap별 영향, 후속 책임 도메인과 acceptance oracle 기록. 수정 PR/담당자 수락은 아직 없음.
- [x] L13 — 두 specialist와 lead의 독립 감사/최종 문서 assessment 완료: clear (감사 기록 한정). 실행 blocker는 별도 유지.
- [x] L14 — 187 reviewed / excluded 0 확인; 최종 readiness는 not_ready. Airflow 정상 runner 재실행 및 후속 결함 처리 필요. Ready 전환·merge는 별도 승인.

## Implementation Work Packages

[남은 작업 조사](14-research-remaining-work.md)는 이전 head `69cc4002`의 근거와 선택지를 소유한다. 최신 확인은 위 Current Evidence를 따른다. 현재 미완료는 I5와 그 변경의 I8이며 완료 항목을 미수행으로 되돌리지 않는다.

실행 계획: [11 — Remediation execution](11-plan-remediation-execution.md). 실행·검토 근거: [12 — Loops](12-report-remediation-loops.md). 2026-10-17 사용자는 이 PR branch에서 수정과 검증을 진행하도록 요청했다.

- [x] I1 — R-HMDA-01: exact-value regression RED/GREEN, unrelated partition 보존. HMDA domain 77 passed; 최종 independent gate는 I8.
- [x] I2 — R-REV-01: parser failure의 typed result와 persisted invocation RED/GREEN. Review AI domain 159 passed; 최종 independent gate는 I8.
- [x] I3 — R-SCH-01: post-commit failure evidence, evaluator, safe replay 회귀. Candidate/executor/evaluator 36 passed; 최종 independent gate는 I8.
- [x] I4 — R-TD-02: 실제 SDK adapter test와 negative-control 검출. 35 passed; 격리 model mapping mutation에서 1 failed / 34 passed.
- [ ] I5 — R-DET-01: C1–C3의 규칙별 판정·계약 확정·경계 회귀와 최소 수정. 단순한 `0` 허용/거부 질문보다 사례별 의미 검토가 선행한다.
- [x] I6 — Airflow DAGRun 5개 정상 환경 재실행: 5 passed, 104.00s. Production task/psutil monkeypatch 없음.
- [x] I7 — 현 구현 revision `e49eee73`의 full suite 926 passed / 2 skipped와 별도 Airflow 5 passed, Ruff/ty/Tach/wheel 검증. Detector 또는 구현 변경 시 해당 evidence를 재평가한다.
- [ ] I8 — 네 단위는 `e49eee73`에서 independent clear. Detector 구현 후 해당 변경의 검증·새 assessment까지 완료해야 전체 gate를 닫는다.
- [x] I9 — 현재 네 단위 checkpoint를 원격 PR branch에 전달하고 continuation을 기록했다. PR 본문은 현재 source/test tree와 남은 detector 결정을 반영한다. 후속 구현 후 evidence·delivery를 다시 갱신한다.

## Audit Inventory

Untruncated Git tree에서 직접 추출한 Python 파일 수. `__init__.py`와 conftest도 포함한다. `tests/dbt` 1개는 Data Platform에 포함한다.

| Domain | Source | Test | Related Specs | Full Audit |
| --- | ---: | ---: | ---: | --- |
| Reliability | 52 | 27 | 10 | Reviewed (static) |
| Data Operations | 9 | 5 | 2 | Reviewed (static) |
| HMDA Data | 17 | 8 | 3 | Reviewed (static) |
| Data Platform | 4 | 5 | 2 | Reviewed (static) |
| Review AI | 12 | 14 | shared reliability-agentic-review | Reviewed (static) |
| Runtime AI | 4 | 3 | no dedicated spec | Reviewed (static) |
| Orchestration | 4 | 5 | 1 | Reviewed (static) |
| **Total** | **102** | **67** | **18 unique** | Reviewed (static) |

## Historical Validation Boundary

클라우드 Python 3.13.16과 locked dependencies로 실행했다. Private clone 인증 대신 connector로 받은 exact-head snapshot을 Git blob SHA와 대조했다. Full suite는 **548 passed / 4 failed / 1 skipped**였고 Airflow serial retry는 5 failed였다. PID/proc 불일치와 SQLite 오류를 기록했으며 정상 runner 재실행이 필요하다. 상세 원인·명령·독립 검토 범위는 08/09 문서를 따른다. 아래 과거 loop의 “unrun”은 당시 상태이며 현행 상태가 아니다.

## Review Loop 1

- Research: baseline tree 1,134 entries, not truncated. Domain folder inventories와 18 OpenSpec을 구분했다.
- Plan: 각 도메인을 별도 감사 루프로 나누고 검증·재현·독립 리뷰를 별도 completion gate로 설정했다.
- Self review: 단순 파일 수집을 검토 완료로 오인하지 않도록 전 도메인 Pending으로 표시했다.
- Next: 7개 도메인의 중요 상태 변경/실패 경계를 소스와 테스트에 대조한다.

## Review Loops 2–8 — First Static Pass

[Seven-domain first pass](04-report-seven-domain-risk-first-pass.md)에 계약·구현·테스트 샘플, 기존 safeguard, 반례 후보 및 미검증 부분을 기록했다. 전 도메인 source/test inventory만 확인했으며 full-file semantic review 또는 pytest가 아니므로 L2–L8의 완료 체크박스는 변경하지 않았다. R-TD-01 외 확정 production defect 없음. CI-only evidence는 기능 테스트의 대체재가 아님.

## Loop 9 — Inventory Consistency Review

- Git tree `29c48e468d470ee02ac470059b556fed9af960ce`의 all 187 domain source/test/spec paths와 file inventory를 직접 대조했다. 187 valid, zero duplicate, zero nonexistent.
- Self-review에서 `tests/dbt/test_analytics_foundation.py`가 Data Platform tests prefix로 잘못 축약된 항목을 발견해 수정했다. 이후 path set 검증을 재실행했다.
- Coverage status는 모든 파일 `pending` 또는 `sampled`; domain semantic review와 pytest는 미완료다.

## Historical Execution Plan (previously unrun)

Repository guidance: [Testing](../../docs/development/testing.md). 아래는 작업 실행자가 고정 baseline의 isolated checkout에서 수행해야 할 검증이며, 여기서는 **실행하지 않았다**.

```bash
uv sync --locked
uv run pytest tests/reliability/test_schema_recovery_candidate.py tests/reliability/test_schema_recovery_executor.py tests/reliability/test_schema_drift_evaluation.py
uv run pytest tests/reliability tests/data_operations tests/hmda_data tests/data_platform tests/dbt
uv run pytest tests/review_ai tests/runtime_ai tests/orchestration
```

Optional integration prerequisites/marker가 있는 테스트의 skipped 결과는 로그에 따로 적는다. baseline GitHub main 및 PR head의 코드 차이가 Inbox 문서뿐이라 해도, run 없이 pass로 표시하지 않는다. 최종 domain validation의 pass/fail/skip, revision 및 환경을 이 목록에 연결한다.

## Loop 10 — Detection Boundary Review

- **Research:** `DetectionThresholds`에서 `volume_drop_ratio=0`, `null_spike_delta=0`을 허용하며 `BasicIncidentDetector`가 비교 변화량이 0일 때도 `0 < 0` false에 따라 skip하지 않음을 정적으로 검증했다.
- **Test:** 격리 Python Pydantic threshold/분기식 조건 검산은 양쪽 false-positive 조건이 true임을 보여줬다. 이는 repository-native pytest가 아니다.
- **Review:** 기본 설정의 일반 감지 실패로 확장하지 않고 **설정값 0에 국한된 Minor finding R-DET-01**으로 분류했다. Baseline에 없는 column을 0% null로 해석하는 경로 R-DET-02는 spec 결정이 필요한 Note로 분리했다.
- **Improve:** [근거·원인·최소 RED test·validation 한계](06-review-reliability-detection-boundaries.md)를 기록하고 detector 관련 file inventory 8개를 sampled 상태로 갱신했다. L2, L9–L14는 미완료 유지.

### Next Executable Focus (not run)

```bash
uv run pytest tests/reliability/test_basic_incident_detection.py -q
uv run pytest tests/reliability/test_basic_incident_detection.py tests/reliability/test_quality_gate.py tests/reliability/test_profile_snapshots.py -q
```

Loop 10 당시 제안은 `threshold=0`에서 동일한 row count·null rate를 오탐하지 않고 실제 양의 악화는 탐지하는 것이었다. 현재는 위 C1–C2에서 규칙별 사례와 계약을 먼저 확정하며, 이 과거 제안을 채택된 요구사항으로 취급하지 않는다. 확정된 변경은 실행 가능한 동일 repo 환경에서 RED→GREEN으로 검증한다.
