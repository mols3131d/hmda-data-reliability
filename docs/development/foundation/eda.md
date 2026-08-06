# EDA

EDA는 HMDA를 이해하기 위한 읽기 전용 관찰이다. 데이터를 고치거나 incident를 만들지 않는다.

## 보는 것

- 6개 core column의 schema와 type compatibility
- 전체 row 수와 `activity_year`별 volume
- core column null 비율
- `state_code`, `loan_purpose`, `action_taken` 분포
- `loan_amount`, `income` 수치 요약
- complete-key `activity_year + state_code + loan_purpose` coverage

`county_code`, freshness, anomaly, profile mapping과 resource budget은 이 EDA의 책임이 아니다. 결과는 YAML로 직렬화하거나 독립 HTML chart로 내보낼 수 있으며, actual-source observation은 JSON에서 Markdown을 파생한다.

구현 위치: `src/project_pivot/hmda_data/eda/`  
검증 위치: `tests/hmda_data/eda/`, `scripts/run_actual_source.py`
