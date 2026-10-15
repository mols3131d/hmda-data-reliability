---
type: plan
title: PR 252 Completion Checklist
description: 일곱 도메인의 감사 완료 조건과 작업 루프별 근거를 추적합니다.
tags:
  - reliability
  - testing
  - review
---

# PR #252 Completion Checklist

**Status: Audit evidence recorded; not merge-ready.** 187개 source/test/spec 정적 검토와 실행·재현을 진행했다. Airflow 통합 실행은 환경 오류로 검증되지 않았고 production 결함은 미해결이다. 현재 근거는 [Cloud validation](08-report-cloud-validation.md), [file inventory](05-report-file-inventory.md), [independent review](09-review-cloud-audit.md)가 소유한다. 아래 이전 loop는 당시 수행 이력이다.

## Completion Work Packages

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

## Inventory Snapshot

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

## Validation Boundary

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

새 regression은 `threshold=0`에서 동일한 row count·null rate를 오탐하지 않아야 하며 실제 양의 악화는 탐지해야 한다. 이 테스트 추가와 구현 수정은 실행할 수 있는 동일 repo 환경에서 먼저 RED→GREEN으로 검증한 별도 최소 변경 단위로 다룬다.
