# EDA

EDA는 HMDA를 이해하기 위한 읽기 전용 관찰이다. 데이터를 고치거나 incident를 만들지 않는다.

## 보는 것

- schema와 핵심 column
- 전체 row 수와 `activity_year`별 volume
- null 비율과 freshness
- 핵심 code 분포
- `loan_amount`, `income` 요약과 의심 값
- `activity_year + state_code + loan_purpose` grain

의심 값은 삭제·clipping하지 않고 관찰 결과로만 남긴다.

구현 위치: `src/project_pivot/hmda_data/eda/`  
검증 위치: `tests/hmda_data/eda/`, `notebooks/eda_mo.py`
