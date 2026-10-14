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

**Status: In Progress; not merge-ready.** First-pass evidence: [7개 도메인 위험 경계 보고서](04-report-seven-domain-risk-first-pass.md), [187-file audit matrix](05-report-file-inventory.md), [Reliability detector 경계 리뷰](06-review-reliability-detection-boundaries.md). 도메인별 전수 검증은 여전히 미완료다. Baseline: `8bc62fa6ec995f2e57456d55712b36ff11b1f1d9` (`main`).

## Completion Work Packages

- [x] L1 — 기준 Git tree에서 [187개 source/test/spec file inventory](05-report-file-inventory.md)를 추출했고 모든 경로의 존재·중복 없음 확인. 인벤토리는 review 완료를 의미하지 않는다.
- [ ] L2 — Reliability 전수 감사 (schema recovery 및 detector zero-threshold 정적 리뷰, 전수 미완료): 승인, 상태 identity, recovery, detector, profile, impact, remediation, evaluation.
- [ ] L3 — Data Operations 전수 감사 (첫 정적 패스 수행; 전수 미완료): quality gate, dbt lock, promotion 및 failure boundary.
- [ ] L4 — HMDA Data 전수 감사 (첫 정적 패스 수행; 전수 미완료): input/source validation, partition re-ingestion, stale guard, synthetic defects.
- [ ] L5 — Data Platform 및 dbt 전수 감사 (첫 정적 패스 수행; 전수 미완료): DuckDB locks, transaction, artifact pair, SQL/dbt contracts.
- [ ] L6 — Review AI 전수 감사 (첫 정적 패스 수행; 전수 미완료): evidence binding, structured outputs, advisory and evaluation/projection boundary.
- [ ] L7 — Runtime AI 전수 감사 (첫 정적 패스 수행; 전수 미완료): settings, provider, error/timeout normalization and tests.
- [ ] L8 — Orchestration 전수 감사 (첫 정적 패스 수행; 전수 미완료): DAG dependencies, quality gate blocking, config, re-execution.
- [ ] L9 — 기준 revision에서 관련 pytest 단독 및 통합 실행, pass/fail/skip evidence.
- [ ] L10 — 결함 의심 재현 또는 반증 (R-DET-01의 Pydantic + 분기식 격리 검산 완료; 앱 pytest/회귀 재현 미완료), spec/기존 safeguard와 교차 검증.
- [ ] L11 — 중요한 검출력 공백에 bounded negative/fault-injection check(격리된 환경에서만).
- [ ] L12 — 확인된 결함·test gaps를 회귀 검증하거나 독립적인 작은 PR에 연결. 미해결 risk/owner 기록.
- [ ] L13 — 최종 revision에 대한 independent reviewer assessment와 blocker 해소.
- [ ] L14 — 모든 source/test의 reviewed 또는 excluded(reason) 상태와 PR validation/readiness 최종 판단. Ready 전환·merge는 별도 승인.

## Inventory Snapshot

Untruncated Git tree에서 직접 추출한 Python 파일 수. `__init__.py`와 conftest도 포함한다. `tests/dbt` 1개는 Data Platform에 포함한다.

| Domain | Source | Test | Related Specs | Full Audit |
| --- | ---: | ---: | ---: | --- |
| Reliability | 52 | 27 | 10 | Pending; schema recovery partial |
| Data Operations | 9 | 5 | 2 | Pending |
| HMDA Data | 17 | 8 | 3 | Pending |
| Data Platform | 4 | 5 | 2 | Pending |
| Review AI | 12 | 14 | shared reliability-agentic-review | Pending |
| Runtime AI | 4 | 3 | no dedicated spec | Pending |
| Orchestration | 4 | 5 | 1 | Pending |
| **Total** | **102** | **67** | **18 unique** | Pending |

## Validation Boundary

GitHub connector는 repo 내용을 읽고 이 문서를 갱신할 수 있지만, 현재 runtime에서 private GitHub clone은 DNS resolution 실패로 실행하지 못했다. DuckDB 패키지도 현재 실행 Python 환경에 없어 repo-native `pytest`는 **Not Verified**다. 문서-only CI Lite success로 대체하지 않는다. 독립 reviewer도 아직 호출하지 못했다.

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

## Required Execution Commands (unrun)

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
