---
type: review
title: Reliability Audit Independent Review
description: 독립 quality·adversarial 검토의 revision별 assessment와 필수 수정·재검증을 보존합니다.
---

# Reliability Audit Independent Review

최초 `a85cac28`의 필수 수정 1건을 처리한 `e772c53f`와 C11을 보강한 `43321757`의 독립 재검토는 모두 `clear`다. 남은 `current_required`나 review blocker는 없다.

- **Target:** 변경된 테스트 5개, plan과 현재 감사 근거, 28-file coverage 및 historical finding 판정.
- **Revision:** 최초 `b16ad5734b4a5a35c1db3d12fe03124438e71348` → `a85cac28c38122d87dd4a324f0743d42ccfe94be`.
- **Scope:** `review-lead`가 별도 quality/adversarial specialist를 호출했다. Implementation 담당자의 자체 audit와 구분한다.

## First Assessment

**Assessment:** `changes_required`. 확인된 finding은 1개이며 `current_required / direct_regression`으로 수용했다.

아래 Major severity는 artifact 전달을 위한 완료 담당자의 분류다. Reviewer가 직접 부여한 label은 위 disposition과 scope relation이다.

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

## Second Assessment

- **Reviewed:** `e772c53fb975232e776d240cb61ff9a13cb896d1` vs `a85cac28c38122d87dd4a324f0743d42ccfe94be`의 F1 보정과 관련 Inbox delta.
- **Assessment:** `clear`. Quality·adversarial 모두 새 material finding이 없고 F1 closure를 지지했다. 변경 없는 최초 검토 범위는 재사용했다.
- **Evidence:** 선택 partition만 UPDATE하므로 empty/all-NULL 사례 모두 다른 partition의 timestamp를 보존하고 table-MAX 오류를 `None` assertion에서 검출한다. 정확한 HEAD·clean 상태·수정 범위와 oracle 경로를 정적으로 확인했다.
- **Limits:** Reviewer는 담당자가 보고한 profile/domain GREEN, 열 가지 기존 control과 F1 보정 control, 정적 검사를 다시 실행하지 않았다. 이 결과는 보고된 실행 근거와 별도의 독립 정적 검토다. H1–H4는 #277 후속 범위이며 인간의 Ready/approval/merge 승인은 아니다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | 독립 두 관점 | Quality/adversarial 별도 호출 후 lead reconciliation. 첫 assessment changes_required 보존 |
| ✅ Pass | F1 정상 재검증 | Profile 9 passed in 0.30s; 전체 Reliability 268 passed in 25.69s |
| ✅ Pass | F1 반례 재검증 | Table-MAX fallback에서 empty/all-NULL assertion FAIL, 7개 PASS |
| ✅ Pass | 수정 후 정적 검사 | Ruff check/format check 및 ty check tests/reliability 통과 |
| ✅ Pass | 수정 snapshot의 독립 assessment | `e772c53f`에서 두 관점과 lead reconciliation 모두 clear |

## Third Assessment

- **Reviewed:** `43321757d8fed9aeebcd0f2a56279acc253dbdfd` vs `9d2ab6eb15efab03bba4813da299bbe04ffac018`. Profile 테스트 28행 추가이며 변경 없는 기존 전수 검토 범위는 재사용했다.
- **Assessment:** `clear`. 별도 quality/adversarial specialist와 lead가 C11을 `accepted / fixed`로 판정했다. 새 `current_required`·blocker는 없다.
- **Evidence:** 실제 UPDATE·INSERT로 행이 바뀐 것을 먼저 관찰하고 schema hash 불변을 검사한다. 정본의 schema-only 계약과 일치하며 기존 DDL 3개 및 F1 freshness sentinel을 보존한다. 정확한 HEAD·clean 상태·변경 경계·contract/oracle·diff check를 확인했다.
- **Validation limits:** Reviewer는 보고된 profile 11/domain 270 GREEN과 두 negative control을 재실행하지 않았다. 별도 독립 정적 검토와 담당자의 실행 근거를 구분한다. 최종 Inbox 갱신·원격 CI·merge 상태 확인은 완료 담당자가 수행한다.
- **Follow-up:** C9/H1/H2의 계약·Spec 결정, H3 통합, H4 공용 hook 문제는 현재 테스트 변경의 필수 수정이 아니다. C16은 기존 reporter의 표현 무결성 후속 과제이며 UI 표시 결과는 미확인이다. 과거의 “H1–H4 모두 #277” 배정은 [현재 소유권 정정](README.md#pr-277-handoff)으로 대체한다.
