---
title: "Environment Variables"
description: "로컬 `.env` 주입 경로, `.env.example` 표기 규칙, 도메인별 환경변수 소유 경계와 확장 원칙을 안내합니다."
categories:
  - software-engineering
tags:
  - airflow
  - configuration
  - dbt
  - dotenv
  - langfuse
---

# Environment Variables

환경변수 키와 기본값의 정본은 [`.env.example`](../../.env.example)이다. 이 문서는 **언제 `.env`가 필요한지, 어떤 값을 수정해야 하는지, 각 변수 그룹을 누가 소유하는지**만 정의한다.

## Usage

일반 offline `pytest`는 `.env` 없이 격리된 기본값과 임시 경로로 동작한다. 원격 Langfuse 연동이나 CLI 실행처럼 환경 주입이 필요한 명령만 `uv run --env-file .env`를 사용한다.

```bash
cp .env.example .env
uv run --env-file .env <command>
```

> [!IMPORTANT]
> `.env`는 Git 추적 대상이 아니다. 이미 자격 증명이 설정된 환경에서는 `cp .env.example .env`로 덮어쓰지 않고 필요한 키만 반영하며, 실제 API 키(`LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `OPENAI_API_KEY`)는 커밋·로그·문서·아티팩트에 기록하지 않는다.

## Ownership By Scope

세부 변수명과 기본값은 [`.env.example`](../../.env.example)을 따르고, 여기서는 도메인별 소유권과 수정 시점만 구분한다.

| Scope | Variables | Owner / Consumer | When to change |
| --- | --- | --- | --- |
| Langfuse | `LANGFUSE_*` | Langfuse Python SDK | 원격 Prompt 등록·Dataset 실험 시 인증 키(`PUBLIC_KEY`, `SECRET_KEY`)와 대상 서버(`BASE_URL`) 설정 |
| Model Provider | `OPENAI_*` | [`RuntimeAISettings`](../../src/hmda_reliability/runtime_ai/settings.py), [`experiment.py`](../../src/hmda_reliability/review_ai/evaluation/experiment.py) | 로컬 Ollama 외 다른 OpenAI-compatible 엔드포인트·게이트웨이를 호출할 때 |
| Data Pipeline | `HMDA_RELIABILITY_DUCKDB_PATH`, `HMDA_RELIABILITY_SOURCE_*` | [`data_operations/request.py`](../../src/hmda_reliability/data_operations/request.py), [`orchestration/config.py`](../../src/hmda_reliability/orchestration/config.py) | 기본 DuckDB 파일이나 HMDA 원본 데이터 경로·연도를 바꿀 때 |
| Artifacts | `HMDA_RELIABILITY_ARTIFACTS_DIR` | [`scripts/log_agent_event.py`](../../scripts/log_agent_event.py), `review_ai` | 로컬 실행 증거 및 평가 산출물 루트(`.local/artifacts`)를 분리할 때 |
| System & Cache | `LOG_LEVEL`, `TZ`, `PYTHONPATH`, `UV_CACHE_DIR`, `TMPDIR`, `TEMP`, `TMP` | Python 런타임, `uv` CLI, `tempfile` | 기본값 유지 권장. `TEMP`·`TMP`는 Windows 임시파일 격리를 위해 `TMPDIR`과 함께 유지 |
| dbt & Airflow | `DBT_*`, `AIRFLOW_HOME`, `AIRFLOW__*` | dbt Core, Apache Airflow | 로컬 프로필 위치나 Airflow 런타임 경로를 변경할 때 |

Review AI 원격 등록과 실험 절차는 [Review AI Evaluation](review-ai-evaluation.md), 프롬프트 config 관리는 [Review AI Prompt Management](review-ai-prompts.md)를 따른다.

## Formatting Rules

[`.env.example`](../../.env.example)과 로컬 `.env`를 편집할 때는 다음 표기 규칙을 적용한다.

| Value type | Rule | Example | Reason |
| --- | --- | --- | --- |
| 문자열·경로·URL | 큰따옴표(`"..."`)로 감싼다 | `PYTHONPATH="src"` | 공백·`#` 주석 오인 방지 및 값 경계 명확화 |
| 빈 문자열 | `""`로 명시한다 | `LANGFUSE_PUBLIC_KEY=""` | 누락이 아닌 의도된 빈 기본값임을 표시 |
| 변수 치환 경로 | 큰따옴표(`"..."`)를 유지한다 | `AIRFLOW_HOME="${PWD}/.local/airflow"` | 작은따옴표(`'...'`) 사용 시 `${PWD}` 치환이 비활성화됨 |
| 숫자·불리언 | 따옴표 없는 리터럴로 표기한다 | `LANGFUSE_TIMEOUT=30`, `AIRFLOW__CORE__LOAD_EXAMPLES=false` | 문자열과 숫자·불리언 타입 의도 구분 |

## Extensibility Rules

환경변수를 새로 추가하거나 정리할 때는 다음 경계를 지킨다.

- **외부 도구 표준 변수 직접 사용**: Airflow(`AIRFLOW__{SECTION}__{KEY}`), Langfuse(`LANGFUSE_*`), dbt(`DBT_*`), OpenAI SDK(`OPENAI_*`)가 공식 지원하는 변수는 자체 `HMDA_*` 접두사로 다시 감싸지 않는다.
- **표준 컨벤션 선점과 사장 변수 분리**: `LOG_LEVEL`처럼 네이밍 파편화를 막는 12-factor 표준 변수는 유지하되, 하위 경로와 연동되지 않는 가짜 상위 변수(예: `DATA_DIR`, `CACHE_DIR`)나 대체된 레거시 변수는 즉시 제거한다.
- **URI 스키마 기반 스토리지 확장**: 클라우드 스토리지(S3, GCS 등) 지원이 필요할 때 `USE_S3` 같은 플래그 변수를 늘리지 않고, 기존 경로 변수(`HMDA_RELIABILITY_SOURCE_ROOT` 등)가 `"s3://bucket/path"` URI를 수용하도록 확장한다.
- **인프라 연결과 모델 파라미터 분리**: 엔드포인트 주소와 인증(`OPENAI_*`)만 환경변수로 두며, 모델 태그·`max_tokens`·추론 읽기 `timeout`은 Langfuse Prompt Management의 versioned config에서 관리한다.
