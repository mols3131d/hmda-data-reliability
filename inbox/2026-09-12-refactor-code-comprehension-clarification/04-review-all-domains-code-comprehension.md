---
type: review
title: "All-Domain Code Comprehension Refactor Review"
description: "현재 refactor revision의 7개 도메인별 동작 보존, 제약 준수와 검증 근거를 검토한다."
tags:
  - "domain:cross-domain"
  - "capability:code-comprehension"
  - "regression-review"
---

# All-Domain Code Comprehension Refactor Review

> [!IMPORTANT]
> **Pass** — 실행 코드와 도메인 경계는 승인 가능한 상태이며 회귀는 확인되지 않았다. inbox 문서의 상대 링크 오류(F1)가 해결되어 코드 및 핵심 검증 기준을 충족한다. 계획 문서의 stale `Next Steps`(F2)는 후속 작업으로 정리 가능하다.

- **Target** — [refactor/code-comprehension-clarification](../../)
- **Revision** — `6f0db10` against baseline `59a0ee4`
- **Scope** — HMDA Data, Data Platform, Data Operations, Reliability, Review AI, Runtime AI, Orchestration 및 scripts/shared의 source·tests·inbox artifact

## Domain Verdicts

| Domain | Verdict | Evidence summary |
| --- | --- | --- |
| Data Platform | Pass | DuckDB, SQL quoting, artifact lock/hash 변경에서 회귀를 확인하지 못함 |
| HMDA Data | Pass | ingestion, partition, synthetic case, EDA 계약과 기존 테스트 유지 |
| Orchestration | Pass | Airflow data-plane dependency와 control-plane 분리 유지 |
| Data Operations | Pass | lifecycle, quality gate, runner의 read-only·promotion·lock 경계 유지 |
| Reliability | Pass | deterministic detection, impact, remediation, recovery 계약 유지 |
| Runtime AI | Pass | provider-neutral settings, retry, error normalization, output limit 계약 유지 |
| Review AI | Pass | advisory review, deterministic validation, provenance 경계 유지 |
| Scripts and Shared | Pass | 실행 동작 및 새 review/issue artifact의 Markdown 링크 검증 통과 |

## Findings

| ID | Severity | Finding | Action |
| --- | --- | --- | --- |
| F1 | 🟢 **Resolved** | 새 out-of-scope issue 문서의 source·test 링크가 문서 위치 기준으로 해석되지 않음 | 링크를 `../../src/...`, `../../tests/...`, `../../scripts/...` 형태로 수정 완료 |
| F2 | 🟡 **Minor** | 계획 문서의 모든 domain 작업은 완료로 표시됐지만 `Next Steps`에는 초기 작업이 남아 있음 | 완료 상태에 맞게 stale `Next Steps`를 제거하거나 현재 후속 조치로 갱신 |
| F3 | 🔵 **Note** | lifecycle의 동일 shared artifact lock 중첩과 lock failure normalization은 후속 검토 가치가 있음 | 별도 correctness/safety 변경 단위에서 focused test와 contract 검토 |

## Details

### F1 · Inbox Markdown 링크 오류

🟠 **Major**

#### Locations · F1

- [01-note-out-of-scope-issues.md](01-note-out-of-scope-issues.md)
  - 링크가 있는 issue entry
- [inbox/AGENTS.md](../../AGENTS.md)
  - 독립 Markdown artifact와 작업 산출물 규칙
- [.github/instructions/markdown.instructions.md](../../.github/instructions/markdown.instructions.md)
  - Markdown link와 readability 규칙

#### Evidence · F1

문서는 `inbox/2026-09-12-refactor-code-comprehension-clarification/` 아래에 있다. 따라서 레포 루트의 `src/`, `tests/`, `scripts/`를 가리키는 링크는 문서 기준으로 두 단계 올라가야 한다. 현재 문서는 `src/hmda_reliability/...`와 같은 경로를 사용하고 있어 `rumdl`이 `MD057` relative link 오류를 보고했다.

#### Impact · F1

새 작업 artifact를 열어도 source와 test 위치로 이동할 수 없고, 이번 커밋의 Markdown 제약 검사가 실패한다. 기존 inbox 전반의 오류와 달리 해당 링크 오류는 이번 revision에서 추가된 문서에 직접 귀속된다.

#### Action · F1

다음과 같이 링크를 문서 위치 기준으로 수정한다.

- `../../src/hmda_reliability/data_platform/artifacts.py`
- `../../tests/data_platform/test_artifacts.py`
- `../../scripts/rulesync.py`

수정 후 해당 문서에 대해 `uv run rumdl check inbox/2026-09-12-refactor-code-comprehension-clarification/04-review-all-domains-code-comprehension.md`와 새 issue 문서 검사를 실행한다.

### F2 · 계획 상태와 Next Steps 불일치

🟡 **Minor**

#### Locations · F2

- [00-plan-code-comprehension-clarification.md](00-plan-code-comprehension-clarification.md)
  - Domain completion checklist
  - `Next Steps` section

#### Evidence · F2

Domain 1부터 Domain 8까지 조사·작업·검증 항목이 모두 `[x]`로 표시되어 있다. 그러나 문서 끝의 `Next Steps`는 여전히 Domain 1 조사 착수와 계획 확정을 안내한다.

#### Impact · F2

현재 작업 상태를 읽는 사람이 완료된 작업과 아직 시작하지 않은 작업을 구분하기 어렵다. 실행 코드에는 영향이 없지만 inbox checkpoint의 상태 신뢰성을 낮춘다.

#### Action · F2

완료된 revision의 후속 조치로 교체하거나, 작업이 종료되었음을 명시하고 실제 미해결 항목은 별도 issue/review artifact로 연결한다.

### F3 · 후속 안전성 검토 후보

🔵 **Note**

#### Locations

- [incident_lifecycle.py](../../src/hmda_reliability/data_operations/incident_lifecycle.py)
  - `run_incident_lifecycle`
  - `_dbt_projection_id`
- [artifacts.py](../../src/hmda_reliability/data_platform/artifacts.py)
  - `artifact_projection_lock`

#### Evidence

lifecycle 분석 중 shared artifact lock을 획득한 뒤 `_dbt_projection_id`가 동일 lock을 다시 획득한다. 또한 lifecycle 바깥 lock failure의 예외 정규화와 reader lock 파일 open mode는 현재 작업에서 수정하지 않고 [01-note-out-of-scope-issues.md](01-note-out-of-scope-issues.md)에 범위 외 이슈로 기록되어 있다.

#### Impact

현재 테스트와 Linux 실행 환경에서는 회귀가 관찰되지 않았다. 다만 lock 재진입 의미론과 infrastructure exception의 caller 노출은 별도 correctness/safety 변경에서 명시적으로 검증할 가치가 있다.

#### Action

현재 리팩터링에 섞지 말고 별도 변경 단위에서 lock ownership, failure normalization, concurrent reader behavior를 focused test로 고정한다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ `Pass` | 전체 pytest | `605 passed, 1 skipped` |
| ✅ `Pass` | 변경과 직접 관련된 집중 pytest | `29 passed` |
| ✅ `Pass` | Pylance diagnostics | 오류 없음 |
| ✅ `Pass` | `git diff --check` | 통과 |
| ✅ `Pass` | Ruff lint와 format check | 통과 |
| ✅ `Pass` | Tombi TOML lint | 통과 |
| ✅ `Pass` | `rumdl check` (F1 대상 문서) | `01-note-out-of-scope-issues.md` 상대 링크 수정 후 No issues 확인 |
| ✅ `Pass` | 동작 회귀 후보 focused path | lifecycle, artifacts, runtime provider, schema recovery 테스트 통과 |

## Risks and Limits

- 이번 review는 `6f0db10`과 `59a0ee4`의 diff 및 현재 source·tests를 기준으로 했다.
- 테스트 통과는 correctness의 완전한 증명이 아니며, 실제 provider 호출과 운영 환경의 동시성은 별도 검증이 필요하다.
- 기존 inbox의 Markdown 오류는 이번 작업의 변경으로 발생한 오류와 분리해서 추적해야 한다.
