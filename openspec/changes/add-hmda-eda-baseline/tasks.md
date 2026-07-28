## 1. 원천 EDA 구조

- [ ] 1.1 `notebooks/eda_mo.py`에서 CSV reader 설정을 공유 relation으로 정의하고 입력 경로·null 처리·sample 범위를 표시한다.
- [ ] 1.2 required column과 expected type family 상수를 추가한다.

## 2. Baseline 출력

- [ ] 2.1 required column 존재와 추론 타입 비교표를 만들고 누락·타입 불일치 callout을 추가한다.
- [ ] 2.2 전체와 `activity_year`별 row count를 계산하고 baseline/current 출력 역할을 표시한다.
- [ ] 2.3 required column별 null count와 null rate를 계산하고 `NA`, 빈 문자열 null 처리 결과를 표시한다.
- [ ] 2.4 `row_count`, `null_rates`, schema 정보, freshness status를 포함하는 JSON-serializable `eda_evidence` 구조와 화면 렌더링을 분리한다.
- [ ] 2.5 `observed_at` 기반 source freshness를 측정하고, 없으면 `미측정` callout과 filesystem/Bronze ingestion 경계를 표시한다.

## 3. 검증

- [ ] 3.1 Marimo 노트북을 실행해 sample input의 schema, volume, null, freshness 경계 출력이 렌더링되는지 확인한다.
- [ ] 3.2 required column 누락, null 값, `observed_at` 부재 input의 상태 출력을 확인한다.
- [ ] 3.3 `uv run rumdl fmt openspec/changes/add-hmda-eda-baseline`과 OpenSpec 검증을 실행한다.
