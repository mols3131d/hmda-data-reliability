---
type: review
title: HMDA Data Chatbot Deep Review
description: PR #269 테스트 변경의 챗봇 심층 리뷰와 세션 간 지속 검토 상태를 기록합니다.
tags:
  - "capability:test-design"
  - "multi-perspective"
---

# HMDA Data Chatbot Deep Review

> [!IMPORTANT]
> **Blocked (review in progress)** — 새 `current_required` 결함은 아직 확정하지 않았습니다. 이는 머지 불가 판정이 아니라 이번 챗봇 리뷰의 검토 범위와 독립 재검증이 아직 닫히지 않았다는 뜻입니다. 로컬 테스트를 직접 실행하지 않았으므로 기존 CI·독립 리뷰 기록을 본 검토의 재현 결과로 간주하지 않습니다.

- **Target** — [PR #269](https://github.com/mols3131d/hmda-data-reliability/pull/269), owning branch의 Inbox.
- **Revision** — base `ea39a4fd6c8f483509cf00a1d1114feb4ef3b686`; reviewed code/head `83a4dbc5d8e115c6437212ddc7cabc5f99a70bdb` (2026-10-26 KST 1차 확인). 이후 Inbox-only commit은 반드시 test blob 변경 여부를 대조합니다.
- **Scope** — 변경 테스트 6파일의 diff, 기존 8파일 전수 목록·하위 검토 보고서, EDA 숫자 oracle 및 실패 경로를 1차 대조했습니다. 생산 코드의 직접 실행과 정본 전 항목 trace는 아직 미완료입니다.

## Findings

현재 직접 확인한 범위에서 **확정된 신규 finding 없음**. 이는 PR 전체의 `clear` 또는 merge readiness 검증 완료를 의미하지 않습니다.

## Perspectives

| Perspective | Reviewer / Method | Focus | Assessment and Evidence |
| --- | --- | --- | --- |
| Oracle 정확성 | 동일 세션 정적 대조 | EDA 4관측값의 quartile 및 null 분포 | `loan_amount` [-100,-20,40,200]의 p25=-40·median=10·p75=80은 손계산과 일치. `tests/hmda_data/eda/test_eda.py` diff |
| 실패·복구 | 동일 세션 반증 점검 | partition INSERT 실패, overwrite pair 복구 | 원래 전체 row/bytes를 직접 비교하고 constraint cause를 분리하는 assertion이 추가됨. `test_ingestion_partition.py`, `eda/test_eda_evidence.py` diff |
| 격리·소유권 | 동일 세션 boundary 대조 | synthetic 원본, 잠금, 분리 경로 | invalid fraction 시 source byte 불변·output 부재 및 lock 실패 시 row 불변 테스트 존재. 제품·공용 파일 변경 없음. PR 변경 경로 목록 |

## Candidate Decisions

| ID | Perspectives | Candidate | Decision | Rationale | Finding |
| --- | --- | --- | --- | --- | --- |
| C1 | Oracle | 분위수 계산이 의도적으로 부정확할 수 있음 | Drop | 입력값의 독립 계산이 추가된 fixed oracle과 일치. 실제 결함 근거 없음 | — |
| C2 | 실패·복구 | 두 번째 evidence replace 실패의 기존 pair 복구가 완전하지 않을 수 있음 | Open | 복구 시나리오가 존재하지만 mock 경로/backup cleanup과 구현은 다음 회차에서 독립 추적 필요 | — |
| C3 | 격리 | partition 롤백 테스트가 단순 fixture 예외를 오인할 수 있음 | Open | `duckdb.ConstraintException` cause와 변경 전후 전체 row 동일성을 확인함. 실제 실행·transaction 구현은 미확인 | — |

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | Diff/path 소유권 정적 대조 | 변경 18파일 중 테스트는 `tests/hmda_data/**` 6개, 나머지 PR 소유 Inbox로 확인. 다른 세 PR와 겹치는 변경 경로 없음 |
| ✅ Pass | EDA 고정 분포 계산 | `test_eda.py`의 숫자 입력과 expected quartile 손계산 대조 |
| ⚪ Not Verified | 정확한 소스·정본 Spec 전수 trace | 기존 [audit report](05-report-hmda-data-audit.md)와 [independent review](06-review-hmda-data-independent.md)의 주장을 대체할 직접 확인 필요 |
| ⚪ Not Verified | pytest/CI 재실행·negative control | PR의 197 passed/CI 증빙은 읽었지만 이 세션에서 실행하지 않음 |

## Risks and Limits

- 차트 HTML의 `var spec =` 파싱은 생성 결과를 검사하지만 renderer 세부에 결합할 가능성이 있습니다. 실제 contract·실패 영향 확인 전에는 finding으로 승격하지 않습니다.
- EDA JSON/Markdown cleanup 및 target schema drift 등 기존 보고서의 known limits를 이 PR의 새 회귀로 분류하지 않습니다.

## Continuation

- **State:** `mols-loops deep`; Prepare → RPI Research/Plan/Work/Review 1차(동일 세션의 순차 관점) 완료, 독립 신규 specialist 게이트 및 완전한 contract trace 미완료. 이 기록은 제품/테스트를 수정한 증거가 아니라 리뷰 checkpoint입니다.
- **Next:** `tests/hmda_data/eda/test_eda_evidence.py`의 replace mock과 `src`의 evidence write 구현, partition staging/transaction 구현을 정본 Spec과 줄 단위 대조. 합성 파일 helper의 path sanitization 반례 및 과거 H1–H8 disposal을 현행 근거로 spot-check.
- **Revalidation trigger:** main/base, head의 test/source/Spec blob, CI 상태, 새로운 feedback이 바뀌면 기존 판단을 stale로 표시하고 영향을 받는 영역을 다시 조사합니다. 전수 파일 수나 이전 에이전트가 표시한 `clear`를 독립 검증으로 대체하지 않습니다.
- **Boundary:** 이 문서는 비정본입니다. 공유 CI/Git fixture와 교차 도메인 계약은 [#277](https://github.com/mols3131d/hmda-data-reliability/pull/277)에서 선행 PR을 취합한 뒤 검증합니다. 승인·merge·thread resolution은 수행하지 않습니다.

## R2 · 2026-10-26 Source and CI Revalidation

- **Research:** main/base `ea39a4fd6c8f483509cf00a1d1114feb4ef3b686` 유지. R1 code head `83a4dbc5d8e115c6437212ddc7cabc5f99a70bdb`부터 현재 head `3cd6f778fc36aea71868f859d1eb971ea74433dd`까지 Inbox review 추가 1건뿐이며 test/source/Spec 변경은 없다.
- **Plan/Review:** 기존 C2는 [evidence writer](https://github.com/mols3131d/hmda-data-reliability/blob/ea39a4fd6c8f483509cf00a1d1114feb4ef3b686/scripts/run_actual_source.py#L91-L159)의 second-replace rollback 및 [test](https://github.com/mols3131d/hmda-data-reliability/blob/83a4dbc5d8e115c6437212ddc7cabc5f99a70bdb/tests/hmda_data/eda/test_eda_evidence.py#L155-L210)에서 create/overwrite byte equality를 확인해 **Drop**. C3는 [transaction](https://github.com/mols3131d/hmda-data-reliability/blob/ea39a4fd6c8f483509cf00a1d1114feb4ef3b686/src/hmda_reliability/hmda_data/ingestion/partition.py#L323-L383)과 [real constraint failure test](https://github.com/mols3131d/hmda-data-reliability/blob/83a4dbc5d8e115c6437212ddc7cabc5f99a70bdb/tests/hmda_data/test_ingestion_partition.py#L237-L271)로 **Drop**. 새 current_required 없음.
- **Open / pre-existing H5 variant (scope_decision):** evidence writer의 첫 JSON replace 실패는 기존 backup을 남길 수 있는데 test는 두 번째 replace 실패만 주입한다. 현재 pair 손상으로 일반화하지 않고, 기존 [H5](05-report-hmda-data-audit.md)와 묶어 첫 replace 실패의 backup cleanup oracle을 #277에 인계한다. Production 변경은 이 PR 범위 밖이다.
- **Validation:** GitHub [CI Lite 40218900666](https://github.com/mols3131d/hmda-data-reliability/actions/runs/40218900666) log에서 **197 passed in 7.89s**, selected Python check 성공 확인. 이번 회차 로컬 pytest/negative control은 **Not Verified**; 별도 독립 specialist 검토도 **Not Verified**. 동일 세션의 source·oracle·ownership·CI 관점 대조는 독립 리뷰가 아니다.
- **Boundary/Next:** 수정 소유권은 이 PR Inbox뿐. 다른 PR 테스트와 경로 중복 없음. #277은 선행 PR 병합 후 동일 main revision에서 교차 도메인·공용 Git fixture를 검증해야 한다. Review gate는 독립 specialist 미실행으로 `blocked`(PR 승인/merge 판단 아님). 이 기록의 reviewed head는 Inbox-only commit 직전 SHA이며 다음 회차에 다시 대조한다.
