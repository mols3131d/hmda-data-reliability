---
type: review
title: PR 271 Current Review and Merge Preparation
description: C6 보완의 새 독립 리뷰, 현재 검증 revision과 CI, C11·공유 hook의 미해결 범위 및 인간의 다음 머지 판단을 기록합니다.
---

# PR 271 Current Review and Merge Preparation

**Assessment: clear. Review readiness: ready.** 수용한 C6의 테스트 보완·실제 반례 검증·새 독립 리뷰와 현재 base/head의 CI를 완료했다. 이 평가는 인간 review에 들어갈 근거가 충족됐다는 뜻이다. PR은 Draft이며 인간의 Ready 전환·review·merge 판단은 남아 있다. C11과 공유 hook의 영구 수정이 완료됐다는 뜻은 아니다.

## Revision And Scope

- **Assessed:** 2026-10-27 KST.
- **Base:** `ea39a4fd6c8f483509cf00a1d1114feb4ef3b686` (`main`).
- **Reviewed delta:** `b285467ad631f6c1055b573b6c8657f46a822a57..dce28291b3dcc0795f01d8e80fadee31fd771b19`.
- **Validated implementation:** `dce28291b3dcc0795f01d8e80fadee31fd771b19`.
- **CI / delivery snapshot:** Head `75efa9949aa6264c1b6dd509b9f677ff01daccca`, prospective merge `961be736cce7398ae883025283bb94896f17418b`. GitHub commit API와 checkout log에서 부모가 위 base와 head임을 확인했다. 이 head의 test/design은 reviewed implementation과 동일하다.
- **Write scope:** [analytics test](../../tests/dbt/test_analytics_foundation.py)와 [design](../../tests/dbt/test_analytics_foundation.design.md), 이 PR의 Inbox 및 PR 본문. Source·Spec·공유 설정·다른 도메인 테스트는 변경하지 않았다.
- **Delivery freshness:** 이 기록의 이후 commit은 Inbox 문서만 전달한다. 최종 전달 후 base/head·Checks·본문·Git 상태를 다시 대조하며, 최종 SHA와 CI 링크는 [현재 PR 본문](https://github.com/mols3131d/hmda-data-reliability/pull/271)에 기록한다. 아래 CI 수치를 이후 head의 직접 실행 결과로 바꿔 읽지 않는다.

기존 전수 감사의 범위·oracle 보강은 [원래 감사 보고서](05-report-current-audit.md)에 보존했다. 이 문서는 [챗봇 후보 수용 판정](09-report-chatbot-review-adoption.md) 이후 C6을 실제로 보완한 현재 평가다. [원래 독립 리뷰](06-review-independent.md)의 C6 기각 판정은 새 반례와 이번 수정·리뷰로 대체됐다.

[챗봇 원문](08-review-chatbot-deep.md)은 기존 판정을 보존하고 중복 빈 줄 세 곳과 이 checkout에 없는 #277 계획의 링크만 정리했다. 링크는 해당 기록이 사용한 고정 revision으로 연결했다.

## Change And Acceptance

[새 guard](../../tests/dbt/test_analytics_foundation.py#L114)는 모든 dbt 결과에서 `pass`·`fail` 이외 status를 거부한다. 기존 CLI exit `1` 요구와 source/staging/mart의 정확한 네 fail descriptor 비교는 유지했다. 구현은 assertion 6줄이며 결과를 성공으로 변환하거나 추가 오류를 무시하지 않는다.

| Scenario | Actual result | Acceptance |
| --- | --- | --- |
| 원래 negative quality scenario | 실제 dbt에서 의도된 네 fail을 확인하고 pytest 통과 | 기존 failure oracle 유지 |
| `test` 직전 임시 mart의 `application_count` column 제거 | build exit `0`, test exit `1`; **13 pass / 4 fail / 1 error** | `Unexpected dbt test statuses`로 추가 not-null node의 `error`를 거부 |

Fault probe는 원래 test 함수와 실제 dbt CLI를 호출하면서 임시 DB에만 `ALTER TABLE marts.mart_hmda_loan_outcomes DROP COLUMN application_count`를 추가했다. 결과 JSON이나 return code를 합성하지 않았다. Coordinator와 adversarial specialist가 서로 별도의 context와 임시 자원으로 이 경로를 확인했다. 이는 정상 fixture의 운영 장애나 전체 mutation coverage를 뜻하지 않는다.

## Independent Review

별도 `review-lead`가 서로 독립된 quality/adversarial specialist의 결과를 계약·diff·source와 대조해 취합했다. **확정된 미해결 `current_required` finding과 이번 bounded gate의 evidence·권한·coverage blocker는 없다.** Reviewed delta는 위에 고정했으며 관찰 head `75efa994`의 추가 변경이 Inbox 두 문서뿐임도 확인했다.

| Reviewer | Independent evidence | Limit |
| --- | --- | --- |
| Quality | 실제 negative pytest **1 passed / 7.60s**. Exit code와 정확한 네 fail 검증이 유지되고 새 guard·design이 일치함을 확인 | 전체 domain·정적 검사·CI를 재실행하지 않음 |
| Adversarial | 실제 dbt fault가 새 guard에 거부됨. Guard AST에서 status 11종을 확인. C11 원본 함수의 shared/exclusive symlink 경로도 직접 재현 | AST 확인은 실제 dbt의 status 11종 실행을 뜻하지 않음. 일반 pytest collection·전체 suite·현재 wrapper·원격 CI는 검증하지 않음 |
| Lead | C6 수용 조건과 두 결과를 취합해 `clear`. C11 source와 공유 hook이 main·baseline·target에서 동일하며 이번 delta가 노출을 넓히지 않음을 확인 | Ready·approval·merge나 공유 Git identity 판정은 포함하지 않음 |

이 문서는 reviewer의 반환 결과를 coordinator가 기록한 것이다. Coordinator의 전체 검증이나 과거 CI를 독립 reviewer가 재실행한 것으로 세지 않는다.

## Remaining Findings And Ownership

| Item | Disposition | Remaining work / merge implication |
| --- | --- | --- |
| C6: 추가 error를 무시하는 negative oracle | **resolved** | 실제 추가 error가 거부되고 정상 negative scenario가 통과했다. 이번 lane의 필수 보완 완료. |
| C11: lock symlink가 manifest를 truncate | **follow_up / independent_requirement** · conditional Major impact | Adversarial도 원본 함수에서 shared/exclusive 모두 `50→0 bytes`를 재현했다. Coordinator의 이전 52-byte probe와 별개 입력이다. 실제 운영의 directory 수정 주체·노출은 미확인이다. Data Platform source owner가 경로 신뢰·기존 regular lock 호환성 정책과 별도 수정·회귀 범위를 결정해야 한다. 이번 테스트 delta의 blocker로 채택하지 않았으며, 수정하려면 별도 `scope_decision`이 필요하다. |
| C4: promotion→consumer composition | **follow_up** · #277 | Result-only drift·기존 current pair 보존 및 선행 domain 변경을 합친 한 revision의 통합 검증. Primitive 성공을 이 근거로 대체하지 않는다. |
| C12: 공유 hook의 영구 격리와 수정 권한 | **follow_up / independent_requirement** · shared owner | [공유 hook 인계](07-report-pre-push-environment.md)를 #277에서 취합하되, 공유 hook·Git fixture 수정의 owning change와 허용 경로를 명시해야 한다. Test-only lane이 전달받았다는 이유로 공유 수정 권한이 생기지 않는다. |
| Git commit identity | **delivery limitation / shared configuration follow_up** | 공유 local config가 `CI Test <ci-test@example.invalid>`로 남아 있어 `dce28291`·`75efa994`에 적용됐다. Global identity와 기존 정상 commit은 `mols`다. 공유 config와 공개 history는 변경하지 않았고, 이후 commit은 검증한 global identity를 명령 한 번의 override로 사용한다. GitHub의 unattributed-change 추가 승인 규칙이 이 두 commit에 적용되는지는 직접 확인하지 못했다. |

C11은 source blob `9efb14181777fe5058605b32ee091d57c8ba2ca8`이 main·baseline·reviewed target에서 동일한 기존 위험이다. 기존 위험이라는 사실로 무해하다고 기각하지 않는다. 이번 변경과의 인과·노출 확대가 없어 후속 source 수정으로 분리한 것이다. #277은 consumer 통합을 취합하며 source 수정 권한을 자동으로 얻지 않는다.

## Validation And Delivery Evidence

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | Owner focused dbt | `uv run --no-sync pytest tests/dbt/test_analytics_foundation.py -q`: **3 passed / 17.22s** |
| ✅ Pass | Owner full domain | `uv run --no-sync pytest tests/data_platform tests/dbt -q`: **43 passed, 1 warning / 21.78s**, skip 없음. 기존 fork DeprecationWarning 1건 |
| ✅ Pass | Owner Python checks | Ruff lint·format, `ty check tests/data_platform tests/dbt` 통과 |
| ✅ Pass | Markdown / artifact validation | Inbox·design Markdown **15개**, YAML required frontmatter **13개**, repository Inbox validator와 whitespace 검사 통과 |
| ✅ Pass | Actual fault / independent review | 위 C6 실제 fault 검출 및 quality·adversarial·lead의 `clear` |
| ✅ Pass | Temporary hook isolation | 새 외부 wrapper가 `git rev-parse --local-env-vars`의 모든 이름을 pytest child에서 제거. Synthetic Git fixture **1 passed / 0.12s**; 실제 wrapper log에서 `GIT_DIR`·`GIT_PREFIX` 제거 확인. Probe 전후 parent HEAD/index 동일 |
| ✅ Pass | Normal pre-push | `pytest --testmon --testmon-forceselect`: **1 passed, 2 deselected / 7.80s**, Python check 통과. Cache 기반 선택을 full suite 통과로 확대하지 않음 |
| ✅ Pass | Prospective-merge CI | [CI Lite 40494379741](https://github.com/mols3131d/hmda-data-reliability/actions/runs/40494379741), merge `961be736`: `FULL_TESTS=false`, `TARGETS=tests/data_platform tests/dbt`, **43 passed, 1 warning / 21.34s**. Scoped Python lint·format·type validation도 성공 |
| ✅ Pass | Git integrity at delivery snapshot | Local/origin head `75efa994` 일치, index·tracked worktree clean, reviewed implementation 이후 test/design diff 없음. Base 대비 source·Spec·공유 hook/config diff 없음 |
| ⚪ Not Verified | Outside current validation | 운영 C11 노출·source 수정, 공유 hook 영구 수정·Git config 복구, 최종 cross-domain 통합, 실제 인간 review·approval·merge |

## Human Decision And Refresh Conditions

2026-10-27 조회에서 GitHub는 Open Draft, `MERGEABLE` / `CLEAN`, CI 성공이며 review·comment는 없다. Main rules는 PR 경유·deletion 및 non-fast-forward 방지이고 required approving review count는 `0`, `require_extra_approval_for_unattributed_changes=true`다. 규칙 조회만으로 실제 추가 승인 적용 여부를 확정하지 않는다. Repository policy의 인간 review·머지 권한은 그대로 적용한다.

인간의 다음 판단은 현재 diff와 이 잔여 위험을 검토해 Ready 전환 및 merge 여부를 결정하는 것이다. C11이나 공유 hook을 이번 PR의 선행 조건으로 선택하면 해당 owner·쓰기 범위·검증을 먼저 승인하고 readiness를 다시 평가해야 한다. Base·test/design·계약·blocking feedback이 바뀌거나 필요한 CI가 실패하면 이 판단을 재사용하지 않는다.
