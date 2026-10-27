---
type: review
title: Common Support Current Test Audit
description: Common Support의 현행 테스트 전수 검토, 과거 finding 재판정, 최소 회귀 보강과 검증 근거를 기록합니다.
---

# Common Support Current Test Audit

> [!NOTE]
> 도메인 테스트 검토와 허용된 보강을 수행했다. 독립 리뷰는 clear이며 최종 전달 상태는 아래 Current Review에서 확인한다. Draft/Ready/approval/merge는 별도 인간 결정이다.

- **Target:** [PR #276](https://github.com/mols3131d/hmda-data-reliability/pull/276)의 exclusive test lane과 read-only support/reserved integration.
- **Revision:** base `be1dca8d044494e92a0d25c791471a41b5d11bcf`; implementation/test head `64f3a1a28866b976322a4e7cc0b3b526244515e1`. 최초 준비 branch에 최신 main을 merge하여 검증했다.
- **Scope:** current tracked 22파일 전체 본문을 두 specialist가 각자 검토했다. Source/Spec은 관련 계약 대조용이며 수정하지 않았다.

## Findings And Adoption

| ID | Decision | Current evidence and action |
| --- | --- | --- |
| S1 / C1 / G8 | deferred / scope_decision | OpenSpec inventory uncertainty에서 full Python만 선택하고 `openspec_bulk=false`가 남는다. #277의 새 CLI 3-case probe로도 재확인; source/tooling owner가 안전한 fallback을 결정·수정해야 한다. |
| S2 / C2 | deferred to #277 | 예약 workflow test의 top-level PR/main entry, path-filter 부재, prospective merge checkout oracle을 #277에서 보강했다. |
| S3 | accepted / implemented | 기존 loader로 실제 bootstrap `main()`을 호출한다. 첫 external command가 17이면 반환 17과 후속 명령 미실행을 함께 검사한다. |
| S4 | deferred / scope_decision | reviewer의 새 public validator probe에서 comment-only null 및 comment가 붙은 빈 double/single quoted scalar 세 경우 모두 `errors=[]`. 실제 nonempty YAML 계약의 source 문제다. |
| S5 | accepted / implemented | 실제 local enabled/disabled/root Rule fixture에 enabled literal row 하나만 기대한다. 생성기와 regenerated index의 자기 일치로 대체하지 않는다. |
| S6 | deferred to #277 | 예약 telemetry test의 설명을 실제 관찰한 xdist compatibility smoke로 좁혔다. Worker span 관측을 새로 주장하지 않는다. |

## Contract Coverage

실제 Git·CLI·파일 보존/삭제와 literal argv/exit, independent fixtures가 주된 oracle이다. 외부 설치·npm·hosted Actions·live routing은 통제된 경계이며 성공 증거로 승격하지 않는다. CI argv stub은 실제 외부 validator 실행 성공과 다르다. Shared Git fixture/hook의 환경 상속은 기존 #270/H4와 같은 후속으로 통합하며, 검증 child에서 Git-local 변수 전체를 제거한다.

## Source Follow-up

[validate_inbox_artifacts.py](../../scripts/validate_inbox_artifacts.py)의 `_has_value`가 raw comment를 값으로 센다. `description: # TODO`, `description: "" # TODO`, `description: '' # TODO`를 거부하고 quoted 문자열 내부의 유효 `#`는 보존해야 한다. #276은 tests-only lane이므로 이를 green behavior로 고정하거나 production script를 수정하지 않았다. #277도 현재 exclusive 목록만으로 source 수정 권한이 생기지 않는다.

## File Coverage

이 표는 위 revision의 검토 ledger다. 테스트 수와 파일 수는 별개이며 reserved 파일의 검토는 수정 권한을 뜻하지 않는다.

| File | Coverage | Contract / oracle |
| --- | --- | --- |
| [tests/scripts/__init__.py](../../tests/scripts/__init__.py) | reviewed | package 설명 support |
| [tests/scripts/ci/__init__.py](../../tests/scripts/ci/__init__.py) | reviewed | package 설명 support |
| [tests/scripts/ci/conftest.py](../../tests/scripts/ci/conftest.py) | reviewed | 임시 Git, argv/exit stub, 독립 OpenSpec inventory |
| [tests/scripts/ci/helpers.py](../../tests/scripts/ci/helpers.py) | reviewed | classifier/runner subprocess와 Git/call-log support |
| [tests/scripts/ci/test_ci_classifier.py](../../tests/scripts/ci/test_ci_classifier.py) | reviewed | selection, deletion/rename, missing dir, Git failure, Inbox 제외 |
| [tests/scripts/ci/test_ci_classifier_openspec.py](../../tests/scripts/ci/test_ci_classifier_openspec.py) | reviewed | #277 reserved; active pairing/bulk/archive; uncertainty는 source 후속 |
| [tests/scripts/ci/test_ci_classifier_python.py](../../tests/scripts/ci/test_ci_classifier_python.py) | reviewed | full/scoped, dependency/architecture/setup routing |
| [tests/scripts/ci/test_ci_pytest.py](../../tests/scripts/ci/test_ci_pytest.py) | reviewed | exact argv/markers/parallel/guard dedup/failure |
| [tests/scripts/ci/test_ci_steps.py](../../tests/scripts/ci/test_ci_steps.py) | reviewed | #277 reserved; real Git changes, path, exit, OpenSpec modes |
| [tests/scripts/ci/test_ci_workflow.py](../../tests/scripts/ci/test_ci_workflow.py) | reviewed | #277 reserved; pinning/step selection/failure, entry/ref는 #277 보강 |
| [tests/scripts/test_agent_assets.py](../../tests/scripts/test_agent_assets.py) | reviewed | module CLI forwarding/order/failure |
| [tests/scripts/test_bootstrap.py](../../tests/scripts/test_bootstrap.py) | reviewed | step argv/order/cwd와 실제 main의 실패 중단 |
| [tests/scripts/test_clean.py](../../tests/scripts/test_clean.py) | reviewed | 실제 삭제/보존, symlink, tracked-index 재조회와 Git 격리 |
| [tests/scripts/test_commands.py](../../tests/scripts/test_commands.py) | reviewed | argv/cwd, npm 부재, Windows boundary |
| [tests/scripts/test_generate_agent_routes.py](../../tests/scripts/test_generate_agent_routes.py) | reviewed | lock/hash/collision/incomplete HTTP, literal enabled/disabled/root rows |
| [tests/scripts/test_generate_docs_indexes.py](../../tests/scripts/test_generate_docs_indexes.py) | reviewed | literal TSV, depth/exclusion, drift check 무변경 |
| [tests/scripts/test_log_agent_event.py](../../tests/scripts/test_log_agent_event.py) | reviewed | event correlation과 sanitized exact ledger fields |
| [tests/scripts/test_tach.py](../../tests/scripts/test_tach.py) | reviewed | native graph의 실제 forbidden imports/type-only/root/unowned |
| [tests/scripts/test_tach_config.py](../../tests/scripts/test_tach_config.py) | reviewed | configuration과 native negative control |
| [tests/scripts/test_tool_wrappers.py](../../tests/scripts/test_tool_wrappers.py) | reviewed | argv/cwd/exit와 stale projection 안내 |
| [tests/scripts/test_validate_inbox_artifacts.py](../../tests/scripts/test_validate_inbox_artifacts.py) | reviewed | naming/frontmatter/bundle/scope; comment scalar는 source 후속 |
| [tests/test_pytest_opentelemetry.py](../../tests/test_pytest_opentelemetry.py) | reviewed | #277 reserved; serial span과 xdist compatibility |

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | Current domain suite | `uv run --no-sync pytest -q -ra tests/scripts`: **365 passed, 2 skipped (22.17s)**. Testmon selection 없이 domain 전체를 실행했다. |
| ✅ Pass | Changed Python | Ruff check/format check와 ty check 통과. 위 implementation head의 변경 파일 대상이다. |
| ✅ Pass | Artifact mechanics | Native rumdl, Inbox validator, 실제 YAML parser의 필수값 검사, local links와 git diff check 통과. |
| ⚪ Not Verified | Runtime limits | Windows npm/Node와 cached zizmor actual audit 두 항목은 환경 조건으로 skip했다. |

## Current Review

**Assessment: clear.** Review-lead가 quality/adversarial 두 specialist의 독립 결과를 조정했다. 정확한 reviewed implementation head는 `64f3a1a28866b976322a4e7cc0b3b526244515e1`이며 base는 `be1dca8d044494e92a0d25c791471a41b5d11bcf`다. 기존 46파일 baseline 중 이 lane의 변경된 테스트와 현재 문서 3개를 두 관점에서 다시 대조했다.

수용한 공백은 닫혔고 남은 `current_required` finding은 없다. Source/공유 tooling 후속은 `follow_up / scope_change`로 분리했다. Reviewer는 suite를 재실행하지 않았으며 위 실행 결과는 coordinator evidence다. 이 판정은 test/document review gate이며 제품 source 후속의 해결이나 correctness approval을 의미하지 않는다.

최종 Inbox-only delivery는 이 head의 test/source/Spec blob을 보존한다. 전달 후 exact remote head, prospective merge CI와 review readiness는 [현재 PR 본문](https://github.com/mols3131d/hmda-data-reliability/pull/276)에서 확인한다. Draft/Ready/approval/merge를 자동 전환하지 않는다.

## Handoff

[Plan](00-plan-common-support-tests.md)과 위 검토 ledger에서 이어간다. 과거 [historical bundle](01-review-historical/README.md)은 그대로 보존하며 현재 검증 수로 재사용하지 않는다. Final Inbox-only delivery는 위 head의 test/source/Spec blob을 보존하고 exact remote head/CI는 PR 본문에서 확인한다.
