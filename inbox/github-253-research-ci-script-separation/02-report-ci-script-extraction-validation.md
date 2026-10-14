---
type: report
title: CI Script Extraction Validation
description: PR 253의 CI 스크립트 추출, classifier 배치와 분리 판단, 로컬 검증 결과 및 기존 경계 위험을 기록한다.
---

# CI Script Extraction Validation

## Change

[계획](00-plan-ci-validation-and-script-extraction.md)에 따라 CI-only 변경이 classifier와 step 계약 테스트를 선택하도록 하고, source·dependency·Tach 변경의 검증은 유지했다. 긴 Markdown, OpenSpec, Python, pytest step을 독립 Bash 스크립트로 추출했다. Workflow는 setup과 step 조건, 짧은 도구 호출을 소유한다.

추가 정리 요청으로 classifier를 [scripts/ci/classify_changes.sh](../../scripts/ci/classify_changes.sh)로 옮겼다. OpenSpec capability mapping, 연관 active Change 탐색과 fallback은 [classify_openspec.sh](../../scripts/ci/classify_openspec.sh)에 모았다. 공통 selector 상태, 일반 경로 분류, domain consumer mapping과 최종 출력은 classifier에 유지했다. 작은 [changed_files.sh](../../scripts/ci/changed_files.sh)는 파일 수집 한 가지 역할만 하므로 더 나누지 않았다. 파일 길이만을 이유로 domain별 스크립트나 범용 routing framework를 추가하지 않았다.

기존 classifier의 `--stdin`, `--markdown-paths`와 출력 파일 append 계약은 유지한다. Workflow의 classifier 호출을 실제 임시 Git 저장소에서 실행하는 테스트로 새 경로와 `GITHUB_OUTPUT` wiring을 확인했다. `full_unit`과 CI 변경이 겹치면 선택된 CI non-unit 계약 테스트도 실행하며, `full_tests`에서는 중복 실행하지 않는다.

## Local Validation

**Basis:** 2026-10-03, branch `agent/research-ci-script-separation`, HEAD `4f6c9960cda33136fe989e02ca90c40c46bc7e11` 위의 미커밋 작업 트리. 아래 결과는 원격 CI나 커밋된 revision의 통과 근거가 아니다.

| Result | Command or Check | Observed Evidence |
| --- | --- | --- |
| Pass | `uv run --no-sync pytest tests/scripts/test_ci_classifier.py tests/scripts/test_ci_steps.py -q` | 분리와 workflow 호출 테스트 추가 후 114 passed |
| Pass | `bash -n` for `scripts/ci/*.sh` | CI Bash 스크립트 7개의 문법 검사 통과 |
| Pass | Ruff check / format check | 수정한 두 CI 계약 테스트 모듈 통과 |
| Pass | `ty check` | 수정한 두 CI 계약 테스트 모듈 통과 |
| Pass | `rumdl check` | CI policy와 Testing Guide 통과 |
| Not Run | Remote CI | 구현 변경은 아직 commit/push하지 않음 |

VS Code 테스트 도구가 사용자 설정으로 비활성화되어 있어 pytest는 local terminal에서 실행했다. 외부 CLI 경계는 fake executable로 통제하고 실제 임시 Git 저장소를 사용했으며 network provider는 호출하지 않았다.

## Independent Review

최종 `review-lead` assessment는 **clear**다. Quality와 adversarial specialist가 현재 파일과 전체 numbered HEAD 기준본을 대조했고, 승인된 범위의 새로운 `current_required` finding은 없었다. OpenSpec 정책만 분리한 경계에 추가 분할을 요구할 근거도 없었다.

최초 assessment는 실행 도구가 없어 기준본과 tracked diff를 확보하지 못해 `blocked`였다. 이후 완전한 classifier 502행·workflow 274행의 기준본과 tracked diff, 아래 후보의 runtime 비교를 제공해 증거 공백을 해소했다. 두 후보는 이번 변경의 회귀가 아닌 기존 제한으로 확인되어 `follow_up`으로 남겼다.

Review는 HEAD 위의 지정된 미커밋 파일 내용에 적용된다. Reviewer들은 파일 비교와 진단 조회를 직접 수행했지만 pytest·Bash 검사를 독립 재실행하지 않았으며, Git status와 로컬 실행 결과는 구현 담당자의 exact-state 근거를 사용했다. 이 판정은 원격 CI 통과나 GitHub approval·merge 판정이 아니다.

## Follow-Ups

두 항목은 이번 behavior-preserving 정리에서 수정하지 않은 기존 제한이다. 임시 저장소에서 기준 classifier와 현재 classifier의 기존 출력 key가 같은지 비교했다.

| Candidate | Reproduction | Baseline and Current Result | Disposition |
| --- | --- | --- | --- |
| Git quoted path | 이름에 쌍따옴표를 포함한 `inbox/double"quote.md`를 commit 후 `HEAD^1 HEAD` 비교 | `core.quotePath=false`에서도 C-quoted 경로가 반환되어 둘 다 `markdown=false`, `inbox=false`; 파일 수집 helper도 빈 배열 | Follow-up: NUL-safe 수집 또는 미지원 경로의 명시적 실패 정책 검토 필요 |
| OpenSpec intermediate symlink | active Change의 `specs`가 없는 inventory를 가리키는 dangling symlink | 둘 다 관련 Change target이 비고 `full_tests=false` | Follow-up: 중간 부모 경로까지 inventory 안전성 검사 검토 필요 |

Skills lock과 route generator의 schema 호환성, pre-push range 원인은 별도 범위로 남긴다. Route 검증과 hook을 끄거나 추측으로 수정하지 않았다. 기존 조사·리뷰 artifact의 옛 classifier 경로는 당시 상태를 설명하는 기록이므로 일괄 수정하지 않았다.
