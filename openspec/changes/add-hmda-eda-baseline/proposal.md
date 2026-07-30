## Why

현재 EDA baseline은 CSV 파싱 오류 행을 조용히 제외할 수 있고, 완료된 것으로 표시된 검증은 현재 입력에서 계산·렌더링된 결과를 증명하지 않는다. 신뢰할 수 없는 row count와 null rate는 이후 reliability 기준선의 해석을 왜곡할 수 있으므로, reader 무결성과 재실행 검증을 명시해야 한다.

## What Changes

- 원천 HMDA CSV의 required columns 존재와 타입 기준을 표시한다.
- 전체 및 `activity_year`별 row count, required column별 null count와 null rate를 표시한다.
- EDA 출력과 `ProfileSnapshot` evidence 필드의 대응 및 baseline/current 역할을 표시한다.
- 원천 관측 시각이 없으면 freshness를 `미측정`으로 표시하고, 파일 수정 시각과 Bronze `ingested_at`을 데이터 freshness와 구분한다.
- CSV reader를 fail-fast로 구성한다. 파싱 오류 또는 입력 파일 부재 시 baseline metric과 `eda_evidence`를 생성하지 않는다.
- valid sample, malformed CSV, full source를 분리한 새 Marimo kernel 검증으로 baseline 결과를 확인한다.

## Capabilities

### New Capabilities

- `hmda-eda-baseline`: 원천 HMDA CSV를 탐색해 reliability 기준선과 측정 경계를 표시하는 Marimo 노트북 계약.

### Modified Capabilities

- 없음

## Impact

- `notebooks/eda_mo.py`의 화면용 EDA 출력이 확장된다.
- CSV reader의 `ignore_errors=true` 동작이 제거된다. 손상된 입력은 성공한 baseline 대신 명시적 실행 오류를 반환한다.
- EDA reference와 OpenSpec task 상태는 실제 input path 및 새 kernel 실행 증거와 일치해야 한다.
- 저장 가능한 EDA 구조와 화면 표시는 분리하지만, production lifecycle, detector, recovery API는 변경하지 않는다.
- 새 runtime dependency와 데이터 migration은 없다.
