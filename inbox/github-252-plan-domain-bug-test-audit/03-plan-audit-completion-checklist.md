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

**Status: In Progress; not merge-ready.** First-pass evidence: [7개 도메인 위험 경계 보고서](04-report-seven-domain-risk-first-pass.md). 도메인별 전수 검증은 여전히 미완료다. Baseline: `8bc62fa6ec995f2e57456d55712b36ff11b1f1d9` (`main`).

## Completion Work Packages

- [x] L1 — 기준 소스 트리에서 도메인별 source/test/spec 목록을 추출한다. 인벤토리는 검토 완료를 의미하지 않는다.
- [ ] L2 — Reliability 전수 감사 (첫 정적 패스 수행; 전수 미완료): 승인, 상태 identity, recovery, detector, profile, impact, remediation, evaluation.
- [ ] L3 — Data Operations 전수 감사 (첫 정적 패스 수행; 전수 미완료): quality gate, dbt lock, promotion 및 failure boundary.
- [ ] L4 — HMDA Data 전수 감사 (첫 정적 패스 수행; 전수 미완료): input/source validation, partition re-ingestion, stale guard, synthetic defects.
- [ ] L5 — Data Platform 및 dbt 전수 감사 (첫 정적 패스 수행; 전수 미완료): DuckDB locks, transaction, artifact pair, SQL/dbt contracts.
- [ ] L6 — Review AI 전수 감사 (첫 정적 패스 수행; 전수 미완료): evidence binding, structured outputs, advisory and evaluation/projection boundary.
- [ ] L7 — Runtime AI 전수 감사 (첫 정적 패스 수행; 전수 미완료): settings, provider, error/timeout normalization and tests.
- [ ] L8 — Orchestration 전수 감사 (첫 정적 패스 수행; 전수 미완료): DAG dependencies, quality gate blocking, config, re-execution.
- [ ] L9 — 기준 revision에서 관련 pytest 단독 및 통합 실행, pass/fail/skip evidence.
- [ ] L10 — 결함 의심 재현 또는 반증, spec/기존 safeguard와 교차 검증.
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
