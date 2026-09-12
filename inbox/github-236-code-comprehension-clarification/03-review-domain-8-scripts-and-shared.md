---
type: review
title: "Review: Domain 8 (scripts & shared) Code Comprehension Refactor and Clarification"
description: "Domain 8(scripts & shared utilities)의 전체 파일군(scripts/, tests/scripts/, src/hmda_reliability/logger.py)에 대해 서브에이전트 병렬 실행으로 진행된 코드 이해 비용 리팩터링 및 설명 보강에 대한 품질 및 안전성 통합 리뷰"
tags:
  - review
  - comprehension
  - scripts
  - shared
  - quality
  - adversarial
---

# Review: Domain 8 (`scripts` & shared) Code Comprehension Refactor and Clarification

## Executive Summary

Domain 8 (`scripts` & shared)의 전체 파일군([scripts/](scripts/), [tests/scripts/](tests/scripts/), [src/hmda_reliability/logger.py](src/hmda_reliability/logger.py))을 대상으로 서브에이전트 2대를 병렬로 분할·실행하여 `mols-clarify-code`, `mols-clarify-runtime`, `mols-code-comprehension-refactor` 작업을 성공적으로 완료했다.

모든 변경은 **외부 관찰 가능한 기능, CLI 인터페이스, 부수 효과 순서, 서브프로세스 호출 규약 및 에러 시맨틱스를 100% 보존**하면서 복잡한 경로 정리 subsumption 로직, Git 추적 파일 필터링 제어 흐름, Windows 플랫폼 전용 래퍼 우회 메커니즘, 프런트매터 추출 및 의존성 합성 불변식을 명확히 문서화하고 네이밍을 정돈했다.

관련 단위/컴포넌트 테스트 **122개(121 passed, 1 skipped) 전체가 무회귀(Zero Regression)로 통과**되었으며, Ruff 린트(`line-length=88` 준수 포함) 및 포맷 검증도 완벽히 통과했다.

---

## Review Scope & Inspected Changes

서브에이전트 2개 워커(Group A, Group B)로 분할하여 안전하게 병렬 처리했다:

| Group | Files Covered | Main Interventions | Skill |
| --- | --- | --- | --- |
| **Group A**<br/>(에셋/문서/동기화) | `scripts/rulesync.py`<br/>`scripts/agent_assets.py`<br/>`scripts/generate_agent_routes.py`<br/>`scripts/generate_docs_indexes.py`<br/>`src/hmda_reliability/logger.py`<br/>`tests/scripts/test_agent_assets.py`<br/>`tests/scripts/test_generate_agent_routes.py`<br/>`tests/scripts/test_generate_docs_indexes.py` | - 브리지 생성 및 tracked diff 오라클 불변식 문서화<br/>- YAML 프런트매터 파싱, JSONC 주석 보존, GitHub raw URL 합성 및 중복 충돌 거부 불변식 명시<br/>- TSV 포맷 후행 탭 방지 및 디렉토리 설명 투영 불변식 명시<br/>- 공통 로거 멱등성 계약 보강<br/>- 테스트 시나리오별 검증 목적 및 불변식 주석 보강 | `mols-clarify-code`<br/>`mols-clarify-runtime` |
| **Group B**<br/>(운영/CLI 도구) | `scripts/_commands.py`<br/>`scripts/bootstrap.py`<br/>`scripts/clean.py`<br/>`scripts/biome.py`<br/>`scripts/tombi.py`<br/>`scripts/log_agent_event.py`<br/>`scripts/validate_inbox_artifacts.py`<br/>`scripts/run_actual_source.py`<br/>`scripts/run_agentic_review_live.py`<br/>`tests/scripts/test_bootstrap.py`<br/>`tests/scripts/test_ci_classifier.py`<br/>`tests/scripts/test_clean.py`<br/>`tests/scripts/test_commands.py`<br/>`tests/scripts/test_log_agent_event.py`<br/>`tests/scripts/test_tool_wrappers.py`<br/>`tests/scripts/test_validate_inbox_artifacts.py` | - Windows npm.cmd 우회 및 `.local/tooling` 로컬 바이너리 실행 계약 명시<br/>- `clean.py`의 후보군 subsumption 중복 제거(`_deduplicate_candidates`) 및 Git 추적 경로 포함 검사(`_tracked_index_contains_path`) 네이밍 및 제어 흐름 단순화<br/>- 심볼릭 링크 순회 거부(`_symlink_ancestor_reason`) 및 6단계 안전성 검증(`_safety_reason`) 계약 명시<br/>- 도그푸딩 이벤트 원본 페이로드 필터링 및 조용한 실패(Fail-closed) 계약 명시<br/>- 인박스 아티팩트 루트 축약 및 번들 README 처리 규칙 문서화<br/>- `test_clean.py` 동적 모듈 임포트 반환 타입 힌트 오류 정돈 | `mols-clarify-code`<br/>`mols-code-comprehension-refactor` |

---

## Quality Assessment (품질 평가)

### 1. Intended Behavior & Contract Preservation

- **CLI 호출 규약 및 부수 효과 보존**: `scripts/_commands.py`, `scripts/biome.py`, `scripts/tombi.py`, `scripts/clean.py` 등 모든 CLI 도구의 파라미터 파싱, 종료 코드 반환, stdout/stderr 출력 및 파일 삭제 조건이 100% 동일하게 유지되었다.
- **제어 흐름 가독성 및 네이밍 정돈**: `clean.py`에서 `_contains_tracked_path`를 `_tracked_index_contains_path`로 변경하고, `unique` 및 `is_already_covered` 변수명을 도입하여 경로 깊이 순 정렬과 부모 디렉토리 포함 판정 로직을 독자가 즉각 이해할 수 있도록 개선했다.
- **포맷 및 린트 준수**: 모든 docstring 및 인라인 주석이 저장소 기본 규칙인 `line-length = 88` 및 Ruff 표준 검사를 완벽히 통과하도록 정돈되었다.

---

## Adversarial Assessment (적대적/안전성 평가)

### 1. Security & Fail-closed Invariants

- **심볼릭 링크 및 디렉토리 순회 공격 방지**: `clean.py`의 `_symlink_ancestor_reason` 및 `_safety_reason`의 6단계 안전성 검증이 온전히 보존되어 의도치 않은 시스템 파일 또는 상위 경로 삭제가 철저히 방지됨을 검증했다.
- **에이전트 텔레메트리 새니타이징**: `log_agent_event.py`에서 민감한 프롬프트/응답/도구 입력 데이터가 제거되고 스칼라 메타데이터만 원장에 남는 안전성 계약이 명확히 보존되었다.

### 2. Isolated Out-of-Scope Issues

조사 중 발견된 아래 2건의 중요 위험 요인은 본 리팩터링에서 임의로 수정하지 않고 [inbox/2026-09-12-refactor-code-comprehension-clarification/01-note-out-of-scope-issues.md](01-note-out-of-scope-issues.md)에 안전하게 격리 기록되었다.

1. `ISSUES-scripts-01`: `rulesync.py`의 `_check_claude_bridges`에서 stale 및 mismatched 브리지 모두 `"stale ..."` 프리픽스로 출력하여 내용 불일치 항목이 오인되는 문제.
1. `ISSUES-scripts-02`: `generate_agent_routes.py`의 `find_local_skill_files` git 명령 실패 시 glob 폴백 경로와 git 파싱 경로 간의 일관성 위험.
