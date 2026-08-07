---
type: openspec-rpi
category: research
title: "Project Pivot Deep Review Validity and Architectural Evidence Research"
description: "inbox/2026-08-07/03-40-project-pivot-deep-review-2026-08-07.md 보고서의 지적 사항을 코드베이스의 실제 구현 및 계약과 교차 검증한다."
status: "completed"
tags:
  - "domain:reliability"
  - "subdomain:evidence"
  - "capability:deep-review-validation"
---

> [!NOTE]
> Deep Review 보고서의 P1~P3 지적 사항을 코드베이스와 검증한 결과, dbt build 성공 전 아티팩트 삭제로 인한 증거 소실(P1), `freshness_at` 강제 대체(P1), 메인 README 설명 부족(P3) 등 핵심 지적들이 코드상에서 유효함을 확인했다. 다만 OpenSpec 완료 수치 및 Marimo 잔재(P2)는 최근 커밋을 통해 이미 일부 해결되었거나 아카이브가 수반되었다.

## Question

- **Primary:** `inbox/2026-08-07/03-40-project-pivot-deep-review-2026-08-07.md` 보고서의 지적 사항들이 현재 코드베이스의 실제 아키텍처 및 동작과 일치하며, 맹신 없이 채택할 만한 근거를 갖추었는가?
- **Scope:** `src/project_pivot/data_operations/runner.py`, `src/project_pivot/reliability/profiling/profile_snapshot_builder.py`, `src/project_pivot/reliability/contracts/profile.py`, `README.md`, OpenSpec 아카이브 상태.
- **Stop Condition:** P1~P3 지적 사항별로 코드 위치, 실제 동작, 타당성 평가 및 개선 제안과의 정합성이 모두 명확히 분류될 때.

## Findings

### F1. dbt build 실패 시 기존 artifact 유실 문제 (P1 - Valid)

`src/project_pivot/data_operations/runner.py`의 `run_dbt_build()` 함수는 빌드 시도 직전 `_remove_dbt_artifacts(request)`를 호출하여 기존 `manifest.json`과 `run_results.json`을 즉시 삭제한다. 빌드가 실패하거나 타임아웃이 발생할 경우 직전 성공 시점의 artifact까지 유실된다.

- **Evidence** - `src/project_pivot/data_operations/runner.py`에서 `_remove_dbt_artifacts`가 `subprocess.run` 이전에 무조건 실행된다.
- **Implication** - 실패한 빌드 이후 Lineage 또는 Impact 분석을 시도할 때 직전 성공 상태의 아티팩트가 삭제되어 시스템의 증거 보존(Evidence Integrity) 원칙을 위배한다.

### F2. Freshness 미측정 시 observed_at 대체 문제 (P1 - Valid)

`src/project_pivot/reliability/profiling/profile_snapshot_builder.py`의 `_normalize_freshness` 함수는 `freshness_column`이 지정되지 않거나 파티션 내 값이 없으면 `request.observed_at`을 `freshness_at`으로 채워 넣는다.

- **Evidence** - `src/project_pivot/reliability/profiling/profile_snapshot_builder.py`의 `if value is None: return fallback` 구문. `ProfileSnapshot` 계약(`src/project_pivot/reliability/contracts/profile.py`)도 `freshness_at: datetime`을 필수 필드로 강제한다.
- **Implication** - 측정되지 않은 관측 시각이 마치 원천 데이터의 최신 갱신 시각인 것처럼 오해될 수 있어, 신뢰성 탐지기(Detector)가 지연(Delay)을 감지하지 못할 위험이 존재한다.

### F3. OpenSpec 상태 불일치 지적 (P2 - Partially Resolved / Outdated)

리뷰 보고서는 OpenSpec change의 `tasks.md` 미완료 수치 및 active set 누적을 지적했다.

- **Evidence** - 최근 커밋(`0b14023`, `30c7a30`)에서 `hmda-eda-baseline-reduce-core-scope` 및 `hmda-eda-reconcile-core-contract` 두 change가 `openspec/changes/archive/2026-08-07-*`로 성공적으로 이동 및 아카이브되었다.
- **Implication** - 보고서 작성 시점(baseline `8980e09`) 기준으로는 유효했으나, 최근 TDD 및 아카이브 작업을 통해 현재 리포지토리에서는 해결된 상태다.

### F4. README의 리포지토리 가이드 부족 (P3 - Valid)

현재 `README.md`는 프로젝트의 개괄적 목적만 한 문장으로 제공하고 있으며 quickstart, 시스템 구성도, 데이터 가이드가 포함되어 있지 않다.

- **Evidence** - `README.md` 단일 파일 내용 확인.
- **Implication** - 외부 검토자나 신규 기여자가 시스템 실행 방식과 안전 경계를 이해하는 데 문서 탐색 비용이 커진다.

## Options

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| **Option A: P1 이슈 즉시 리팩토링** | 증거 보존(Evidence Integrity) 및 신뢰성 계약의 수밀성 향상 | dbt 빌드 롤백 디렉터리 구조 및 `ProfileSnapshot` Optional 타입 변경 수반 |
| **Option B: CI Gate 구축 및 README 보완** | 리포지토리 거버넌스 및 온보딩 편의성 강화 | 핵심 도메인 로직 변경 없이 인프라/문서 작업에 집중 |

## Conclusion

- **Answer** - Deep Review 보고서는 dbt 빌드 실패 시 증거 삭제, Freshness 대체 문제 등 아키텍처 핵심을 매우 정확히 지적하고 있다. 다만 OpenSpec 아카이브 미비 등 일부 거버넌스 지적은 최근 작업을 통해 조치 완료된 상태다.
- **Recommendation** - 보고서의 지적 중 P1 결함(dbt last-known-good 아티팩트 보존, `freshness_at` Optional/Status 모델링)을 우선 조치하고, 이어서 README 및 CI Gate 추가 작업을 수행할 것을 권장한다.
- **Next Step** - `runner.py`의 dbt build 아티팩트 보존 로직에 대한 TDD 설계 및 `ProfileSnapshot` freshness 타입 모델링 검토.

## Evidence

| Evidence | Supports | Location |
| --- | --- | --- |
| `_remove_dbt_artifacts` 호출 위치 | F1 (dbt artifact 유실) | `src/project_pivot/data_operations/runner.py` |
| `_normalize_freshness` 폴백 동작 | F2 (Freshness 대체) | `src/project_pivot/reliability/profiling/profile_snapshot_builder.py` |
| OpenSpec archive 폴더 이동 커밋 | F3 (OpenSpec 상태 해결) | `openspec/changes/archive/2026-08-07-*` |
| 메인 README 단일 문장 구성 | F4 (README 설명 부족) | `README.md` |
