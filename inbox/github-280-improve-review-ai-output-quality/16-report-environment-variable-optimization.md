---
type: report
title: Environment Variable Audit and Optimization Review
description: 활성 개발 프로젝트 맥락과 인간 개발자 UX, 표준 컨벤션 선점 및 미래 확장성을 고려한 환경변수 최적화 권고안입니다.
tags:
  - environment
  - configuration
  - cleanup
  - developer-experience
  - extensibility
---

# Environment Variable Audit and Optimization Review

`.env.example` 및 코드베이스 전반의 환경변수 사용처를 전수 조사하고, 활발히 개발이 진행 중인 프로젝트 맥락(Active Development), 인간 개발자 UX, 표준 컨벤션 선점 및 확장성 관점에서 최적화 방안을 재정립합니다.

## Audit Overview

- **대상 파일**: `.env.example`, `.env`, `src/`, `scripts/`, `tests/`
- **조사 목적**: 코드 삭제에만 매몰되지 않고, 개발 중인 프로젝트의 표준 컨벤션 선점 효과와 명백한 레거시 사장 설정을 균형 있게 분별하여 최적의 개발자 경험(DX)을 구축.

## Current Variable Classification

| Group | Variable | Reference / Consumer | Classification | Optimization Action |
| --- | --- | --- | --- | --- |
| System | `LOG_LEVEL` | 향후 표준 로깅 연동 예정 | **Convention** | **유지** (표준 컨벤션 선점 및 파편화 방지) |
| System | `TZ` | Python / C Runtime (`Asia/Seoul`) | **Active** | **유지** |
| System | `PYTHONPATH` | Python Module Import (`src`) | **Active** | **유지** |
| Cache & Temp | `DATA_DIR` | 코드 내 참조 없음 | **Dead** | **제거** (하위 경로와 연동 안 되는 가짜 앵커) |
| Cache & Temp | `CACHE_DIR` | 코드 내 참조 없음 | **Dead** | **제거** (`UV_CACHE_DIR`로 충분) |
| Cache & Temp | `UV_CACHE_DIR` | `uv` CLI, CI 테스트 참조 | **Active** | **유지** |
| Cache & Temp | `TMPDIR` | Python `tempfile` 표준 | **Active** | **유지** |
| Cache & Temp | `TEMP`, `TMP` | Python `tempfile` Windows fallback | **Defensive** | **유지** (크로스 플랫폼 임시파일 격리) |
| Artifacts | `HMDA_RELIABILITY_ARTIFACTS_DIR` | `review_ai`, `log_agent_event.py`, 테스트 | **Active** | **유지** |
| Langfuse | `LANGFUSE_BASE_URL` | Langfuse Python SDK | **Active** | **유지** |
| Langfuse | `LANGFUSE_PUBLIC_KEY` | Langfuse Python SDK | **Active** | **유지** (온보딩 필수 설정) |
| Langfuse | `LANGFUSE_SECRET_KEY` | Langfuse Python SDK | **Active** | **유지** (온보딩 필수 설정) |
| Langfuse | `LANGFUSE_TIMEOUT` | Langfuse Python SDK | **Active** | **유지** |
| Provider | `OPENAI_BASE_URL` | `RuntimeAISettings`, `experiment.py` | **Active** | **유지** |
| Provider | `OPENAI_API_KEY` | `RuntimeAISettings`, `experiment.py` | **Active** | **유지** |
| Data Lake | `HMDA_RELIABILITY_DUCKDB_PATH` | `data_operations`, `orchestration` | **Active** | **유지** |
| Data Lake | `HMDA_RELIABILITY_SOURCE_ROOT` | `data_operations`, `orchestration` | **Active** | **유지** |
| Data Lake | `HMDA_RELIABILITY_SOURCE_YEAR` | `data_operations`, `orchestration` | **Active** | **유지** |
| Data Lake | `HMDA_EDA_DATA_PATH` | 과거 아카이브 문서 외 참조 없음 | **Dead** | **제거** (이미 `SOURCE_ROOT`/`YEAR`로 대체됨) |
| dbt | `DBT_PROFILES_DIR` | dbt Core CLI | **Active** | **유지** |
| dbt | `DBT_SEND_ANONYMOUS_USAGE_STATS` | dbt Core CLI | **Active** | **유지** |
| Airflow | `AIRFLOW_HOME` | Apache Airflow CLI/Runtime | **Active** | **유지** |
| Airflow | `AIRFLOW__CORE__DAGS_FOLDER` | Apache Airflow Configuration | **Active** | **유지** |
| Airflow | `AIRFLOW__CORE__LOAD_EXAMPLES` | Apache Airflow Configuration | **Active** | **유지** |

## Active Project Development and Human UX Analysis

단순히 "현재 코드에서 읽지 않으니 모두 삭제한다"는 기계적인 규칙은 활발히 개발 중인 프로젝트에 부적합할 수 있습니다. 템플릿의 변수는 **미래 코드 작성을 유도하는 컨벤션 신호(Signaling)** 역할도 수행합니다.

### 1. `LOG_LEVEL` 유지 이유 (표준 컨벤션 선점)

- **네이밍 파편화 방지**: `LOG_LEVEL`은 12-factor 앱의 사실상 표준입니다. 템플릿에 선점되어 있지 않으면 팀원이나 새 모듈 작성 시 `DEBUG_MODE`, `VERBOSE`, `HMDA_LOG` 등 임의의 변수를 만들어 파편화될 위험이 있습니다.
- **템플릿 안정성**: 로깅 설정을 보강할 때마다 `.env.example`을 삭제했다가 다시 추가하는 커밋 노이즈를 방지합니다.
- **인지적 일치**: 백엔드/데이터 엔지니어에게 프로젝트 루트의 `LOG_LEVEL=INFO`는 가장 직관적이고 친숙한 설정입니다.

### 2. 플랫폼 방어 변수 유지 (`TEMP`, `TMP`)

- Linux/macOS에서는 `TMPDIR`만으로 충분하지만, Windows 네이티브 환경(PowerShell 등)에서는 Python `tempfile`이 `TEMP` / `TMP`를 우선 탐색합니다.
- 제거 시 Windows 사용자의 임시 파일이 시스템 기본 폴더로 누출될 수 있으므로, 방어적 목적으로 유지하고 주석으로 이유를 설명합니다.

### 3. 명백한 제거 대상 (정리해야 할 진짜 부채)

컨벤션 가치가 없고 개발자에게 헛수고를 유발하는 변수는 정리가 필수적입니다.

- **`HMDA_EDA_DATA_PATH`**: 2026년 7월 초기 설계 잔재이며, 실제 코드는 이미 `HMDA_RELIABILITY_SOURCE_ROOT`와 `HMDA_RELIABILITY_SOURCE_YEAR`를 조합해 동작합니다. 남아 있으면 엉뚱한 변수를 수정하게 만드는 오해를 낳습니다.
- **`DATA_DIR`, `CACHE_DIR`**: 상위 폴더를 바꾸면 하위 DB나 캐시가 연동될 것처럼 보이지만, 실제로는 하위 변수들이 독립 하드코딩 문자열을 사용합니다. 연동되지 않는 가짜 상위 앵커는 제거하는 것이 멘탈 모델에 좋습니다.

## Extensibility and Future-Proofing Analysis

### 1. 표준 도구 네이티브 확장 원칙 (Zero Custom Wrapper)

- 외부 도구(Airflow, Langfuse, dbt, OpenAI 등)를 감싸는 자체 `HMDA_*` 접두사를 만들지 않고 공식 표준 변수를 직접 유지합니다.
- Airflow는 `AIRFLOW__{SECTION}__{KEY}` 체계로 코드 수정 없이 환경변수로만 설정을 확장할 수 있습니다.

### 2. URI 스키마 기반 스토리지 확장

- 로컬 파일에서 향후 클라우드(S3, GCS, Lakehouse)로 확장 시 `USE_S3=true`, `S3_BUCKET=...` 등의 플래그성 변수를 늘리지 않습니다.
- 기존 경로 변수(`HMDA_RELIABILITY_SOURCE_ROOT` 등)가 `s3://bucket/path`와 같은 표준 URI 스키마를 수용하도록 설계하여 환경변수 개수를 불변으로 유지합니다.

### 3. 게이트웨이 기반 다중 모델 확장

- OpenAI-compatible 엔드포인트(`OPENAI_BASE_URL`)를 유지하여 게이트웨이(LiteLLM 등)나 프록시를 통해 모델이 추가되어도 환경변수 증식을 억제합니다.

## Refined Optimization Recommendations

1. **명백한 사장 변수 3건 정리**: `HMDA_EDA_DATA_PATH`, `DATA_DIR`, `CACHE_DIR` 삭제 (가짜 앵커 및 대체된 과거 잔재 제거).
1. **표준 컨벤션 변수 유지**: `LOG_LEVEL` 유지 (로깅 표준 선점).
1. **플랫폼 방어 변수 유지**: `TMPDIR`, `TEMP`, `TMP` 유지 (Windows 임시파일 격리).
1. **온보딩 가시성 향상**: 필수 수정 항목(Langfuse 키)과 기본값 영역 시각 분리.
1. **문자열 값 큰따옴표(`"..."`) 포맷팅**: 경로·URL·식별자·빈 키(`""`)는 큰따옴표로 감싸 경계와 빈 문자열 의도를 명확히 하고, 숫자(`30`, `2025`)와 불리언(`false`)은 리터럴로 유지.

## Proposed Optimized `.env.example`

```bash
# === System & Runtime Environment ===
LOG_LEVEL="INFO"
TZ="Asia/Seoul"
PYTHONPATH="src"

# === Cache and Local Directory Isolation ===
UV_CACHE_DIR="./.cache/uv"
# Python tempfile isolation across POSIX (TMPDIR) and Windows (TEMP, TMP)
TMPDIR="./.tmp"
TEMP="./.tmp"
TMP="./.tmp"

# Generated local evaluation and run artifacts
HMDA_RELIABILITY_ARTIFACTS_DIR="./.local/artifacts"

# === Langfuse Native Review AI (Action Required for Remote Evals) ===
LANGFUSE_BASE_URL="https://cloud.langfuse.com"
LANGFUSE_PUBLIC_KEY=""
LANGFUSE_SECRET_KEY=""
LANGFUSE_TIMEOUT=30

# === Model Provider (Local Ollama default, compatible with OpenAI & Gateways) ===
OPENAI_BASE_URL="http://localhost:11434/v1"
OPENAI_API_KEY="ollama"

# === Data Pipeline & Storage (Local paths or future URI schemes: s3://) ===
HMDA_RELIABILITY_DUCKDB_PATH="data/hmda_reliability.duckdb"
HMDA_RELIABILITY_SOURCE_ROOT="data/raw/hmda"
HMDA_RELIABILITY_SOURCE_YEAR=2025

# === dbt Configuration ===
DBT_PROFILES_DIR="dbt"
DBT_SEND_ANONYMOUS_USAGE_STATS=false

# === Apache Airflow Local Runtime (Extendable via AIRFLOW__{SECTION}__{KEY}) ===
AIRFLOW_HOME="${PWD}/.local/airflow"
AIRFLOW__CORE__DAGS_FOLDER="${PWD}/src/hmda_reliability/orchestration/dags"
AIRFLOW__CORE__LOAD_EXAMPLES=false
```
