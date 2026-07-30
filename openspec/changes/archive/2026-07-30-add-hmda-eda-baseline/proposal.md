## Why

현재 `notebooks/eda_mo.py`는 원천 HMDA CSV의 컬럼명과 추론 타입만 표시한다. Reliability가 비교하는 row count, null rate, schema, freshness의 탐색 기준선과 근거를 확인할 수 없다.

## What Changes

- 원천 HMDA CSV의 required columns 존재와 타입 기준을 표시한다.
- 전체 및 `activity_year`별 row count, required column별 null count와 null rate를 표시한다.
- EDA 출력과 `ProfileSnapshot` evidence 필드의 대응 및 baseline/current 역할을 표시한다.
- 원천 관측 시각이 없으면 freshness를 `미측정`으로 표시하고, 파일 수정 시각과 Bronze `ingested_at`을 데이터 freshness와 구분한다.

## Capabilities

### New Capabilities

- `hmda-eda-baseline`: 원천 HMDA CSV를 탐색해 reliability 기준선과 측정 경계를 표시하는 Marimo 노트북 계약.

### Modified Capabilities

- 없음

## Impact

- `notebooks/eda_mo.py`의 화면용 EDA 출력이 확장된다.
- 저장 가능한 EDA 구조와 화면 표시는 분리하지만, production lifecycle, detector, recovery API는 변경하지 않는다.
- 새 runtime dependency와 데이터 migration은 없다.
