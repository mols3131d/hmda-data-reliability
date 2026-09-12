---
type: note
title: "Out-of-Scope Issues and Technical Debt Observations"
description: "각 도메인별 코드 이해 리팩터링 및 조사 과정에서 발견되었으나, 동작 보존 불변식에 따라 현재 작업에서 격리하여 인박스에 기록하는 잠재적 결함, 안전성 이슈 및 구조적 부채 목록"
tags:
  - observations
  - issues
  - technical-debt
---

# Out-of-Scope Issues and Technical Debt Observations

이 문서는 `refactor/code-comprehension-clarification` 작업 중 발견된 **범위 외(Out-of-Scope) 중요 문제, 잠재적 버그, 안전성/무결성 위험 및 아키텍처 부채**를 안전하게 격리하여 기록하는 공간이다.

현재 작업은 "기능 및 동작 보존(Preservation of Observable Behavior)"을 절대 규칙으로 하므로, 여기에 기록된 항목들은 현재 리팩터링에서 임의로 수정하지 않고 추후 별도의 변경 단위(이슈 또는 전용 PR)로 해결하도록 권고한다.

## Issue Entry Template

새로운 이슈를 발견할 때마다 아래 템플릿 형식으로 누적 기록한다.

```markdown
### [ISSUES-<도메인>-<번호>] <이슈 제목>
- **위치**: [<파일 경로>](<파일 경로>#L<라인>)
- **분류**: Bug / Safety / Architecture Debt / Contract Mismatch
- **발견 도메인**: `<domain_name>`
- **현상 및 잠재적 영향**:
  - <구체적인 현상 설명>
  - <영향도 및 도달 가능한 실패 경로(Reachable Failure)>
- **현재 작업에서 격리한 이유**:
  - <동작 보존 원칙 및 리팩터링 범위 제외 사유>
- **권장 후속 조치**:
  - <별도 이슈 생성, 독립 브랜치/PR 제안 등>
```

---

## Logged Issues

### [ISSUES-data_platform-01] `artifact_projection_lock`의 Shared Reader 락 획득 시 쓰기 모드(`"w"`) 파일 오픈

- **위치**: [src/hmda_reliability/data_platform/artifacts.py](../../src/hmda_reliability/data_platform/artifacts.py#L52)
- **분류**: Safety / Bug
- **발견 도메인**: `data_platform`
- **현상 및 잠재적 영향**:
  - `artifact_projection_lock(directory, exclusive=False)`는 공유 읽기 락(`fcntl.LOCK_SH`)을 목적으로 하지만, 락 파일 오픈 시 항상 `lock_file = (directory / ".artifact-promotion.lock").open("w")`로 쓰기 모드(`O_WRONLY | O_CREAT | O_TRUNC`)를 사용함.
  - 여러 프로세스가 동시 reader 락을 획득하려 할 때 락 파일을 반복해서 truncate하게 되며, 파일시스템 또는 디렉토리가 읽기 전용 권한인 환경에서는 reader 락 요청임에도 `PermissionError`가 발생할 위험이 있음.
- **현재 작업에서 격리한 이유**:
  - 동작 및 파일 오픈 모드 변경(`"a"` 또는 `os.O_RDWR` 등으로의 전환)은 런타임 권한 및 파일 생성 동작을 변경할 수 있으므로, 비기능적 코드 이해 리팩터링 범위를 벗어남.
- **권장 후속 조치**:
  - 추후 별도 버그 수정 PR에서 `exclusive=False`일 때 읽기 전용/추가 모드 오픈 또는 `os.open` 플래그를 분기하도록 패치 검토.

### [ISSUES-data_platform-02] `artifact_projection_id`의 `data_platform` 단위 테스트 누락

- **위치**: [tests/data_platform/test_artifacts.py](../../tests/data_platform/test_artifacts.py#L1-L60)
- **분류**: Test Coverage Debt
- **발견 도메인**: `data_platform`
- **현상 및 잠재적 영향**:
  - [src/hmda_reliability/data_platform/artifacts.py](../../src/hmda_reliability/data_platform/artifacts.py#L24-L39)에 정의된 `artifact_projection_id`는 길이 프리픽스 기반 해싱이라는 핵심 암호학적 불변식을 소유하고 있으나, 정작 자체 단위 테스트 파일인 [tests/data_platform/test_artifacts.py](../../tests/data_platform/test_artifacts.py)에는 락 관련 테스트 3개만 존재하고 `artifact_projection_id`의 직접 단위 테스트가 없음 (하류 `test_dbt_runner` 등에서만 간접 검증).
- **현재 작업에서 격리한 이유**:
  - 새 테스트 스위트 설계 및 추가는 `mols-clarify-runtime` 및 `mols-code-comprehension-refactor`의 범위를 벗어나며(테스트 설계/품질 책임), 기능 변경을 수반하지 않는 현재 목표와 분리함.
- **권장 후속 조치**:
  - 추후 테스트 보강 작업 시 두 아티팩트의 순서 보존, 길이 프리픽스 충돌 방지, `ArtifactProjectionReadError` 예외 발생 케이스를 검증하는 단위 테스트 추가 권고.

### [ISSUES-hmda_data-01] `_replace_partition_rows`의 위치 기반(Positional) INSERT로 인한 컬럼 순서 불일치 위험

- **위치**: [src/hmda_reliability/hmda_data/ingestion/partition.py](../../src/hmda_reliability/hmda_data/ingestion/partition.py#L393-L400)
- **분류**: Safety / Bug
- **발견 도메인**: `hmda_data`
- **현상 및 잠재적 영향**:
  - `_replace_partition_rows`에서 타겟 파티션 행을 교체할 때 `INSERT INTO {target} SELECT * FROM {_STAGING_TABLE}`을 실행함.
  - DuckDB의 `INSERT INTO ... SELECT *`는 컬럼 목록이나 `BY NAME` 절이 지정되지 않으면 SQL 표준에 따라 위치(positional) 기반으로 컬럼을 매핑함.
  - `preserve_source_metadata=False`인 일반 파티션 적재의 경우 스테이징 테이블의 컬럼 순서는 전달된 파일의 컬럼 순서에 따라 결정되므로, 만약 타겟 Bronze 테이블이 다른 컬럼 순서로 이미 생성되어 있다면 데이터가 잘못된 컬럼에 삽입되거나 타입 변환 오류가 발생할 수 있음.
- **현재 작업에서 격리한 이유**:
  - `INSERT INTO ... BY NAME SELECT *` 또는 명시적 컬럼 프로젝션으로의 전환은 실행 SQL 문법 및 실행 계약을 변경할 수 있으므로, 비기능적 코드 이해 리팩터링 범위를 벗어남.
- **권장 후속 조치**:
  - 추후 별도 버그 수정 PR에서 파티션 삽입 시 DuckDB의 `BY NAME` 절을 사용하거나 타겟 테이블 컬럼 순서에 맞춘 명시적 `SELECT` 프로젝션을 적용하도록 패치 검토.

### [ISSUES-hmda_data-02] `load_hmda_loans`의 필수 컬럼 검증 실패 시 불완전한 타겟 테이블 잔존

- **위치**: [src/hmda_reliability/hmda_data/ingestion/full_load.py](../../src/hmda_reliability/hmda_data/ingestion/full_load.py#L58-L62)
- **분류**: Safety / Architecture Debt
- **발견 도메인**: `hmda_data`
- **현상 및 잠재적 영향**:
  - `load_hmda_loans`는 `_create_hmda_loans_table`을 통해 `CREATE OR REPLACE TABLE`을 먼저 수행한 후 `validate_required_columns`를 호출함.
  - 원천 파일에 필수 컬럼이 누락된 경우 `HMDADataValidationError`가 발생하지만, 이미 타겟 테이블은 불완전한 스키마로 교체된 채 남게 됨 (이전 유효 데이터 유실 및 Bronze 테이블 손상 상태 잔존).
  - 현재 단위 테스트(`test_load_hmda_loans_validates_required_columns`) 역시 실패 후 불완전한 테이블이 남아 있음을 명시적으로 단언하고 있어 기존 계약으로 고정되어 있음.
- **현재 작업에서 격리한 이유**:
  - 파티션 적재와 같은 스테이징 검증 후 교체(stage-and-swap) 방식으로의 변경은 기존 테스트 단언을 깨뜨리고 관찰 가능한 테이블 교체 라이프사이클을 변경하므로, 동작 보존 원칙에 따라 코드 수정을 수행하지 않음.
- **권장 후속 조치**:
  - 추후 아키텍처 개선 PR에서 전체 적재도 스테이징 테이블 검증을 통과한 경우에만 최종 타겟을 교체하는 트랜잭션/임시 테이블 패턴 도입 검토.

### [ISSUES-data_operations-01] `run_incident_lifecycle`의 동일 Reader Lock 중첩 획득 및 락 범위 분리

- **위치**: [src/hmda_reliability/data_operations/incident_lifecycle.py](../../src/hmda_reliability/data_operations/incident_lifecycle.py#L97-L104)
- **분류**: Safety / Architecture Debt
- **발견 도메인**: `data_operations`
- **현상 및 잠재적 영향**:
  - `run_incident_lifecycle()` 내에서 이미 `with artifact_projection_lock(request.dbt_manifest_path.parent, exclusive=False):` 블록을 통해 shared reader 락을 획득하고 있는 상태에서, 블록 내부에서 호출되는 `_dbt_projection_id(request)`가 동일한 락 파일에 대해 다시 `with artifact_projection_lock(..., exclusive=False):`을 재진입(중첩 획득)함.
  - Linux `fcntl.flock`은 파일 디스크립터 기준이므로 동일 프로세스 내 별도 FD 오픈 시 중첩 lock이 허용되기는 하나, 중첩 스코프 종료 시 내부 lock의 `LOCK_UN` 및 파일 닫기로 인해 리소스 해제 순서가 불투명해지고 잠재적 race condition 및 파일 잠금 의미론적 혼란을 유발함.
  - 또한 `target_content_identity`를 계산하는 DuckDB 호출은 artifact lock 블록 외부로 분리되어 있어, dbt 아티팩트와 DuckDB 상태 사이의 원자적 일관성 창이 분리되어 있음.
- **현재 작업에서 격리한 이유**:
  - `_dbt_projection_id`의 독립 함수 시그니처나 락 획득 책임을 변경하는 것은 `_dbt_projection_id`를 재사용하거나 향후 개별 호출하는 계약 및 에러 발생 순서(예: `ArtifactProjectionLockError` 컨텍스트)에 영향을 줄 수 있어, 비기능적 코드 이해 리팩터링 범위를 벗어남.
- **권장 후속 조치**:
  - `_dbt_projection_id`가 이미 락이 획득된 컨텍스트를 지원하도록 매개변수를 분리하거나, 락 획득 책임의 계층을 단일화하는 전용 안전성 리팩터링 검토.

### [ISSUES-data_operations-02] `_create_run_target`에서 생성된 임시 디렉토리의 생애주기 관리 부재(정리 누락)

- **위치**: [src/hmda_reliability/data_operations/runner.py](../../src/hmda_reliability/data_operations/runner.py#L312-L318)
- **분류**: Architecture Debt / Operational
- **발견 도메인**: `data_operations`
- **현상 및 잠재적 영향**:
  - `runner.py`의 `_create_run_target(target_root)`는 `tempfile.mkdtemp(prefix="run-", dir=target_root)`를 사용하여 실행마다 고유한 `run-XXXXXX` 디렉토리를 생성함.
  - 생성된 run 디렉토리는 dbt 산출물(`manifest.json`, `run_results.json`)을 보관하고 이후 `promote_dbt_artifacts`가 호출되기 전까지 보존되어야 하므로 run 종료 즉시 삭제되지 않음.
  - 그러나 승격이 완료된 후나 실패한 빌드, 또는 승격되지 않고 버려진 candidate 빌드 디렉토리를 정리(reap/cleanup)하는 보존 정책이나 가비지 컬렉션 메커니즘이 존재하지 않아, 장기 실행 시 `dbt/target/runs/` 디스크 공간이 지속적으로 누적되는 operational 부채가 존재함.
- **현재 작업에서 격리한 이유**:
  - candidate 디렉토리의 수명 주기 정책(보존 기간, 정리 시점 등)은 시스템 사양 및 운영 요구사항에 따른 새로운 기능적 설계가 필요하며 기존 동작 보존 원칙을 유지하기 위해 격리함.
- **권장 후속 조치**:
  - 추후 dbt run artifact에 대한 TTL 기반 정리 작업이나 백그라운드 cleanup 유틸리티 도입 검토.

### [ISSUES-scripts-01] `rulesync.py`의 `_check_claude_bridges`에서 stale 및 mismatched bridge 로그 메시지 중복 표기

- **위치**: [scripts/rulesync.py](../../scripts/rulesync.py#L125-L128)
- **분류**: Bug / Minor Observability
- **발견 도메인**: `scripts` & shared (Group A)
- **현상 및 잠재적 영향**:
  - `_check_claude_bridges()` 내에서 고아 브리지(`stale`)와 내용 불일치 브리지(`mismatched`)를 출력할 때, 두 루프 모두 `"stale Claude AGENTS.md bridge: ..."`라는 동일한 문자열 프리픽스를 출력함.
  - 미리보기 함수(`_preview_claude_bridges`)에서는 각각 `"would remove Claude AGENTS.md bridge:"`와 `"would update Claude AGENTS.md bridge:"`로 명확히 분기되어 있으나, check 함수에서는 내용 불일치(mismatched) 항목도 stale로 오인되어 잘못된 운영 정보를 전달함.
- **현재 작업에서 격리한 이유**:
  - CLI 표준 출력 문자열 변경은 해당 출력을 파싱하거나 검사하는 외부 스크립트/테스트가 있을 경우 관찰 가능한 인터페이스 변경이 될 수 있으므로, 기능 및 동작 보존 원칙에 따라 격리함.
- **권장 후속 조치**:
  - 추후 `mismatched` 루프의 출력 메시지를 `"mismatched Claude AGENTS.md bridge: ..."` 또는 `"outdated Claude AGENTS.md bridge: ..."`로 정정하는 패치 제안.

### [ISSUES-scripts-02] `generate_agent_routes.py`의 `find_local_skill_files` git 실패 시 상대 경로 불일치 위험

- **위치**: [scripts/generate_agent_routes.py](../../scripts/generate_agent_routes.py#L322-L334)
- **분류**: Safety / Contract Mismatch
- **발견 도메인**: `scripts` & shared (Group A)
- **현상 및 잠재적 영향**:
  - `git ls-files` 정상 실행 시 `REPO_ROOT / line.strip()`으로 절대 `Path` 목록을 반환함.
  - 그러나 예외 폴백(`subprocess.CalledProcessError` 등) 발생 시 `SKILLS_ROOT.glob("*/SKILL.md")`를 반환하는데, `SKILLS_ROOT`는 `REPO_ROOT / ".rulesync" / "skills"`이므로 절대 경로임.
  - 만약 호출자가 `relative()` 함수를 거치지 않고 직접 `path`의 타입을 사용하거나 경로 형식을 가정할 경우, 환경에 따라 파일 리스트의 경로 양식이 달라질 수 있는 잠재적 불일치가 존재함.
- **현재 작업에서 격리한 이유**:
  - 기존 폴백 코드의 반환 형식을 변경하는 것은 동작 보존 범위를 벗어나며 현재 테스트에서 이미 폴백 경로가 격리 검증되고 있으므로 격리함.
- **권장 후속 조치**:
  - Git 및 파일시스템 탐색 결과의 경로 타입을 항상 명시적 절대경로 또는 `REPO_ROOT` 기준 상대경로로 일관되게 정규화하도록 추후 패치 검토.

### [ISSUES-runtime_ai-01] `_sanitize_base_url`의 넷록 내 사용자 인증정보(`user:pass@`) 미제거 위험

- **위치**: [src/hmda_reliability/runtime_ai/settings.py](../../src/hmda_reliability/runtime_ai/settings.py#L13-L19)
- **분류**: Safety / Bug
- **발견 도메인**: `runtime_ai`
- **현상 및 잠재적 영향**:
  - `_sanitize_base_url(url: str)`은 독스트링상 "사용자 정보 또는 쿼리 파라미터가 제거된 정규화된 기본 URL을 반환한다"고 선언하지만, 실제 구현은 `parsed.netloc` 전체를 그대로 `urlunsplit`에 전달함.
  - 파이썬 `urllib.parse.urlsplit`에서 `netloc`은 `username:password@hostname:port` 형태의 사용자 인증정보를 포함하므로, 만약 잘못된 URL이 전달될 경우 사용자 자격 증명이 제거되지 않고 그대로 반환될 수 있음.
  - 현재는 [src/hmda_reliability/runtime_ai/settings.py](../../src/hmda_reliability/runtime_ai/settings.py#L37-L40)의 `_validate_base_url` 검증자에서 `value.username` 또는 `value.password`가 존재할 경우 `ValueError`를 발생시켜 Pydantic 레벨에서 차단하고 있으므로 런타임상 누출되지는 않으나, `_sanitize_base_url` 독립 함수 자체로는 자격 증명을 제거하지 못하는 계약 불일치가 존재함.
- **현재 작업에서 격리한 이유**:
  - `RuntimeAISettings.model_validate`가 이미 자격 증명이 포함된 URL 입력을 금지하고 있어 기존 계약상 안전하며, `_sanitize_base_url`의 내부 파싱 동작 변경은 IPv6 호스트 처리 등 미묘한 URL 재조합 계약에 영향을 줄 수 있으므로 비기능적 리팩터링 범위에서 제외함.
- **권장 후속 조치**:
  - 추후 별도 보안/버그 패치 PR에서 `_sanitize_base_url` 구현 시 `parsed.netloc` 대신 `parsed.hostname` 및 `parsed.port`를 사용하여 자격 증명을 물리적으로 배제하는 정규화 로직으로 강화 검토.

### [ISSUES-runtime_ai-02] `_OpenAIChatCompletionTransport`의 HTTP 429(Rate Limit) 재시도 제외 위험

- **위치**: [src/hmda_reliability/runtime_ai/provider.py](../../src/hmda_reliability/runtime_ai/provider.py#L225-L236)
- **분류**: Contract Mismatch / Resilience Debt
- **발견 도메인**: `runtime_ai`
- **현상 및 잠재적 영향**:
  - `APIStatusError` 처리 시 `is_server_error = error.status_code >= 500`으로만 판단하여 `retryable=is_server_error`로 플래그를 설정함.
  - HTTP 429(`RateLimitError` / Too Many Requests)는 4xx 계열이므로 `provider_client_error`로 분류되고 `retryable=False`가 됨.
  - 이로 인해 LLM 제공자의 일시적 초당 요청 수 제한(Rate limit) 발생 시, 어댑터에 설정된 지수 백오프 재시도 기회를 활용하지 못하고 즉시 1회 시도만에 `ProviderUnavailableError`로 실패하게 됨.
- **현재 작업에서 격리한 이유**:
  - 429를 retryable로 전환하는 것은 재시도 루프 횟수, 대기 시간, 로깅 및 예외 처리 정책 등 관찰 가능한 런타임 재시도 동작을 변경하는 동작 변경(Behavior Change)이므로, 동작 보존 원칙에 따라 리팩터링 범위에서 제외함.
- **권장 후속 조치**:
  - 추후 LLMOps/안정성 개선 PR에서 HTTP 429 상태 코드에 대해 `retryable=True` 및 `Retry-After` 헤더 기반 지연 전략을 지원하도록 별도 이슈로 추진 권고.
