---
type: report
title: HMDA Data Test Audit and Delivery Evidence
description: PR 269의 현행 전수 inventory, 과거 finding 재판정, 회귀 보호와 검증 및 후속 인계를 기록합니다.
---

# HMDA Data Test Audit and Delivery Evidence

**State:** tracked 8파일 전수 검토와 회귀 테스트 보강을 완료했고, 최종 도메인 suite는 197개 통과했다. 독립 리뷰는 `clear`이고 기록한 원격 CI checkpoint도 통과했다. 기술 산출물은 인간 검토에 전달할 수 있으며 Draft와 인간 lifecycle gate를 유지한다. Production 후속 항목은 아래 별도로 남긴다.

## Revision And Scope

- **Main baseline:** `ea39a4fd6c8f483509cf00a1d1114feb4ef3b686`, 2026-10-25 live branch API 및 fetch 확인.
- **Inherited PR head:** `69afeef8b93eb348410b13eff3705cf302ef3983`.
- **Audit head:** `150d565a6be06bc71ca0c446ad26e8143523d780`, 위 head에 최신 main을 merge했다. 최초 base `81fe44b2` 이후 main의 HMDA Data source/test/Spec 변경은 없다.
- **Implementation candidate:** `637cdbd05640d859cff6eaf33866924c204f82ff`, 독립 리뷰를 고정한 테스트·하위 영역 보고서 commit이다.
- **Writable scope:** HMDA Data authored tests와 이 PR 소유 Inbox. Production, OpenSpec, 공유 설정과 타 도메인 수정은 포함하지 않는다.

## Current File Inventory

`git ls-tree -r --name-only ea39a4fd6c8f483509cf00a1d1114feb4ef3b686 tests/hmda_data`로 확정한 8개 tracked 파일이다. 추가 fixture/sample/design 파일은 없으며 과거 PR #258 inventory를 현행 전수 검토 근거로 사용하지 않았다. 테스트가 새로 추가되면 최종 diff와 함께 이 목록을 다시 대조한다.

| File | Review status | Evidence and disposition |
| --- | --- | --- |
| [conftest.py](../../tests/hmda_data/conftest.py) | reviewed | 정상 CSV/Parquet의 고정 행, 4가지 format 조합의 누락 schema, 실제 NULL 값 fixture를 확인했다. `tmp_path`와 독립 in-memory DuckDB로 격리되며 oracle을 production 계산에서 생성하지 않는다. 변경 불필요. |
| [__init__.py](../../tests/hmda_data/__init__.py) | reviewed / excluded from edits | package docstring만 존재한다. 실행·fixture 계약이 없어 추가 테스트 대상에서 제외한다. |
| [test_ingestion.py](../../tests/hmda_data/test_ingestion.py) | reviewed | [Ingestion review](02-review-ingestion.md) |
| [test_ingestion_partition.py](../../tests/hmda_data/test_ingestion_partition.py) | reviewed | [Ingestion review](02-review-ingestion.md) |
| [test_eda.py](../../tests/hmda_data/eda/test_eda.py) | reviewed | [EDA review](03-review-eda.md) |
| [test_eda_evidence.py](../../tests/hmda_data/eda/test_eda_evidence.py) | reviewed | [EDA review](03-review-eda.md) |
| [test_eda_explorer.py](../../tests/hmda_data/eda/test_eda_explorer.py) | reviewed | [EDA review](03-review-eda.md) |
| [test_synthetic.py](../../tests/hmda_data/test_synthetic.py) | reviewed | [Synthetic review](04-review-synthetic.md) |

### Contracts And Support

[contracts/__init__.py](../../src/hmda_reliability/hmda_data/contracts/__init__.py)는 여전히 docstring만 있는 placeholder다. 독립 executable contract가 없으므로 별도 test module 부재를 결함으로 세지 않는다. 실제 required-column, identity/freshness, EDA와 synthetic 계약은 각 owning API와 canonical Spec을 대조한다.

[errors.py](../../src/hmda_reliability/hmda_data/errors.py)의 load/validation/stale/synthetic exception은 각 API의 실패 시나리오에서 검증한다. 예외 class 상속만 반복하는 테스트는 추가하지 않는다. [공개 facade](../../src/hmda_reliability/hmda_data/__init__.py)의 호출 surface와 각 domain API의 소유권도 확인했다.

## Historical Finding Disposition

원본 보고서는 [historical bundle](01-review-historical/README.md)로 보존한다. 판정은 현재 source와 테스트에서 다시 내렸으며, 테스트 gap과 기존 production 문제를 구분한다.

| ID | Disposition | Current evidence and action |
| --- | --- | --- |
| H1 | obsolete | synthetic 원본 경로 중첩·alias 거부와 source bytes 보존은 이미 구현·회귀 보호되어 중복 수정하지 않았다. [Synthetic](04-review-synthetic.md) |
| H2 | obsolete | 각 파일의 필수 컬럼 검증과 format/order matrix가 이미 있다. [Ingestion](02-review-ingestion.md) |
| H3 | accepted | 실제 UNIQUE index INSERT 실패 뒤 기존 행·provenance 보존과 staging 정리를 확인하는 rollback 회귀를 추가했다. [Ingestion](02-review-ingestion.md) |
| H4 | accepted | 같은 연도 두 파일 중 선택한 파일만 갱신하고 sibling 전체 행이 동일함을 확인한다. [Ingestion](02-review-ingestion.md) |
| H5 | accepted | 기존 EDA backup cleanup 실패의 JSON/Markdown 불일치를 재현했다. 소유 범위 밖인 production 수정은 #277에 인계한다. [EDA](03-review-eda.md) |
| H6 | accepted | 음수·NULL·비대칭 값의 non_null_count/min/p25/median/p75/max를 두 숫자 컬럼 모두 독립 고정값으로 비교한다. [EDA](03-review-eda.md) |
| H7 | accepted | symlink로 연 실제 file DB에서 canonical lock 획득 실패가 full/partition mutation을 막는지 검증한다. [Ingestion](02-review-ingestion.md) |
| H8 | accepted | 희소 연도의 유지, 최소 1행 및 전체 정렬 결정성을 작은 고정 입력으로 직접 검증한다. [Synthetic](04-review-synthetic.md) |

## Regression Protection

기존 **154 → 197** 실행 case로 늘었다. 최종 영역별 실행 결과는 ingestion 49, EDA 34, synthetic 114개다. 새 입력 조합뿐 아니라 기존 assertion도 전체 행 보존, 정확한 통계와 projection 내용 비교로 강화했다. Fixture와 package support는 변경하지 않았다.

하위 영역 리뷰에 새 oracle과 transient negative-control 결과를 남겼다. Transaction 누락, year 전체 삭제, loader의 잘못된 DB lock 경로, schema 검증 우회, 분위수 오류·음수 clipping·NULL count와 sparse-year partition 제거가 실제 assertion에서 검출됨을 확인했다. 이는 선택된 regression의 검출력 근거이며 exhaustive mutation score가 아니다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | isolated locked environment | 전용 worktree에서 `uv sync --locked`, dependency 파일 변경 없음 |
| ✅ Pass | baseline domain suite | clean audit head `150d565a`에서 `uv run --no-sync pytest tests/hmda_data -q`: **154 passed in 13.20s** |
| ✅ Pass | final domain suite | `uv run --no-sync pytest tests/hmda_data -q`: **197 passed in 16.74s** |
| ✅ Pass | static checks | `uv run --no-sync ruff check tests/hmda_data`, `ruff format --check tests/hmda_data` (8 files), `ty check tests/hmda_data`, `git diff --check` |
| ✅ Pass | final synthetic assertions | 최종 no-output assertion 2개는 수정 뒤 별도 실행에서도 **2 passed in 1.01s** |
| ✅ Pass | remote CI checkpoint | [CI Lite 40206081091](https://github.com/mols3131d/hmda-data-reliability/actions/runs/40206081091), merge `c81633ff`: **197 passed in 6.35s**, domain Ruff/format/ty 통과 |
| ✅ Pass | CI selection | changed path classifier: `targets=tests/hmda_data`, `type_targets=tests/hmda_data`, `full_tests=false` |
| ✅ Pass | independent two-perspective review | `637cdbd0`의 실제 review-quality/review-adversarial 검토 완료. 테스트 결함 없음, H6 설명의 `mean` 과장 1건을 정정했다. [정정의 targeted 확인](06-review-hmda-data-independent.md)까지 `clear`로 종료했다. |
| ❌ Fail | initial native pre-push environment | Git hook의 `GIT_DIR` 상속으로 임시 Git fixture가 owning HEAD/index를 바꿨다. **11 failed, 1113 passed, 3 skipped in 319.09s**; 뒤늦은 전체 경로 오분류로 tombi 미설치 오류도 발생했다. Push는 전송 전에 중단됐다. |
| ✅ Pass | clean Git-fixture scope | Git hook 밖 정상 환경에서 `uv run --no-sync pytest tests/scripts/ci -q`: **232 passed, 1 skipped in 25.16s** |
| ✅ Pass | isolated native hook retry | 기존 hook의 모든 선택 검사를 그대로 실행해 **11 passed, 142 deselected in 3.00s**, Python 6파일 lint/format 통과 후 push 성공. testmon이 선택하지 않은 전체 suite를 재실행한 결과로 주장하지 않는다. |
| ✅ Pass | Git isolation root cause | 두 임시 저장소만 쓰는 probe에서 inherited `GIT_DIR`가 fixture commit을 owning repository로 보내는 현상을 재현했다. 실제 후보는 복구 후 clean `637cdbd0` 및 전체 tracked blob 일치를 확인했다. |

## Follow-up And Handoff

[PR #277](https://github.com/mols3131d/hmda-data-reliability/pull/277)의 후속 담당자는 아래 재현과 제안 oracle을 먼저 읽는다. 이 PR에서 해당 production/Spec 파일을 수정하거나 known failure를 통과 조건으로 고정하지 않았다.

| Item | Classification | Impact and next action |
| --- | --- | --- |
| H5 | production defect / deferred | backup 정리 실패 시 JSON은 이전 분석, Markdown은 새 분석이 될 수 있다. [EDA의 재현·pair oracle](03-review-eda.md)을 기준으로 overwrite commit과 cleanup 경계를 수정하고 fault regression을 추가한다. |
| S1 | production defect / follow_up | 이미 VARCHAR인 `loan_amount`에 schema drift를 적용하면 physical type이 바뀌지 않는데 성공한다. [Synthetic의 유효 Parquet 재현](04-review-synthetic.md)을 기준으로 입력 type 처리와 type-change oracle을 결정한다. |
| E1 | environment failure / shared tooling follow_up | Git hook의 repository-local Git 환경이 CI test fixture로 전파된다. 아래 재현과 격리 방식을 기준으로 #277에서 공용 실행 경계를 수정한다. |
| S2 | spec gap / follow_up | `activity_year` target 금지 requirement와 `target_year` 동시 지정 scenario의 범위가 다르다. [Synthetic의 분기·재현](04-review-synthetic.md)을 읽고 Spec/source 정합을 먼저 결정한다. |

PR #269의 suite 성공은 위 결함 해결, 제품 acceptance 또는 도메인 간 통합 검증을 뜻하지 않는다. #277의 실제 접점 검증은 선행 PR이 main에 반영된 뒤 수행하며, 인간 review·Ready 전환·approval·merge는 별도 gate다.

### Git Hook Environment Isolation

초기 push의 native pre-push가 새 testmon cache에서 전체 suite를 실행했다. Hook이 넘긴 `GIT_DIR`를 Git fixture가 그대로 상속해 임시 directory의 `git init`·`git commit`이 이 worktree의 HEAD/index를 변경했다. 검토 기준 객체는 보존되어 있었고 remote push는 실패했다. 변경 직전의 known candidate `637cdbd0`으로 own local ref를 expected-old 조건과 함께 복구하고 index만 재구성했다. 이후 `git status --short`가 비었고 모든 tracked working blob이 candidate와 일치했다. 이 과정에서 production/test 파일을 수정하지 않았다.

별도 root-cause probe는 두 `TemporaryDirectory` 하위 저장소 A/B만 사용했다. A의 empty commit을 만든 다음 `GIT_DIR=A/.git`인 환경에서 B의 `git init`과 empty commit을 실행하자 A의 HEAD가 바뀌었다. 상속된 repository-local Git 환경이 원인이라는 직접 재현이며 실제 worktree를 다시 훼손하는 실험은 하지 않았다.

재시도는 disposable pre-push wrapper가 `git rev-parse --local-env-vars`에 해당하는 변수만 제거한 뒤 **기존 hook을 그대로 exec**하도록 구성한다. 검사를 생략하거나 공용 hook/config를 수정하지 않는다. CI test fixture의 subprocess 환경 격리 또는 hook의 Git environment 정리가 필요한 영구 수정은 #277로 넘긴다. 초기 실패를 전체 suite 성공으로 바꾸어 기록하지 않으며, 재시도 결과는 별도로 기록한다.

## Delivery And Next Action

- **Verified checkpoint base:** `ea39a4fd6c8f483509cf00a1d1114feb4ef3b686`.
- **Verified checkpoint head:** `5dde7f291cba1b954b0d1b5c1561abc55eb33c5b`.
- **Prospective merge:** `c81633ffb7d00c8f7cf1f7cad93f10f3e0d670bd`; GitHub commit parents와 CI checkout log가 위 base/head와 일치한다.
- **Observed CI scope:** `TARGETS=tests/hmda_data`, `TYPE_TARGETS=tests/hmda_data`, `FULL_TESTS=false`. Domain 197개와 선택 Python 검사가 실제 실행됐다. Markdown/OpenSpec/build/Tach 등 skipped step을 검증 성공으로 확대하지 않는다. Inbox 12개 문서는 별도 local rumdl·native Inbox validator·parsed YAML 필수 scalar 검사로 확인했다.
- **Evidence applicability:** 독립 review의 code candidate `637cdbd0`에서 위 checkpoint까지는 이 PR의 문서 3개만 바뀌었다. 이 checkpoint 기록을 추가한 마지막 commit도 plan/report 문서만 변경한다. 테스트·source·Spec·공유 설정이 동일함을 diff로 확인하고 최종 PR head/checks는 [PR #269](https://github.com/mols3131d/hmda-data-reliability/pull/269) 본문에서 다시 고정한다.
- **Review readiness:** 기술 검토와 도메인 검증은 준비됐으나 인간 review 완료를 대신하지 않는다. Ready 전환·approval·merge는 수행하지 않았다. 인간 reviewer는 [독립 검토](06-review-hmda-data-independent.md)와 위 후속 4개 항목을 먼저 보고 이 test 보강의 채택 여부를 판단한다.
- **Continuation:** #277 담당자는 H5/S1/S2/E1의 위치·재현·권장 oracle을 하위 영역 리뷰 및 이 보고서에서 읽고, 선행 PR이 main에 반영된 뒤 실제 writer 간 lock lifetime과 cross-domain 접점을 검증한다. Default hook은 영구 수정 전까지 같은 Git environment 누수가 재발할 수 있으므로 재사용 시 disposable wrapper를 다시 구성해야 한다.
