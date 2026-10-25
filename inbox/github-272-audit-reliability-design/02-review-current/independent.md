---
type: review
title: Reliability Audit Independent Review
description: 독립 quality·adversarial 검토의 revision별 assessment와 필수 수정·재검증을 보존합니다.
---

# Reliability Audit Independent Review

첫 독립 리뷰의 필수 수정 1건을 처리했으며 수정 snapshot의 재검토가 남아 있다.

- **Target:** 변경된 테스트 5개, plan과 현재 감사 근거, 28-file coverage 및 historical finding 판정.
- **Revision:** 최초 `b16ad5734b4a5a35c1db3d12fe03124438e71348` → `a85cac28c38122d87dd4a324f0743d42ccfe94be`.
- **Scope:** `review-lead`가 별도 quality/adversarial specialist를 호출했다. Implementation 담당자의 자체 audit와 구분한다.

## First Assessment

**Assessment:** `changes_required`. 확인된 finding은 1개이며 `current_required / direct_regression`으로 수용했다.

| ID | Severity | Finding | Action |
| --- | --- | --- | --- |
| F1 | Major | 전역 NULL update가 다른 날짜 sentinel을 지워 baseline empty freshness oracle을 약화함 | 선택 partition만 NULL로 바꾸고 focused/domain 및 table-MAX 반례 재검증 |

### F1: Freshness Sentinel Regression

#### Locations

- [test_profile_snapshots.py](../../../tests/reliability/test_profile_snapshots.py)
  - 최초 target의 `test_unmeasurable_profile_reports_unavailable_freshness` setup.

#### Evidence

Adversarial의 메모리 probe에서 정상 SUT는 baseline empty와 target profile 9개를 모두 통과했다. 선택 partition의 MAX가 NULL이면 table MAX를 사용하는 오류는 target 9개를 모두 통과했지만 baseline empty는 다른 날짜의 `2024-01-03T09:00Z`를 차용해 실패했다. Quality도 현재 계약과 주변 safeguard를 대조해 지지했다.

#### Impact

기존 검출력을 보존한다는 acceptance를 위반한다. Production은 정상이며 test fixture 수정으로 해결할 수 있다.

#### Action

NULL update에 `WHERE CAST(partition_at AS DATE) = ?`를 적용해 선택 partition만 바꿨다. 빈 partition과 nonempty all-NULL 모두 다른 날짜의 유효 timestamp를 유지한다. 수정 후 profile 9 passed, domain 268 passed이며 table-MAX mutant는 empty/all-NULL assertion에서 실패했다.

## Reconciled Coverage

Lead는 baseline/target의 28개 목록과 보고서 19/4/5개 행의 일대일 대응, 과거 4개 fix commit의 ancestry와 R1/R2/I1/E1의 기해결, R3/E2 보강 근거를 확인했다. H1/H2/H3는 `follow_up`으로 #277에 남겼다. Hook 환경 오염 복구 후 관련 98개 파일이 지정 commit과 바이트 단위로 같음을 별도로 확인했다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | 독립 두 관점 | Quality/adversarial 별도 호출 후 lead reconciliation. 첫 assessment changes_required 보존 |
| ✅ Pass | F1 정상 재검증 | Profile 9 passed in 0.30s; 전체 Reliability 268 passed in 25.69s |
| ✅ Pass | F1 반례 재검증 | Table-MAX fallback에서 empty/all-NULL assertion FAIL, 7개 PASS |
| ✅ Pass | 수정 후 정적 검사 | Ruff check/format check 및 ty check tests/reliability 통과 |
| ⚪ Not Verified | 수정 snapshot의 독립 assessment | 재검토 후 해당 revision과 결과 추가 예정 |
