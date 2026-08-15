# Observability

관찰 결과를 나중에 다시 확인할 수 있게 남기는 기준이다.

## 세 가지 근거

- `Evidence`: 무엇을, 어디서, 언제 봤는지
- `ProfileSnapshot`: partition의 row 수, null, schema와 measured/unavailable freshness
- `LineageEvidence`: upstream과 downstream의 연결

## 기준

- asset, partition, source, 관찰 시점을 남긴다.
- fixture 결과와 실제 source 결과를 구분한다.
- 관찰만 하며 remediation이나 recovery를 실행하지 않는다.
- EDA와 ProfileSnapshot은 각각 descriptive context와 detector 입력 지표를 담당한다.
- Freshness measurement가 없으면 `observed_at`으로 대체하지 않고 unavailable로 남긴다.

구현 위치: `src/project_pivot/reliability/contracts/`  
검증 위치: `tests/reliability/`, `tests/hmda_data/eda/`
