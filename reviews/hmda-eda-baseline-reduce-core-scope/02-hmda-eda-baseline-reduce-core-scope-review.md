# Review: hmda-eda-baseline-reduce-core-scope

- **Change**: `hmda-eda-baseline-reduce-core-scope`
- **Date**: 2026-08-06
- **Reviewer**: GitHub Copilot (`review-quality` subagent)
- **Verdict**: **PASS**

## Validations Performed

1. **Core Evidence Contract (`analysis.py`)**
   - `anomalies`, `freshness`, `schema_hash` 및 `county_code` 분포 계산 로직이 제거되었음을 확인했습니다.
   - 6개 핵심 컬럼에 대한 descriptive evidence 반환 여부와 타입 검증을 확인했습니다.
1. **Notebook Rendering (`notebooks/eda_mo.py`)**
   - Marimo 노트북에서 의존성이 사라진 UI 컴포넌트(freshness, profile mapping 등)가 제거되었음을 확인했습니다.
   - Core evidence 계산 결과와 UI 렌더링이 성공적으로 분리되었습니다.
1. **Test Integrity (`tests/hmda_data/eda/`)**
   - 무거운 memory/fixture 기반 테스트 파일들과 스크립트가 의도대로 제거되었습니다.
   - `test_eda.py`에서 제거된 항목의 부재와 API 노출 차단을 검증하는 테스트가 성공적으로 동작합니다.
   - `test_eda_notebook.py`가 서브프로세스를 사용해 valid/malformed 입력에 대한 통합 테스트를 정상 수행합니다.
1. **Documentation & Dashboards**
   - `docs/references/hmda_eda.md`에 1회성 실제 데이터 관측 결과와 제약 사항이 올바르게 기록되었습니다.
   - `readiness.yml` 및 `readiness.md`의 진행 상황이 축소된 스펙을 기준으로 100% 완료 상태로 업데이트되었습니다.

## Findings

### 1. [Style / Minor] Local Imports in Test Functions

- **Location**: `tests/hmda_data/eda/test_eda_notebook.py`
- **Description**: `test_valid_fixture_completes_notebook_rendering` 및 `test_malformed_fixture_reports_notebook_failure` 테스트 함수 내부에 `import os`, `import shutil` 선언이 포함되어 있습니다.
- **Reasoning**: 해당 모듈들은 Python 표준 라이브러리이므로 파일 최상단에서 import 하는 것이 일반적인 파이썬 스타일 가이드에 부합합니다. 로컬 스코프에 있어도 기능적(Defect) 문제는 없으나 일관성을 위해 리팩토링을 권장합니다.

## Remaining Risks

- **관찰된 주요 위험 없음**: 분석 도메인이 명확하게 축소되었고, 불필요한 테스트 부하가 제거되어 시스템 전반의 유지보수성과 안정성이 크게 향상되었습니다. 노트북 통합 테스트 역시 브라우저 실행 없이 동작을 검증하므로 CI 환경에서의 안정성이 확보되었습니다.
