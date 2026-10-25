---
type: report
title: Data Platform Current Test Audit and Handoff
description: PR 271의 현행 전수 검토 범위, legacy finding 수용, 회귀 보강과 검증 및 다음 판단을 확인합니다.
---

# Data Platform Current Test Audit and Handoff

**State:** 현행 테스트 5개 파일 전수 검토와 회귀 보강, 로컬 검증, 독립 리뷰(`clear`), 안전한 push와 prospective-merge CI 확인을 완료했습니다. 아래 exact base/head 기준 **review readiness: ready**입니다. PR은 Draft이며 인간 review·Ready 전환·approval·merge는 별도입니다.

## Revision And Scope

- **Owner:** PR #271, `agent/test/audit-data-platform-design`, 이 PR 소유 Inbox 경로.
- **Base:** `ea39a4fd6c8f483509cf00a1d1114feb4ef3b686` (`main`, 2026-10-26 조회).
- **Inherited head:** `f1cf36e5baf74f356333c7a7ff70240287e27c55`.
- **Integration anchor:** `4f2bebb4d5a5a6e64336e5df3c9c11b5da65f4ae` (현재 main additive merge). 이후 테스트·Inbox 변경은 이 commit 위에서 검증합니다.
- **Validated implementation:** `8bf4e6b095aac7377ac0b22052711c96d929f926`. 모든 테스트 변경과 신규 design을 포함하며 이후 Inbox-only commit은 이 코드 검증을 변경하지 않습니다.
- **Readiness / CI snapshot:** Head `37c53d04b0646bdbc0cb1341f54e0f87aafcd0ad`, prospective merge `d2367583965655a33e9e2f9a7cfd797da8501c56`; 부모는 위 base와 head임을 GitHub commit API 및 checkout log로 확인했습니다. 이후 이 결과를 기록하는 Inbox-only commit은 같은 tests/design를 유지합니다.
- **In scope:** [plan](00-plan-data-platform-tests.md)의 exclusive test lane과 현행 source·Spec 대조. 제품 코드, Spec, 공유 설정과 다른 도메인 테스트는 검토만 합니다.

## Inventory And Review Coverage

`git ls-files tests/data_platform tests/dbt`로 baseline 추적 파일 5개를 재확인했습니다. 각 행은 리뷰 대상이며 수정 허용 여부는 별도로 표시합니다.

| File | Responsibility | Write | Review evidence |
| --- | --- | --- | --- |
| [test_duckdb.py](../../tests/data_platform/test_duckdb.py) | Connection, metadata, mutation lock | Yes | [Primitive review](02-review-primitives.md) |
| [test_sql.py](../../tests/data_platform/test_sql.py) | Identifier / literal quoting | Yes | [Primitive review](02-review-primitives.md) |
| [test_artifacts.py](../../tests/data_platform/test_artifacts.py) | Pair bytes / identity, projection lock | Yes | [Artifact review](04-review-artifacts.md) |
| [test_analytics_foundation.py](../../tests/dbt/test_analytics_foundation.py) | Profile, Bronze→staging→mart, artifact / lineage | Yes | [dbt review](03-review-dbt.md) |
| [__init__.py](../../tests/data_platform/__init__.py) | Package support | No | [Primitive review](02-review-primitives.md) |

Baseline에 별도 helper·fixture·design 파일은 없습니다. 이번에 추가한 [analytics design map](../../tests/dbt/test_analytics_foundation.design.md)은 dbt의 여러 계약과 고정 oracle의 연결을 설명하며 [dbt review](03-review-dbt.md)의 추가 검토 대상으로 포함했습니다. 따라서 현재 변경의 authored test/support/design coverage는 baseline 5개와 신규 design 1개입니다.

## Legacy Adoption

| Candidate | Disposition | Current evidence / action |
| --- | --- | --- |
| Historical P1: metric branch oracle | accepted → resolved | TX 세 행의 action `1/2/4`, approvals `2`, rate `0.666667`, non-null 평균 `150000.0/75.0`을 손계산한 tuple과 비교합니다. Action 2 누락, 반올림 제거, numeric NULL의 zero 대체 mutant를 모두 검출했습니다. [dbt review](03-review-dbt.md). |
| Historical read-only write rejection limit | accepted → resolved | 실제 INSERT 거부와 재접속 후 원래 row 보존을 확인합니다. [Primitive review F1](02-review-primitives.md#findings). |
| Historical SQL expected-formula duplication | accepted → resolved | 기존 고정 quoting 예시를 유지하고 property는 실제 DuckDB parser 결과와 원문을 비교합니다. [Primitive review F2](02-review-primitives.md#findings). |
| Historical result-only projection drift note | accepted for primitive / deferred for composition | Pair identity가 result-only·manifest-only·순서·byte 경계를 구별하는지는 직접 보강했습니다. Operations promotion composition은 #270/#277 소유로 유지합니다. [Artifact review](04-review-artifacts.md#legacy-adoption-and-handoff). |

## Current Improvements And Boundaries

- **DuckDB / SQL:** 정상·예외 후 연결 close, memory 격리, read-only 실제 거부, quoted metadata, lock 획득 실패의 typed cause를 보호합니다. SQL property가 구현의 escape 식을 복제하지 않습니다.
- **Artifacts:** 고정 입력의 pair inequality, 동일 byte의 경로 독립성, 누락 파일별 typed error, 실제 OS shared/exclusive lock matrix, body/unlock 동시 실패의 원래 예외 보존을 확인합니다.
- **dbt:** 실제 build와 두 번의 재실행 결과를 변환하지 않은 원값으로 고정 tuple에 대조합니다. 세 grain 차원, 9개 staging type, complete-key numeric NULL과 action `1/2/4`를 구별합니다. 별도 negative scenario는 source·staging·mart quality test의 정확한 네 실패를 관찰합니다.
- **Classification:** 확인된 문제는 테스트 oracle·evidence gap입니다. 이 PR에서 재현한 production defect는 없습니다. 새 product behavior나 source·Spec·공용 설정 변경을 포함하지 않습니다.

## Final Integration Handoff

| Owner | Item | Evidence / next action |
| --- | --- | --- |
| #270 / #277 | Result-only candidate drift와 current pair 보존 | 현행 main의 [Operations drift test](../../tests/data_operations/test_dbt_runner.py)는 manifest 변경을 사용합니다. Result만 달라지는 candidate를 거부하고 기존 current 두 파일의 고정 bytes를 보존하는 composition 검증은 해당 owner에서 재확인합니다. 이 PR의 primitive 결과를 end-to-end 성공으로 승격하지 않습니다. |
| #277 | Artifact primitive의 canonical detail | Pair identity·projection lock의 domain ownership과 기존 public behavior는 확인했지만 Data Platform의 두 canonical Spec에는 세부 계약이 직접 선언되어 있지 않습니다. Spec 보강 여부는 별도 owning change의 판단 사항이며 이번 테스트 보강의 production defect로 세지 않습니다. |
| #277 | Shared / cross-domain integration | 소비자가 같은 physical lock과 artifact pair를 사용하는지, 공유 dbt·CI 설정과 다른 도메인의 최종 조합을 선행 PR 병합 뒤 검증합니다. |
| #277 | Shared pre-push Git environment | [상세 재현·격리 근거](07-report-pre-push-environment.md). Git fixture가 hook의 `GIT_DIR`·`GIT_INDEX_FILE`을 상속하는 위험을 공유 pytest 실행 경계에서 영구 수정해야 합니다. PR #271은 위험 hook을 중단했고 branch/index 무손상을 확인했으며 임시 외부 wrapper의 격리 probe가 통과했습니다. |

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | Isolated environment | `uv sync --locked --offline`; PR worktree의 `.venv`에 locked dependency를 준비했습니다. tracked dependency 변경 없음. |
| ✅ Pass | Pre-change Data Platform baseline | `uv run --no-sync pytest tests/data_platform -q`: 22 passed, 5.68s. 기존 fork DeprecationWarning 1건. |
| ✅ Pass | Final domain suite | `uv run --no-sync pytest tests/data_platform tests/dbt -q`: **43 passed, 1 warning in 21.75s**, validated implementation `8bf4e6b0`. 마지막 metric helper 원값 비교까지 포함한 재실행입니다. 모든 marker level을 유지하고 기본 `memory/stress`만 제외했습니다. Skip 없음. warning은 기존 fork DeprecationWarning입니다. |
| ✅ Pass | Python lint / format / diagnostics | `uv run --no-sync ruff check tests/data_platform tests/dbt`, `ruff format --check`, `ty check tests/data_platform tests/dbt`: 모두 통과. `ruff check --show-files`로 Python 5개 파일을 확인했습니다. IDE diagnostics 도구는 제공되지 않아 type diagnostics는 `ty`로 확인했습니다. |
| ✅ Pass | Counterexample detection | [Primitive report](02-review-primitives.md#validation)의 3종, [artifact report](04-review-artifacts.md#validation)의 4종, [dbt report](03-review-dbt.md#validation)의 3종 transient mutant를 모두 검출했습니다. 전체 mutation coverage나 타 도메인 성공을 의미하지 않습니다. |
| ✅ Pass | Final Markdown / frontmatter / diff | `rumdl fmt/check` 11개 Markdown, repository Inbox validator와 YAML parser 기반 required frontmatter 검사 9개 artifact, `git diff --check` 통과. Tests/design는 reviewed implementation과 추가 diff가 없습니다. |
| ✅ Pass | Independent review | [별도 review-lead와 두 specialist의 최종 평가](06-review-independent.md): `clear`, confirmed current_required finding과 coverage gap 없음. Reviewed implementation `8bf4e6b0`. |
| ✅ Pass | Git state / temporary hook isolation | [hook incident report](07-report-pre-push-environment.md). 중단 후 HEAD/index/tests는 `8bf4e6b0`과 일치. Git-local env scrub 후 synthetic Git init/add/commit probe 1개 통과. 중단된 broad hook을 pass로 세지 않습니다. |
| ✅ Pass | Safe normal pre-push | 실제 pytest child의 Git-local env가 비어 있음을 확인한 뒤 `pytest --testmon --testmon-forceselect`: **850 passed, 3 skipped, 79 deselected in 153.69s**. Python check도 통과. Push 후 HEAD/index/worktree와 테스트 코드 무손상 확인. Cache 기반 선택 범위를 전체 suite의 증거로 확대하지 않습니다. |
| ✅ Pass | Prospective-merge CI | [CI Lite 40208654726](https://github.com/mols3131d/hmda-data-reliability/actions/runs/40208654726), 위 `d2367583`에서 `python3 scripts/ci/run_checks.py pytest`, `FULL_TESTS=false`, `TARGETS=tests/data_platform tests/dbt`: **43 passed, 1 warning in 32.42s**. Python validation의 scoped type target도 동일했고 성공했습니다. 생략된 OpenSpec·Tach·wheel·다른 도메인 검증을 수행했다고 주장하지 않습니다. |
| ⚪ Not Verified | Final cross-domain / permanent hook remediation | #277 소유입니다. Fixture 실행·로컬 primitive·녹색 CI를 live service나 모든 소비자 조합의 성공으로 승격하지 않습니다. |

## Review Readiness And Handoff

위 snapshot에서 scope·description·현재 validation·독립 리뷰가 충족됐고 unresolved blocking feedback은 없었습니다. 남은 domain-lane 구현 작업은 없습니다. 이 보고서의 상태를 기록하는 Inbox-only delivery 뒤에는 GitHub의 최신 base/head·Checks를 다시 조회해 같은 판단이 적용되는지 확인합니다. Base, tests, 계약 또는 material feedback이 바뀌면 이 assessment를 재평가합니다.

인간의 다음 판단은 고정 metric fixture와 oracle 변경을 검토하고 Draft의 Ready 전환 여부를 결정하는 것입니다. 위 #277 인계 항목, 특히 공유 pre-push 환경의 영구 수정은 별도 owner의 다음 작업입니다. 이 PR의 테스트를 약화하거나 허용된 쓰기 경계를 넘어 닫지 않습니다.
