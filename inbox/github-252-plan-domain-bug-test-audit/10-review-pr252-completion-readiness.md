---
type: review
title: PR 252 Completion Readiness Review
description: PR #252의 감사 이후 결함 수정·회귀 검증 완료 조건과 현재 PR evidence의 간극을 검토합니다.
tags:
  - reliability
  - testing
  - review
---

# PR 252 Completion Readiness Review

> [!IMPORTANT]
> **Blocked (review assessment) / not_ready (PR review readiness)** — 7개 도메인의 감사와 독립 감사 기록은 확보됐지만, 현재 PR Goal에 포함된 제품 결함 수정·회귀 검증은 완료되지 않았다. 정상 runner의 Airflow 통합 검증과 최종 구현 독립 리뷰도 없으므로 Ready 전환이나 병합을 권고하지 않는다.

- **Target** — [PR #252 — 도메인 결함 감사·수정 및 회귀 검증](https://github.com/mols3131d/hmda-data-reliability/pull/252), 현재 Inbox 변경 10개와 해당 감사·검증 근거
- **Revision** — PR base `8bc62fa6ec995f2e57456d55712b36ff11b1f1d9`, PR head `1ba28fa96e72b23ac133ae5304007555b859fce4`; 확인 시점의 `main` head `6ed9882ae8bed628c24931b960c18327ac60f9af` (2026-10-17)
- **Scope** — PR의 명시적 Goal, 실제 diff, 기존 [완료 체크리스트](03-plan-audit-completion-checklist.md)·[클라우드 실행 보고서](08-report-cloud-validation.md)·[독립 감사 리뷰](09-review-cloud-audit.md), readiness 계약의 일치성. 이번 검토에서 도메인 코드를 새로 실행하거나 DualVantage specialist에게 별도 위임하지 않았다.

## Findings

| ID | Severity | Finding | Action |
| --- | --- | --- | --- |
| F1 | 🟠 Major | 확인된 결함과 테스트 공백의 해결 근거가 아직 없어 현재 PR Goal을 수용할 수 없음 | 분리된 수정 PR·RED→GREEN 회귀 결과·독립 리뷰를 #252에 연결해 완료 확인 |
| F2 | 🟠 Major | Airflow 통합 계약의 정상 실행 환경 검증이 없어 최종 acceptance를 판정할 수 없음 | 정상 proc/filesystem runner에서 DAGRun 5개를 재실행하고 결과에 따라 원인을 구분 |
| F3 | 🟡 Minor | Detector의 zero-threshold 의미가 확정되지 않아 무단 계약 변경 위험이 있음 | 계약 소유자가 허용 동작을 결정하고, 계약 변경이 필요하면 별도 승인 후 수정 |

## Details

### F1 · 결함 수정 및 테스트 검출력 완료 근거 부재

#### Locations

- [PR #252의 변경 파일과 설명](https://github.com/mols3131d/hmda-data-reliability/pull/252/files)
  - 현재 diff의 10개 파일은 모두 `inbox/github-252-plan-domain-bug-test-audit/` 문서다.
- [Cloud validation](08-report-cloud-validation.md)
  - `Confirmed Findings And Follow-up`
- [Completion checklist](03-plan-audit-completion-checklist.md)
  - `Completion Work Packages`의 L12–L14는 **감사·기록 완료**이고 수정·회귀 검증 완료가 아니다.

#### Evidence

기존 실행 보고서는 `R-HMDA-01`(컬럼 순서에 따른 값 손상), `R-REV-01`(일부 parser 오류의 invocation evidence 누락), `R-SCH-01`(commit 이후 unlock 실패 상태 오분류)을 Major로, `R-TD-02`(실제 SDK adapter mapping 오류를 기존 테스트가 놓침)를 Minor로 기록한다. 이 finding의 재현 근거와 구체적 회귀 oracle은 08 문서가 소유한다. 기존 [독립 감사 리뷰](09-review-cloud-audit.md)의 `clear`는 감사 기록의 타당성에 한정된다.

PR 본문은 현재 Goal을 감사·수정·회귀 검증까지로 명시하고, 독립적인 수정은 별도 Draft PR로 분리해 #252에서 추적하도록 한다. 하지만 현 diff에는 구현·테스트 수정이 없고 기존 보고서에는 수정 PR 생성 및 owner 수락이 아직 없다고 기록됐다.

- **Scope relation:** `explicit_target` / `acceptance_gap`
- **Disposition:** `current_required` (현재 Goal의 완료 근거)

#### Impact

감사 증거를 실제 제품 수정·회귀 방지 증거로 오인하면 값 손상이나 실패 provenance 계약 위반이 남은 상태에서 완료를 선언하게 된다. #252가 추적 PR인 것 자체는 문제로 보지 않으며, 코드 수정이 반드시 #252의 diff에 있어야 한다는 요구도 하지 않는다.

#### Action

서로 독립적인 결함은 해당 도메인의 최소 수정 PR로 처리하고 #252에 링크한다. 각 수정에서 실패를 드러내는 회귀 oracle, 수정 후 테스트 결과, 영향을 받는 계약과 최종 revision을 제시한다. 특히 SDK adapter 공백은 기존 31개 테스트 통과를 충분한 검출력 근거로 취급하지 않고 adapter를 실제 통과하는 negative control로 닫는다. 후속 구현이 완료되면 현재 통합 revision에 대한 독립 리뷰와 readiness를 다시 판정한다.

### F2 · Airflow 통합 검증의 실행 환경 한계

#### Locations

- [Cloud validation](08-report-cloud-validation.md)
  - `Airflow Execution Limit`
- [Completion checklist](03-plan-audit-completion-checklist.md)
  - `Validation Boundary`
- [DAGRun tests](../../tests/orchestration/test_airflow_dagrun.py)

#### Evidence

기존 7-domain suite는 `548 passed / 4 failed / 1 skipped`, Airflow DAGRun serial retry는 5 failed다. 독립 `psutil.Process()` 호출에서 현재 PID의 `/proc` 항목 부재와 `NoSuchProcess`가 재현됐고, SQLite의 `database disk image is malformed`도 발생했다. SQLite 오류의 정확한 원인은 확정되지 않았다. 이는 **당시 실행 환경의 한계**에 관한 증거이지 production DAG 결함을 확정한 결과가 아니다.

- **Scope relation:** `acceptance_gap`
- **Disposition:** `unknown` (최종 검증에 필요한 환경에서의 결과 부재; review gate를 막음)

#### Impact

정상 환경의 dependency ordering, 실패 차단, asset update 및 promotion 계약을 통과했다고 볼 수 없다. 이전 CI Lite 성공은 이 DAGRun 실패를 해소하거나 도메인 통합 성공을 대체하지 않는다.

#### Action

정상 proc/filesystem과 격리된 metadata DB를 제공하는 runner에서 보고서의 DAGRun 5개 전체를 재실행한다. 실패가 남으면 환경/fixture 문제와 production behavior를 분리해 근거를 갱신한다. 테스트가 통과하도록 production task나 `psutil`을 임의 monkeypatch한 결과를 실제 증명으로 인정하지 않는다.

### F3 · Zero-threshold 계약 판단 필요

#### Locations

- [Detection boundary review](06-review-reliability-detection-boundaries.md)
- [Cloud validation](08-report-cloud-validation.md)
  - `R-DET-01 — Zero Threshold False Positives`
- [Detection implementation](../../src/hmda_reliability/reliability/detection/detector.py)

#### Evidence

기존 실행 근거에서 threshold 0일 때 row count와 null rate가 변화하지 않아도 incident가 생성됐다. 양의 악화만 incident라는 해석과 inclusive threshold 문구의 의미가 충돌할 수 있다. 따라서 현재 동작의 관측과 의도된 계약의 결정은 구별해야 한다.

- **Scope relation:** `scope_change` (기존 계약의 변경이 필요한 경우)
- **Disposition:** `scope_decision` (계약을 바꾸는 선택은 리뷰 권한 밖)

#### Impact

의미를 확정하지 않고 검사식을 수정하거나 threshold 0을 금지하면 사양과 사용자 기대를 조용히 변경할 위험이 있다.

#### Action

Reliability detection의 계약 소유자와 승인권자가 `0`의 의미를 확정한다. 기존 계약 범위에서 해결할 수 있으면 해당 수정·회귀 테스트로 처리한다. 허용값 또는 의미의 계약 변경이 필요하면 먼저 권한 있는 범위 결정을 받고 OpenSpec의 owning contract와 테스트를 일치시킨다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | 현재 PR 상태·diff 확인 | Open/Draft, head `1ba28fa...`, 10개 Inbox 문서만 변경; PR description은 수정과 검증의 미완료를 명시 |
| ✅ Pass | 기존 감사 근거 대조 | 03/08/09에서 187개 정적 감사, 결함 5건, 독립 감사 review의 좁은 `clear` 의미와 미검증 상태를 구분 |
| ✅ Pass | 기존 head의 CI Lite 기록 확인 | Head `1ba28fa...`, [CI Lite run 38679599563](https://github.com/mols3131d/hmda-data-reliability/actions/runs/38679599563) 성공; 이 검사는 도메인 실행의 대체가 아님 |
| ❌ Fail | 기존 도메인 테스트 기록 | 08에 `548 passed / 4 failed / 1 skipped`, Airflow serial retry 5 failed 기록; 이번 검토에서 재실행하지 않음 |
| ⚪ Not Verified | 최신 main과의 통합 증거 | 현재 main `6ed9882...` 대비 PR head가 1커밋 뒤처짐; 현재 base+head 조합의 새로운 검증을 확인하지 못함 |
| ⚪ Not Verified | 신규 구현·정상 Airflow·독립 최종 리뷰 | 현 diff에 수정 구현 없음; 정상 runner 결과와 그 최종 구현에 대한 독립 specialist 결과도 없음 |

## Risks and Limits

- 본 문서는 **현재 PR Goal의 완료·리뷰 준비 여부에 관한 단일 컨텍스트 근거 검토**다. 기존 09의 Quality/Adversarial 독립 감사 근거를 재사용했지만 이번 검토 자체를 새로운 독립 DualVantage 검토로 표현하지 않는다.
- `00-plan-domain-bug-test-audit.md`와 `07-report-domain-audit-session-handoff.md`에는 이전 시점의 미완료 상태가 남아 있다. 현재 감사 상태는 03/08/09의 최신 근거를 우선해 읽고, 과거 checkpoint를 현재 미수행 주장으로 사용하지 않는다.
- 감사 14개 work package 완료는 제품 결함 해소·MVP acceptance 완료와 다르다. 수정 PR이 생성·병합되거나 본 PR의 material state가 달라지면 이전 검증 및 본 readiness 판단의 적용 가능성을 다시 확인해야 한다.
