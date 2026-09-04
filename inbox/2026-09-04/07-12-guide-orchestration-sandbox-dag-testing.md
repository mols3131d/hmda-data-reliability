---
type: guide
title: "Airflow Web UI 샌드박스 DAG 실행 및 파라미터 설정 가이드"
description: "Airflow 웹 콘솔에서 hmda_data_plane DAG을 실행할 때 메인 DB 격리를 보장하기 위한 런타임 파라미터 설정법, 시나리오별 입력값 및 UI 조작 절차를 안내한다."
tags:
  - orchestration
  - airflow
  - web-ui
  - sandbox
  - params
---

# Airflow Web UI 샌드박스 DAG 실행 및 파라미터 설정 가이드

메인 데이터베이스([data/hmda_reliability.duckdb](../../data/hmda_reliability.duckdb))의 실데이터(1,354만 건)를 완벽히 보호하면서, Airflow Web UI에서 `hmda_data_plane` DAG을 격리된 샌드박스 환경으로 트리거하고 검증하는 방법을 상세히 안내한다.

---

## 1. Web UI 기동 및 로그인

### 1.1 로컬 Standalone 서버 기동

터미널에서 Airflow 로컬 환경변수를 설정하고 서버를 기동한다:

```bash
export AIRFLOW_HOME="$(pwd)/.local/airflow"
export AIRFLOW__CORE__DAGS_FOLDER="$(pwd)/src/hmda_reliability/orchestration/dags"
export AIRFLOW__CORE__LOAD_EXAMPLES=false

uv run airflow standalone
```

### 1.2 콘솔 접속 정보

- **URL:** `http://localhost:8080`
- **Username:** `admin`
- **Password:** [.local/airflow/simple_auth_manager_passwords.json.generated](../../.local/airflow/simple_auth_manager_passwords.json.generated) 파일에 생성된 암호 사용 (`QKRKAfU5zGnDKCZ5`)

---

## 2. DAG 트리거 화면 진입 및 입력 방식

1. 로그인 후 DAG 목록에서 **`hmda_data_plane`** 을 클릭한다.
1. 우측 상단의 재생 아이콘 드롭다운을 열고 **`Trigger DAG w/ config`** 를 선택한다.
1. Airflow UI에서는 두 가지 방식으로 파라미터를 입력할 수 있다:
   - **Form 뷰 (기본):** 각 파라미터 필드별 GUI 입력 박스에 직접 값을 입력.
   - **Configuration JSON 뷰:** 우측/상단의 JSON 탭으로 전환하여 전체 파라미터 JSON을 한 번에 붙여넣기.

---

## 3. 파라미터 상세 명세 및 샌드박스 가이드

[src/hmda_reliability/orchestration/dags/hmda_data_plane.py](../../src/hmda_reliability/orchestration/dags/hmda_data_plane.py)에 정의된 5가지 런타임 오버라이드 파라미터 목록이다:

| 파라미터 (`params`) | UI 타입 | 비워둘 때 적용되는 기본값 | 샌드박스 테스트 시 설정 가이드 |
| --- | --- | --- | --- |
| **`database_path`** | `string` / `null` | `data/hmda_reliability.duckdb`<br>*(메인 DB)* | **[필수 변경]** 메인 DB 오염 방지를 위해 반드시 격리된 경로 입력<br>예: `data/sandbox_2026.duckdb` 또는 `/tmp/sandbox.duckdb` |
| **`source_root`** | `string` / `null` | `data/raw/hmda` | 원천 데이터 폴더. 기본 원천 디렉터리를 그대로 쓰거나 합성 파일이 위치한 폴더 지정 |
| **`source_year`** | `integer` / `null` | `2025` | 적재 대상 연도 파티션 ($2000 \le \text{year} \le 2100$).<br>2026 결함 테스트 시 `2026`으로 지정 |
| **`source_file`** | `string` / `null` | `null` (폴더 내 전체 탐색) | 특정 파일 1개만 단독 적재할 때 파일명 지정 (선택).<br>단, 파일명에 4자리 연도가 포함되어야 함 (예: `2026_null_spike.parquet`) |
| **`run_dbt_build`** | `boolean` / `null` | `true` | 품질 게이트 통과 후 dbt 분석 마트 빌드 여부.<br>전체 파이프라인 검증 시 `true`, 원천 적재/게이트만 빠르게 검증 시 `false` |

> [!WARNING]
> **`database_path`를 절대로 비워두지 마십시오!**  
> `database_path`를 `null`로 두면 프로젝트 기본값인 메인 프로덕션 DB(`data/hmda_reliability.duckdb`)에 직접 적재가 발생합니다. 샌드박스 테스트 시에는 항상 고유한 격리 경로(`data/sandbox_2026.duckdb` 등)를 지정해야 합니다.

---

## 4. 시나리오별 파라미터 설정 (복사하여 사용)

### 시나리오 1. 2026 합성 결함 데이터(`null_spike`) 적재 및 퀄리티 게이트 차단 테스트 [핵심]

- **테스트 목표:** 2026년 합성 이상 데이터가 인제스션된 직후, `evaluate_quality_gate` 태스크가 이를 감지하여 파이프라인을 의도적으로 실패(`AirflowException`)시키고 다운스트림 `build_dbt_loan_analytics` 실행을 정상 차단하는지 검증한다.
- **UI Form 입력값:**
  - `database_path`: `data/sandbox_2026.duckdb`
  - `source_root`: `data/raw/hmda`
  - `source_year`: `2026`
  - `source_file`: `null` (또는 해당 합성 파일명)
  - `run_dbt_build`: `true` (체크 유지)
- **Configuration JSON 붙여넣기:**

  ```json
  {
    "database_path": "data/sandbox_2026.duckdb",
    "source_root": "data/raw/hmda",
    "source_year": 2026,
    "source_file": null,
    "run_dbt_build": true
  }
  ```

- **기대 결과:**
  1. `load_raw_hmda_loans`: **성공 (`success`, 초록색)**
  1. `evaluate_quality_gate`: **실패 (`failed`, 빨간색)** — 내장 baseline 대비 income Null 급증 탐지
  1. `build_dbt_loan_analytics`: **차단 (`upstream_failed`, 주황색)** — dbt 빌드가 실행되지 않음

---

### 시나리오 2. 2025 정상 데이터 샌드박스 전체 E2E 통과 테스트

- **테스트 목표:** 격리된 샌드박스 DB에서 원천 적재부터 퀄리티 게이트 통과, dbt 마트 빌드 및 artifact 승격까지 전 과정이 정상 완료되는지 확인한다.
- **UI Form 입력값:**
  - `database_path`: `data/sandbox_2025.duckdb`
  - `source_root`: `data/raw/hmda`
  - `source_year`: `2025`
  - `source_file`: `null`
  - `run_dbt_build`: `true`
- **Configuration JSON 붙여넣기:**

  ```json
  {
    "database_path": "data/sandbox_2025.duckdb",
    "source_root": "data/raw/hmda",
    "source_year": 2025,
    "source_file": null,
    "run_dbt_build": true
  }
  ```

- **기대 결과:**
  - 3개 태스크 모두 **성공 (`success`, 초록색)** 완료.
  - `load_raw_hmda_loans` 및 `build_dbt_loan_analytics`의 Outlet Asset 이벤트 발행 확인.

---

### 시나리오 3. dbt 빌드 제외 빠른 단독 검증 (`run_dbt_build: false`)

- **테스트 목표:** dbt 빌드 시간을 단축하고, 원천 적재와 퀄리티 게이트 통과 여부만 빠르게 단독 검증한다.
- **Configuration JSON 붙여넣기:**

  ```json
  {
    "database_path": "data/sandbox_fast.duckdb",
    "source_year": 2025,
    "run_dbt_build": false
  }
  ```

- **기대 결과:**
  - `load_raw_hmda_loans`: **성공 (`success`)**
  - `evaluate_quality_gate`: **성공 (`success`)**
  - `build_dbt_loan_analytics`: **건너뜀 (`skipped`, 분홍색)** — `AirflowSkipException` 발생

---

## 5. UI 결과 확인 및 트러블슈팅

### 5.1 태스크 실행 상태 및 로그 확인

1. **Grid 뷰 / Graph 뷰:**
   - 트리거 후 실행 중인 DAGRun 막대를 클릭하여 3개 태스크의 진행 상태를 확인한다.
1. **실패 원인 로그 확인:**
   - 빨간색으로 실패한 `evaluate_quality_gate` 블록 클릭 → 우측 슬라이드 패널에서 **Logs** 탭 선택.
   - `QualityGateError` 및 탐지된 인시던트 내역(예: `null_spike: income Null 비율 초과`) 로그 확인.
1. **Outlet Evidence 확인:**
   - 성공한 태스크 클릭 후 **Asset Events** 또는 태스크 상세 메타데이터에서 `outlet_events`에 기록된 샌드박스 DB 경로, 적재 건수, dbt 결과 코드 확인.

### 5.2 샌드박스 실행 시 자주 발생하는 이슈 및 조치

- **`IO Error: Could not set lock on file ...`**
  - **원인:** DuckDB는 단일 프로세스 전용 락을 가집니다. CLI, DBeaver, marimo, Python 터미널 등이 해당 샌드박스 `.duckdb` 파일을 열어두고 있는 경우 발생합니다.
  - **해결:** 외부 프로그램의 DuckDB 연결을 닫은 후 Airflow 태스크를 재실행(`Clear`)합니다.
- **`HMDADataLoadError: HMDA 소스 파티션에 적재할 행이 없습니다`**
  - **원인:** `source_file`을 지정할 때 파일명에 연도 4자리(예: `2026`)가 들어있지 않으면 파티션 연도 추출 정규식이 실패합니다.
  - **해결:** 원천 파일명이 `hmda_2026_null_spike.parquet`처럼 4자리 연도를 포함하도록 변경하거나 `source_file`을 `null`로 두고 디렉터리 기반으로 탐색하게 합니다.
- **테스트 종료 후 샌드박스 파일 정리:**
  - 샌드박스 검증이 완료된 임시 데이터베이스는 디스크 용량 관리를 위해 삭제할 수 있습니다:

    ```bash
    rm -f data/sandbox_*.duckdb*
    ```
