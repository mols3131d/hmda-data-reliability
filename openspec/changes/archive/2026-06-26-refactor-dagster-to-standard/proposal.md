## Why

현재 Dagster 모듈은 MVP pipeline 실행은 가능하지만, Dagster UI에서 데이터 파이프라인 상태를 읽기에는 정보가 부족합니다. Asset은 `dict`를 반환하고, Bronze/Silver/Gold/Control 경계와 실행 metadata가 UI에 충분히 드러나지 않습니다.

또한 Dagster 표준 실행 환경은 `dagster-webserver`와 `dg` CLI 호환성을 전제로 하므로, 로컬 UI 기동과 asset materialization 검증을 명확히 문서화해야 합니다.

## What Changes

- **Dagster 표준 asset 표면 개선**: asset에 group, dependency, metadata를 명시해 Dagster UI에서 레이어별 상태를 확인할 수 있게 합니다.
- **실행 로직 경계 유지**: DuckDB 적재, dbt 실행, incident lifecycle 핵심 로직은 기존 `pipeline` 및 `reliability` 모듈에 둡니다.
- **설정 구조 단순화**: Dagster 실행 설정은 typed config/resource 중 더 단순한 방식으로 정리합니다.
- **검증 환경 정리**: `dagster-webserver` 의존성과 `dagster dev` 실행 경로를 보장합니다.

## Capabilities

### New Capabilities

- `standard-dagster-orchestration`: Dagster 표준 방식의 asset 정의, metadata 노출, 로컬 UI 실행 환경을 제공합니다.

### Modified Capabilities

- 없음

## Impact

- `src/project_pivot/orchestration/dagster/` 하위 파일 리팩토링
- Dagster asset metadata와 dependency 정의 변경
- Dagster orchestration 테스트 수정
- 필요 시 `pyproject.toml` 및 `tool.dg` 설정 확인
