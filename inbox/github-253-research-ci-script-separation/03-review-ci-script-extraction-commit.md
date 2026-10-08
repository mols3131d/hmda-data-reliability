---
type: review
title: CI Script Extraction Commit Review
description: 커밋 a590cee의 CI 스크립트 추출, 검증 라우팅과 workflow 연결을 부모 커밋 및 CI 계약과 비교하고 검증 한계를 기록한다.
tags:
  - ci
  - github-actions
  - testing
---

# CI Script Extraction Commit Review

> [!IMPORTANT]
> **Pass (`clear`)**: 이번 커밋에서 새로 도입한 필수 수정 사항은 발견하지 못했다. 부모 커밋에도 있는 두 제한은 `follow_up`으로 분리했다. 파일·계약 리뷰는 전체 범위를 완료했지만 독립 실행 검증과 실제 Actions runtime 검증은 완료하지 않았다. 이 판정은 원격 CI 통과나 GitHub approval을 뜻하지 않는다.

- **Target**: PR [#253](https://github.com/mols3131d/hmda-data-reliability/pull/253)의 branch `agent/research-ci-script-separation`에서 생성한 `refactor(ci): 검증 스크립트 분리와 실행 범위 정리` 커밋.
- **Revision**: HEAD `a590ceea237fe76d868f1072659399e6519b87f9`, baseline parent `4f6c9960cda33136fe989e02ca90c40c46bc7e11`. 검토일은 2026-10-03이다.
- **Scope**: 커밋의 16개 변경 항목 전체와 직접 연관된 CI admission 동작. Workflow, 삭제된 classifier와 새 CI Bash 스크립트 7개, 두 계약 테스트, CI·testing 문서와 세 Inbox 산출물을 검토했다.

`review-lead`가 quality와 adversarial specialist의 독립 분석을 조정하고 후보 근거를 재확인했다. 현재 파일 전체와 부모 커밋의 관련 파일 5개 전체를 대조했으며, 과거 Inbox 보고서의 리뷰 판정을 이번 판정의 근거로 사용하지 않았다. 리뷰 시작 시 작업 트리는 clean이었다. 검토 대상 코드는 수정하지 않았다.

## Findings

두 항목 모두 `follow_up`이며 이번 커밋의 `current_required` finding은 아니다. 현재 변경을 완료하기 위한 필수 조치는 없다.

| ID | Severity | Finding | Action |
| --- | --- | --- | --- |
| F1 | Minor | Git이 C-quoted 문자열로 출력하는 파일명이 변경 선택에서 빠질 수 있다. | 별도 작업에서 NUL-safe 전달 또는 미지원 이름의 명시적 실패 정책을 검증한다. |
| F2 | Minor | OpenSpec 중간 dangling symlink가 불확실한 inventory로 분류되지 않는다. | 별도 작업에서 중간 경로 guard와 fail-safe fixture를 추가한다. |

## Details

### F1: Quoted File Paths

Minor, `follow_up`.

#### F1 Locations

- [scripts/ci/changed_files.sh](../../scripts/ci/changed_files.sh#L13)
  - `collect_changed_files`
- [scripts/ci/classify_changes.sh](../../scripts/ci/classify_changes.sh#L30)
  - Git 변경 파일 수집 및 Markdown 경로 분류

#### F1 Evidence

`git diff --name-only`를 줄 단위로 소비하고 literal 경로에 `-f` 검사를 적용한다. `inbox/double"quote.md`처럼 Git이 C-quoted 문자열로 출력하는 이름은 실제 경로와 일치하지 않는다. `core.quotePath=false`도 이 인용을 제거하지 않는다. 부모 classifier의 L26·L44·L343과 workflow L74에도 같은 수집·존재 확인 방식이 있어 추출로 새로 도입한 회귀는 아니다.

이번 리뷰는 정적 경로 분석과 기준본 대조로 판단했다. 앞선 [검증 기록](02-report-ci-script-extraction-validation.md)의 실행 재현은 과거 evidence이며 이번 리뷰의 독립 재현으로 간주하지 않았다.

#### F1 Impact

해당 이름의 변경 파일이 Markdown formatting과 Inbox metadata 검증에서 누락될 수 있다. 일반적인 이름이나 공백을 포함한 경로가 모두 누락된다는 뜻은 아니다.

#### F1 Action

후속 작업에서 Git 변경 목록의 NUL-safe 전달을 검토하거나, 지원하지 않는 이름을 명시적으로 실패시키는 정책을 정하고 실제 Git 파일명 회귀 검사를 함께 추가한다. 이번 리뷰 요청에는 구현 수정이 포함되지 않는다.

### F2: Intermediate OpenSpec Symlink

Minor, `follow_up`.

#### F2 Locations

- [scripts/ci/classify_openspec.sh](../../scripts/ci/classify_openspec.sh#L43)
  - active Change inventory guard
  - 최종 capability 경로 검사

#### F2 Evidence

알려진 canonical capability가 변경되고 active Change의 중간 `specs` 경로가 dangling symlink이면 최종 `specs/$capability`의 `-L`, `-e`, `-d`가 모두 false일 수 있다. Inventory root와 Change 자체의 guard는 이 중간 경로 조건을 차단하지 않는다. 부모 classifier L133·L151·L159에도 같은 검사 순서가 있어 helper 분리의 회귀가 아니다.

판단 근거는 코드와 기준본 대조다. 현재 실제 inventory에 이 조건이 존재하는지, 실제 OpenSpec CLI가 어떻게 반응하는지는 확인하지 않았다.

#### F2 Impact

불확실한 inventory를 관련 Change가 없는 상태로 해석하여 연관 Change 검증과 전체 검증 확대를 누락할 수 있다.

#### F2 Action

후속 작업에서 중간 부모 경로의 안전성도 검사하고, dangling symlink를 포함한 fixture로 보수적 fallback을 확인한다. 현재 커밋의 필수 수정 사항으로 확대하지 않는다.

## Candidate Checks

- CI-only 변경이 source·dependency·Tach 검증을 약화한다는 후보는 기각했다. 해당 경로의 Tach 선택과 setup·boundary·runtime smoke 조건은 유지된다. Workflow 자체만으로 Tach를 선택하던 동작의 제거는 승인된 범위다.
- `full_unit` fallback이 CI non-unit 계약 테스트를 누락한다는 후보는 기각했다. Classifier의 `ci_targets`, workflow 전달과 pytest 보완 실행이 연결되며 `full_tests`에서는 중복 실행하지 않는다.
- Git 비교 실패가 빈 변경 목록으로 성공한다는 후보는 기각했다. Classifier의 선행 수집과 collector의 실패 반환이 오류를 전파한다.
- Markdown 필수 도구 실패와 docs-only lint는 계속 실패를 전파하고 formatter 진단·diff는 비차단으로 분리된다. Trigger, 권한, setup 버전·조건, timeout·concurrency, route-only 검증, marker와 xdist 경계를 대조했으며 의도 밖 변경을 발견하지 못했다.

## Validation

로컬 실행은 커밋 직전의 동일 파일 내용에서 수행했다. Pre-commit은 formatting 차이를 만들지 않았다. Reviewer가 직접 확인한 근거와 호출자가 제공한 실행 근거를 구분한다.

| Result | Check | Evidence |
| --- | --- | --- |
| Pass | 독립 전체 파일·기준본 비교 | Quality·adversarial specialist가 전체 범위를 분석하고 lead가 후보 근거와 baseline 비교를 확인했다. |
| Pass | 독립 editor diagnostics | Workflow와 두 CI 테스트 모듈의 `get_errors`에서 오류 없음. |
| Pass | Focused pytest, 호출자 실행 | `uv run --no-sync pytest tests/scripts/test_ci_classifier.py tests/scripts/test_ci_steps.py -q -p no:sugar --color=no --tb=short`: `114 passed in 4.22s`. |
| Pass | Bash syntax, 호출자 실행 | `scripts/ci/*.sh` 7개에 각각 `bash -n` 실행, 모두 성공. |
| Pass | Python static checks, 호출자 실행 | 두 테스트 모듈의 Ruff check, format `--check`, `ty check` 통과. |
| Pass | 문서·Inbox 계약, 호출자 실행 | CI·Testing Guide의 `rumdl check` 및 세 Inbox 산출물의 `scripts/validate_inbox_artifacts.py` 통과. |
| Pass | Diff와 commit hooks, 호출자 실행 | `git diff --check` 및 pre-commit의 Markdown 5개·Python 2개 formatting/lint 통과, 내용 변경 없음. |
| Not Verified | 독립 pytest·Bash 실행 및 F1·F2 runtime 재현 | Reviewer의 일반 명령 실행 도구가 없었다. VS Code `runTests`도 `No tests found`여서 실행 근거가 아니다. |
| Not Verified | Remote CI와 실제 prospective merge | 구현 커밋을 push하지 않았으며 실제 Actions runner 검증은 실행하지 않았다. |
| Not Verified | Whole suite와 실제 외부 CLI 동작 | Focused 계약 테스트는 실제 임시 Git 저장소와 fake executable을 사용한다. 전체 suite나 실제 도구 연동의 증거가 아니다. |

## Risks and Limits

- Clean worktree, 부모 커밋 관계, baseline archive provenance와 origin 대비 상태는 호출자가 확인한 Git 결과에 의존한다. Reviewer는 파일 대조와 diagnostics를 직접 확인했지만 실행 검증을 독립 재수행하지 않았다.
- 판정은 지정된 head와 baseline의 변경에만 적용된다. 이 보고서의 후속 문서 커밋은 구현 리뷰 대상을 바꾸지 않는다.
- 구현·테스트·CI 설정이나 병합 기준 상태가 실질적으로 바뀌거나 Actions에서 selector·도구·marker 관련 실패가 발생하면 정확한 revision과 실행 로그를 기준으로 재리뷰한다.
- GitHub approval, 리뷰 제출, push, Ready 전환과 merge는 수행하지 않았다. 원격 admission 근거가 필요한 다음 단계는 해당 브랜치를 push한 뒤 prospective merge CI 결과를 확인하는 것이다.
