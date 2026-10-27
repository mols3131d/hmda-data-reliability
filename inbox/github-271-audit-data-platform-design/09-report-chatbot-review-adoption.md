---
type: report
title: Chatbot Review Adoption Decisions
description: PR 271 챗봇 리뷰의 후보를 구현 담당자가 재현·대조해 선택 수용한 이유와 기각 근거 및 후속 소유권을 정리합니다.
---

# Chatbot Review Adoption Decisions

**채택할 핵심은 C6과 C11이다.** C6은 실제 dbt 실행에서 기존 테스트의 false green을 재현했으므로 **PR #271의 테스트 보완 필요**로 수용한다. C11은 원본 lock 함수가 symlink 대상 manifest를 훼손하는 것을 재현했으므로 **기존 source의 조건부 무결성 위험**으로 수용한다. 두 문제의 수정 소유권은 다르다. 나머지 중 통합·공유 hook의 소유권 경계만 후속 조치로 유지하며, 이미 반박된 의심을 새 결함으로 재등록하지 않는다.

## Basis And Boundary

- **Input:** [챗봇 심층 리뷰](08-review-chatbot-deep.md)의 R14 최종 판정과 R1–R13의 후보·반증 기록. 반복 회차 수나 챗봇의 severity만으로 수용하지 않았다.
- **Revision:** PR head `b285467ad631f6c1055b573b6c8657f46a822a57`, base `ea39a4fd6c8f483509cf00a1d1114feb4ef3b686`. 테스트 코드는 기존 검증 implementation `8bf4e6b095aac7377ac0b22052711c96d929f926`과 동일하다.
- **Assessed:** 2026-10-27 KST.
- **Authority:** 사용자 요청에 따른 구현 담당자의 수용 판정이다. 새로운 독립 리뷰·Ready·approval·merge 판정이 아니며, 이번 repository 산출물은 이 문서 한 개다. Source·test·Spec·공유 설정과 기존 리뷰 문서는 수정하지 않았다.
- **Method:** 현재 source·test·정본 Spec을 읽고, 판단을 바꿀 수 있는 C6/C11만 실제 기존 함수와 임시 DB·파일로 재현했다. 챗봇이 실행한 표준라이브러리 실험이나 과거 CI를 이번 로컬 재현으로 세지 않는다.

## Adoption Matrix

| Chatbot item | Decision | Reason | Owner / next action |
| --- | --- | --- | --- |
| C6: 예상 네 fail 외 추가 error를 무시 | **accepted / current_required** · Minor test-oracle gap | 실제 dbt에서 exit `1`, `fail=4`, `error=1`이 공존하는데 기존 test 함수가 정상 반환했다. R14의 도달성 미확정을 이번 실행으로 해소했다. | #271 테스트 담당: 정확한 네 fail 검증을 유지하면서 추가 error를 거부하는 최소 보완 및 반례 검출 확인. |
| C11: projection lock symlink가 manifest를 truncate | **accepted / source follow_up, scope_decision** · Major impact under stated condition | 원본 `artifact_projection_lock`을 호출했을 때 shared reader와 exclusive writer 모두 manifest가 `52→0 bytes`가 됐다. 실제 운영에서 오염된 lock 경로가 제공되는 조건은 별도다. | Data Platform source owner: lock 경로의 신뢰·기존 파일 호환성 정책 결정과 별도 source 수정. #271 test-only lane으로 source 변경을 흡수하지 않는다. |
| C4: primitive 성공을 promotion→consumer 통합 성공으로 확대할 수 없음 | **accepted as existing follow_up** | Pair identity·flock 테스트는 runner의 candidate 선택·promotion과 Reliability reader를 함께 실행하지 않는다. 새 결함이 아니라 검증 경계다. | #277에서 선행 도메인 변경을 합친 한 revision의 통합 검증. |
| C12: 공유 hook의 영구 수정 소유권·쓰기 범위 미정합 | **accepted in part / ownership clarification** | #277 계획이 공용 수정 인계를 받으면서 exclusive lane은 테스트 중심이다. 전달만으로 실제 hook 수정 권한·완료가 생기지 않는다. | 기존 #270 F3 / [#271 hook 보고서](07-report-pre-push-environment.md)와 중복 집계하지 않고, 공유 수정의 owning change와 허용 경로를 명시. |
| C1/C2/C3/C5/C7/C8/C9/C10의 결함 가설 | **rejected as additional findings** | 고정 산술, 실제 parser·flock, 네 fail의 정확한 descriptor, 임시 artifact 경계와 실제 table/test 실행이 넓은 가설을 반박한다. 더 좁은 C6은 위와 같이 별도로 채택한다. | 같은 테스트·finding을 중복 추가하지 않는다. 아래 기각 근거 참조. |
| C13: 임시 wrapper 또는 녹색 CI로 영구 hook 수정 완료를 판단 | **rejected** | Wrapper는 repository 밖의 실행 경계이며, CI는 local pre-push의 환경 격리를 증명하지 않는다. | 영구 수정·회귀 검증은 여전히 공유 작업의 책임이다. |

## Accepted Evidence

### C6: Reproduced Negative-Test False Green

대상은 [test_analytics_foundation.py](../../tests/dbt/test_analytics_foundation.py)의 `test_dbt_quality_tests_detect_source_staging_and_mart_violations`와 `_run_dbt`, `status == "fail"` 필터다. [Analytics quality tests 계약](../../openspec/specs/data-platform-dbt-analytics/spec.md#requirement-analytics-quality-tests), [mart schema](../../dbt/models/marts/schema.yml), [mart materialization](../../dbt/dbt_project.yml)을 대조했다.

실제 실행 절차는 다음과 같다.

1. 현재 test module을 `importlib`로 읽고 기존 negative-test 함수를 `TemporaryDirectory`의 경로로 직접 호출했다. 함수 자체가 성공 build와 기존 세 가지 DB 오염을 실행했다.
1. 프로세스 안에서만 `_run_dbt`를 감싸 **`test` 호출 직전** 아래 SQL을 임시 DB에 추가했다. 이후 원래 helper가 같은 실제 dbt CLI를 실행하게 했다. Source·YAML·repository test 파일은 바꾸지 않았다.
1. `subprocess.run`의 실제 반환값과 생성된 run-results를 관찰했다. 관찰 wrapper는 반환값을 조작하지 않았다. 호출 종료 후 함수 참조를 복원하고 임시 경로를 제거했다.

```sql
ALTER TABLE marts.mart_hmda_loan_outcomes DROP COLUMN application_count;
```

| Observable | Actual result |
| --- | --- |
| 선행 실제 `dbt build` return code | `0` |
| 실제 `dbt test` return code | `1` — 기존 helper의 예상값과 일치 |
| dbt node status | **13 pass / 4 fail / 1 error** |
| 추가 error node | `test.hmda_reliability.not_null_mart_hmda_loan_outcomes_application_count.0ee1e2f2a1` |
| 기존 test 함수 | **AssertionError 없이 정상 반환** |

이 재현은 결과 JSON에 가짜 `error`를 끼워 넣은 predicate 계산이 아니다. 실제 mart column을 제거해 실제 dbt error를 만들었으며, 네 의도된 fail의 기존 assertion도 통과했다. 선행 build의 성공이나 exit `1` 검사만으로 이 fault를 막지 못한다. 다만 정상 fixture가 현재 추가 error를 만든다는 뜻이나 제품 dbt가 성공 exit를 반환했다는 뜻은 아니다. **테스트가 예상 외 실행 오류를 숨길 수 있다는 한정된 oracle 결함**이다.

따라서 [기존 독립 리뷰](06-review-independent.md)의 “도달 경로가 입증되지 않아 rejected”와 챗봇 R14의 `unknown`은 이 후보에 한해 새 근거로 갱신한다. 최소 수정 방향은 네 fail의 identity 검증을 보존하면서 모든 result의 예상 외 error를 거부하는 것이다. 이 반례가 보완 후 실패하는지와 정상 negative scenario가 통과하는지를 함께 확인해야 한다.

### C11: Original Lock Function Damages the Symlink Target

대상은 [artifacts.py](../../src/hmda_reliability/data_platform/artifacts.py)의 `artifact_projection_lock`이다. `.artifact-promotion.lock`을 `open("w")`로 연 뒤 flock을 얻는다. [Data Platform domain ownership](../../docs/domains/data-platform.md)에 따라 source primitive와 consumer composition을 구분했다.

임시 디렉터리에 52-byte JSON manifest와 고정 run-results를 쓰고, symlink case에만 `.artifact-promotion.lock -> manifest.json`을 만들었다. 이어 **원본 repository 함수**를 호출하고 두 파일의 원문·pair identity를 전후 비교했다.

| Control / fault | Manifest | Run-results | Pair identity / lock |
| --- | --- | --- | --- |
| Regular lock / shared reader | `52→52 bytes`, 보존 | 보존 | identity 동일, body 진입 |
| Symlink lock / shared reader | **`52→0 bytes`** | 보존 | identity 변경, body 진입 |
| Symlink lock / exclusive writer | **`52→0 bytes`** | 보존 | identity 변경, body 진입 |

챗봇의 stdlib-only probe보다 강한 원본 함수 재현 근거가 생겼으므로 위험 자체를 수용한다. 정상 경로의 기존 lock 테스트가 틀렸다는 주장이나 원격 공격·운영 사고가 입증됐다는 주장은 수용하지 않는다. 기존 main에도 있는 source 동작이며, 오염된 경로를 만들거나 전달할 수 있는 주체·실제 배치 환경은 확인하지 않았다.

Source owner가 허용 경로·symlink 처리·기존 regular lock 호환성을 결정한 뒤, 원본 함수 호출 전후 보호 대상 bytes의 불변을 확인하는 회귀 테스트와 수정 범위를 정해야 한다. “read-only reader니까 무해하다”는 판단은 이번 재현과 맞지 않는다. #277은 같은 root cause의 consumer 통합만 소유하며 source 수정 권한을 자동으로 얻지 않는다.

## Rejected Or Deferred Claims

| Candidate | Reason for non-adoption as a new defect |
| --- | --- |
| C1: approval·numeric NULL 기대값이 틀림 | Spec의 action `1/2`, 반올림 및 non-null 평균에 따라 TX의 `2/3→0.666667`, `150000/75`는 맞다. |
| C2/C10: SQL 테스트가 escape 식 또는 문자열 형태만 복제 | [SQL test](../../tests/data_platform/test_sql.py)는 실제 DuckDB parser의 column name·원문 값과 결과 row를 비교한다. |
| C3: quality test가 단순 exit code만 확인 | 실제 source/staging/mart 네 fail descriptor를 비교한다. 넓은 주장은 기각하되 추가 error 누락인 C6은 구분한다. |
| C5: artifact lock 검증이 fake lock뿐임 | [Lock test](../../tests/data_platform/test_artifacts.py)는 원래 `fcntl.flock`을 호출하고 contender에만 `LOCK_NB`를 더해 관찰한다. |
| C7: 이전 성공 artifact만 남아도 통과 | 이전 build의 성공 결과만으로 네 fail descriptor 집합을 충족할 수 없다. |
| C8: 네 expected fail이 모든 test node를 포괄 | 이번 실제 dbt test는 18개 node를 실행했다. 네 fail 외 node가 있으며 C6도 그중 하나다. |
| C9: dbt test가 mart를 재생성해 column fault를 없앰 | 실제 `test` 실행에서 추가 column error가 남았으므로 이번 반례에서는 성립하지 않는다. |
| 새로운 specialist가 없으면 과거 독립 리뷰 전체를 무효화해야 함 | 동일한 코드에 대한 과거 실행·리뷰는 역사적 근거다. 새 근거가 바꾸는 C6 판정과 그 영향을 갱신하며, 새 독립 리뷰를 수행했다고 주장하지 않는다. |
| C4/C12를 #271의 즉시 source·공유 설정 수정 요구로 확대 | [#271 계획](00-plan-data-platform-tests.md)과 [#277 계획](https://github.com/mols3131d/hmda-data-reliability/blob/74ac659d084fadd5e93900b132ef5b995ef8d919/inbox/github-277-audit-cross-domain-design/00-plan-cross-domain-tests.md)의 쓰기 경계를 넘어선다. 후속 소유권 확인은 채택하되 이번 문서 작업의 구현 범위로 삼지 않는다. |

## Validation And Remaining Work

아래의 재현 성공은 문제를 확인했다는 뜻이며, 결함이 수정됐다는 뜻이 아니다. 실행 환경은 이 PR worktree의 기존 `.venv`, dbt-core `1.12.3`, dbt-duckdb `1.11.0`, DuckDB `1.5.5`다.

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | C6 원본 함수 + 실제 dbt fault 재현 | `uv run --no-sync python`에서 기존 negative-test 함수를 직접 호출. 선행 build `0`, test `1`, `13 pass / 4 fail / 1 error`와 함수 정상 반환 관측. Pytest collection/plugin을 포함한 suite 실행은 아니다. |
| ✅ Pass | C11 원본 primitive fault 및 대조군 | `uv run --no-sync python`에서 정상 shared 1회와 symlink shared/exclusive 2회 직접 호출. 위 bytes·identity 관측. 모든 대상은 임시 디렉터리 내부다. |
| ✅ Pass | 현재 코드·계약·후보 비교 | b285467a의 챗봇 기록, source·test·Spec과 쓰기 경계 대조. |
| ✅ Pass | 문서 검증·변경 경계 | `rumdl fmt/check`, repository Inbox validator, YAML required frontmatter 검사, 새 파일 whitespace 검사 통과. HEAD·index와 기존 tracked 파일은 그대로이며 이 문서 한 개만 추가했다. |
| ⚪ Not Verified | 수정 후 회귀·새 독립 리뷰·readiness 재판정 | 이번 요청은 수용 판단과 문서 작성이다. 코드 수정·새 회귀 suite·독립 specialist 검토를 수행하지 않았다. |
| ⚪ Not Verified | 운영 경로에서 C11 발생 가능성·영구 hook 수정·#277 통합 | 별도 source/공유 작업 소유자의 검증 및 권한 결정이 필요하다. |

다음 구현에서 먼저 다룰 항목은 **C6의 작은 test-only 보완**이다. C11은 source owner의 정책·수정 작업으로, C4와 공유 hook은 기존 통합·공유 작업으로 남긴다. [이전 ready 보고서](05-report-current-audit.md)와 독립 `clear`를 이 새 C6 재현을 처리한 결과로 해석하지 않는다. C6 보완·검증과 영향을 받는 독립 리뷰를 갱신한 뒤에만 현재 readiness를 다시 판정한다.
