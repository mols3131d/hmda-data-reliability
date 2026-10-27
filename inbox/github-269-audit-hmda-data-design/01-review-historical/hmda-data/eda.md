---
type: review
title: HMDA EDA Test Design Review
description: EDA 지표·portable evidence·실행 진입점과 JSON/Markdown 쌍의 실패 경계 테스트를 검토합니다.
---

> [!WARNING]
> **Historical evidence only:** PR #258 / `bdce0f4e`에서 가져온 과거 판단입니다. 이 PR에서 최신 main·Spec·source·tests로 재검증하고 채택 여부를 결정하기 전에는 현행 결함이나 완료 상태로 해석하지 않습니다.

# HMDA EDA Test Design Review

> [!NOTE]
> 관찰 지표와 portable provenance는 구체적으로 검사한다. 기존 증거 쌍의 갱신 후 cleanup 실패를 놓친다.

- **Target**: HMDA Data EDA와 actual-source evidence writer.
- **Revision**: `3ab899100fc0b35e23d464bd761f3b144a978ae7`.
- **Scope**: [test_eda.py](../../../../tests/hmda_data/eda/test_eda.py), [test_eda_evidence.py](../../../../tests/hmda_data/eda/test_eda_evidence.py), [test_eda_explorer.py](../../../../tests/hmda_data/eda/test_eda_explorer.py)와 관련 구현·계약.

## Findings

| ID | Severity | Finding | Action |
| --- | --- | --- | --- |
| F1 | Minor | 두 replace 후 backup cleanup 실패가 JSON old / Markdown new 불일치를 만들지만 현재 test가 놓친다 | 기존 pair 갱신의 cleanup 장애 회귀 추가 |
| F2 | Minor | numeric summary의 분위수·음수 값 oracle이 약하다 | 비대칭·음수·NULL fixture의 전체 summary 비교 |

## Design Assessment

| Area | Independent Oracle And Strength | Boundary |
| --- | --- | --- |
| EDA metrics | fixture의 고정 row/null/grain 값과 invalid input 검사 | 실제 CSV와 DuckDB, descriptive analysis |
| Evidence | JSON의 exact provenance와 Markdown의 고정 수치, machine-specific 경로 부재 | writer와 file serialization을 실제 실행 |
| Revision | 독립 임시 Git 저장소의 clean HEAD, staged/unstaged/untracked 거부 | 현재 저장소 clean 여부를 가정하지 않음 |
| CLI/explorer | main의 source·resource limits·metadata 전달, explorer 진입 wiring | heavy analysis의 일부는 대체하며 전체 실제 원천 실행을 증명하지 않음 |
| Atomicity | 최초 생성 중 두 번째 replace 실패 시 신규 JSON·Markdown 부재 | 기존 pair와 commit 후 cleanup은 별도 분기 |

### F1 — Minor: Evidence Pair Cleanup Boundary

#### Locations: F1

- [test_eda_evidence.py](../../../../tests/hmda_data/eda/test_eda_evidence.py)
  - `test_write_evidence_cleans_up_new_json_on_first_creation_second_replace_failure`.
- [run_actual_source.py](../../../../scripts/run_actual_source.py)
  - `write_evidence`: 두 replace와 backup unlink를 같은 rollback 분기로 처리한다.

#### Evidence: F1

기존 pair를 100행으로 만들고 200행으로 갱신할 때 backup unlink만 실패시키면 JSON은 100행, Markdown은 200행으로 남는다. Caller의 [A3 재현](https://github.com/mols3131d/hmda-data-reliability/blob/bdce0f4e8e871b1301bac8f8ab3a37c7ba50bd91/inbox/github-258-cover-sdk-retry-classification/03-review-domain-test-design/validation.md#a3-eda-evidence-pair-cleanup)으로 확인했다. 최초 생성 시 두 번째 replace 실패라는 기존 보호는 유효하지만 이 후속 cleanup 분기를 검사하지 않는다.

#### Impact: F1

같은 observation의 정본·요약이 서로 다른 수치를 보여준다. 실패를 반환했다는 사실만으로 증거 쌍의 일관성이 유지되지는 않는다.

#### Action: F1

기존 pair의 overwrite를 기준으로 replace 실패와 committed cleanup 실패를 구분하고, 최종 두 파일이 모두 old 또는 모두 new인지 검사한다. Cleanup 예외가 이미 게시된 새 pair의 한쪽만 되돌리지 않도록 후속 구현을 검토한다. 이번 보고에서는 source를 수정하지 않았다.

### F2 — Minor: Numeric Summary Oracle

#### Locations: F2

- [test_eda.py](../../../../tests/hmda_data/eda/test_eda.py)
  - 115행은 양수 income의 count/min/median/max 중심이다.
  - 147행의 음수 fixture는 `anomalies` key 부재를 검사한다.

#### Evidence: F2

p25/p75가 뒤바뀌거나 `NULL`이 되고 음수를 clipping해도 현재 해당 assertion은 이를 구별하지 못할 수 있다. 현재 구현 오류로 재현한 결과는 아니다. 두 numeric field에 서로 구분되는 음수·NULL·비대칭 값을 넣고 독립적으로 정한 전체 summary를 비교하면 이 공백을 좁힐 수 있다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | 독립 정적 검토 | Batch A 양쪽 관점의 세 test body·writer·계약 대조 |
| ✅ Pass | 현재 suite 실행 | [실행 근거](https://github.com/mols3131d/hmda-data-reliability/blob/bdce0f4e8e871b1301bac8f8ab3a37c7ba50bd91/inbox/github-258-cover-sdk-retry-classification/03-review-domain-test-design/validation.md#test-execution) |
| ❌ Fail | 기존 pair cleanup probe | JSON 100 / Markdown 200 불일치 |
| ⚪ Not Verified | 실제 전체 HMDA 원천 재분석 | 이번 리뷰는 fixture 기반 테스트와 evidence 경계를 검토 |
