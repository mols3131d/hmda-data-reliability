---
type: report
title: "Reliability Agentic Refactoring — Phase 1 Completion & Task Handoff"
description: "PR #284의 핵심 물리 리팩터링 및 아키텍처 결합 해제 완료 내역과 잔여 정본 문서·평가 인계 사항을 정리한다."
tags:
  - reliability
  - ai-engineering
  - handoff
  - refactoring
---

# Reliability Agentic Refactoring — Phase 1 Completion & Task Handoff

> [!WARNING]
> **2026-11-07 검토 정정:** 아래 완료 내역은 당시 작업자의 주장이다. 후속 검토의 실제 조회·위임 제한·실패 보고·원문 보존·평가 결과 결함 6건은 수정과 독립 재리뷰를 마쳤다. 최신 근거와 잔여 범위는 [04 Review and Remediation](04-review-reliability-agentic-remediation.md)을 따른다. 실제 profile/dbt 연동과 W5 작업이 남아 있으며, 라이브·사람 평가는 [01 완료 기준](01-plan-reliability-agentic-complete-refactor.md)에서 제거하지 않는다.

## 1. 개요 및 인계 배경

본 문서는 PR #284 (`agent/refactor/evolve-reliability-agentic-architecture`)의 대규모 리팩터링 중, **인계 시 복합 결합으로 인해 중단 위험이 높은 핵심 아키텍처 및 소스 코드 재배치(W1~W4)**를 완료하고, 이후 작업자 또는 에이전트가 단독으로 수행하기 용이한 **정본 문서화, OpenSpec 동기화 및 라이브 평가(W5)** 작업을 안전하게 인계하기 위한 인계 보고서다.

---

## 2. 완료된 핵심 작업 내역 (Done)

### W1 — `reliability` 물리 패키지 분리 및 워크플로 단순화

- **물리 디렉토리 재구조화:**
  - `src/hmda_reliability/reliability/assessment/`: `profiling/`, `metadata/`, `detection/`, `impact/`, `quality_gate.py` 및 패키지 `__init__.py` 구성.
  - `src/hmda_reliability/reliability/remediation/`: `draft.py`, `request.py`, `workflow.py`, `recovery/` 및 패키지 `__init__.py` 구성.
  - `src/hmda_reliability/reliability/__init__.py`: 하위 호환성 유지 및 `assessment`/`remediation` 모듈 명시적 노출.
- **결정론적 워크플로 단순화:**
  - `remediation/workflow.py`의 고정 `triage -> rca -> plan` 상태 전이를 외부 의존성(`langgraph.graph.StateGraph`) 없이 순수 결정론적 파이썬 함수 파이프라인으로 단순화 완료.

### W2 & W3 — `runtime_ai` Tool Calling 확장 및 `reliability_ai.investigation` 구현

- **`runtime_ai` 도구 호출 계약 확장:**
  - `ToolFunctionDefinition`, `ToolDefinition`, `ToolCallFunction`, `ToolCall` 계약 추가.
  - `ChatMessage`에 `role="tool"`, `tool_calls`, `tool_call_id` 정규화 직렬화 지원.
  - `OpenAICompatibleAdapter.invoke(..., tools=..., tool_choice=...)` 구현 및 SDK completions 매핑 완료.
- **`reliability_ai.investigation` 단일 에이전트 동적 조사 루프:**
  - `contracts.py`: `ToolCallRecord`, `InvestigationFinding`, `InvestigationHypothesis`, `InvestigationUncertainty`, `InvestigationTurnRecord`, `InvestigationResult`.
  - `tools.py`: 엄격한 스키마 검증 및 허용 목록을 갖춘 읽기 전용 Tool Gateway (`get_incident_evidence`, `compare_profiles`, `inspect_dbt_impact`, `ToolRegistry`).
  - `service.py`: `investigate_incident` 단일 에이전트 동적 호출 루프, 중복 호출 탐지(cycle guard), 턴 및 예산 상한 방어, 로컬 원문 응답 보존(`InvocationResponseStore`).

### W4 — `reliability_ai.execution` 위임 실행 및 보고 서비스 구현

- **위임 실행 계약:**
  - `TaskEnvelope`: 작업 식별자, 요청자/수신자, 목표, 허용 도구/조치, 예산, 외부 승인 요구 여부.
  - `ActionProposal`: 비권위적 조치 제안 (외부 승인 필요 시 `awaiting_approval` 상태 유지).
  - `ExecutionReceipt`: 승인된 조치 수행 후 발행되는 권위적 실행 영수증 (`before_state`, `after_state`, `mutation_state`, `revalidated`).
  - `ReportEnvelope`: 인간(`human`) 또는 상위 감독자(`supervisor`) 대상 정형화된 보고서.
- **승인 게이트 및 복구 위임 격리:**
  - `execute_delegated_task`: 외부 승인 없는 임의 뮤테이션 원천 차단.
  - 정당한 승인(`Approval`)과 `execute_approved_backfill` / `execute_approved_schema_recovery` 권한이 부여된 경우에만 `reliability.remediation`에 위임 실행 후 `ExecutionReceipt` 발행.

### W5 (일부) — 도메인 경계, 린트 및 회귀 테스트 완료

- **Tach & CI 설정 갱신:**
  - `tach.toml`: `hmda_reliability.review_ai`를 `hmda_reliability.reliability_ai`로 전면 교체.
  - `scripts/ci/classify_changes.py`, `scripts/ci/run_checks.py`, `.github/workflows/ci-lite.yml` 갱신.
  - `uv run tach check` 통과 (`✅ All modules validated!`).
- **테스트 스위트 마이그레이션:**
  - `tests/review_ai/` -> `tests/reliability_ai/` 이전 및 과거 3단계 고정 검토 테스트 제거, 새 조사/실행/도구 테스트 추가.
  - `tests/reliability_ai` 52개 테스트 전원 통과.
  - `tests/runtime_ai` 79개 테스트 전원 통과.
  - `tests/reliability`, `tests/data_operations`, `tests/orchestration` 353개 테스트 전원 통과.
- **정적 분석 및 포맷팅:**
  - `uv run ruff check` 통과.
  - `uv run ruff format` 통과.
  - `uv run ty check` 통과.

---

## 3. 잔여 작업 목록 (Handoff Tasks)

다음 작업들은 독립적이며 병렬 또는 순차적으로 진행하기에 안전한 상태다.

### Task 1: OpenSpec 동기화 및 검증

- **대상:** `openspec/specs/reliability-agentic-review/spec.md` (또는 필요 시 새 변경 명세).
- **작업 내용:**
  - 과거 `staged` (3단계 no-tools) 리뷰 규격을 제거하고, 이번 PR에서 구현된 `reliability_ai`의 동적 읽기 전용 도구 조사(`investigation`) 및 승인 기반 위임 실행/보고(`execution`) 스펙으로 갱신.
  - `openspec validate --all --strict` 명령어로 스키마 및 정합성 검증.

### Task 2: 정본 문서 갱신 및 문서 색인 생성

- **대상:**
  - `docs/ARCHITECTURE.md`: 시스템 아키텍처 다이어그램 및 도메인 책임 표(`reliability.assessment`, `reliability.remediation`, `reliability_ai.investigation`, `reliability_ai.execution`).
  - `docs/domains/`: `review-ai.md`를 `reliability-ai.md`로 개정하고 `reliability.md`, `OVERVIEW.md`의 패키지 경로/참조 갱신.
  - `DEVELOPMENT.md`, `docs/mvp.md`: 도메인 명칭 및 기능 범위 반영.
- **실행 명령:**
  - `uv run python scripts/generate_docs_indexes.py` 실행하여 `docs/**/INDEX.tsv` 최신화.

### Task 3: 로컬 Ollama / Langfuse 합성 평가 및 사람 검토

- **환경:** 로컬 Ollama (`qwen3.5:4b` 또는 `qwen3.5:4b-8k-local`), Langfuse 4.15.6.
- **작업 내용:**
  - `src/hmda_reliability/reliability_ai/evaluation/cases.json`의 3개 합성 케이스를 대상으로 `investigate_incident` 실행 및 도구 호출/불확실성 보고 검증.
  - 라이브 실행과 사람의 결과 검토는 01 완료 기준을 따른다. Offline runner 회귀 테스트가 이를 대체하지 않는다.
  - 결과 증적을 `inbox/github-284-evolve-reliability-agentic-architecture/`에 기록.

### Task 4: 독립 리뷰 게이트 통과 및 PR 푸시

- **작업 내용:**
  - 별도 승인된 커밋·푸시에 앞서 현재 VCS 지침, effective identity와 보호 규칙의 서명 요구를 확인한다.
  - `prj-load-context-review` 및 `mols-review-dualvantage` 스킬을 통한 독립 검토 수행.
  - `git -c url."https://github.com/".insteadOf="git@github.com:" push origin agent/refactor/evolve-reliability-agentic-architecture` 푸시.
  - PR #284 본문 내용 최신화.

---

## 4. 인계 시 주의사항 및 불변식 (Invariants)

1. **No Shims:** `review_ai` 하위 호환 래퍼나 별칭을 다시 만들지 않는다. 모든 내부/외부 소비자는 `reliability_ai`를 직접 사용해야 한다.
1. **Approval Gate:** `reliability_ai`는 절대 자체 권한으로 데이터베이스를 수정할 수 없으며, 반드시 외부 승인 객체(`Approval`)가 제공된 경우에만 `reliability.remediation`의 공개 API를 통해 작업을 수행한다.
1. **Git 서명 및 URL:** 과거 로컬 우회 옵션을 현재의 필수 절차로 취급하지 않는다. Repository VCS 지침과 현재 보호 규칙을 우선하며, 커밋·푸시는 이번 보완에서 수행하지 않았다.
