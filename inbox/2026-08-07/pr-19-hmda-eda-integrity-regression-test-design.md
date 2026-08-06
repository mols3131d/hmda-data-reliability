# PR #19 HMDA EDA 무결성·회귀 테스트 설계

**파일명:** `pr-19-hmda-eda-integrity-regression-test-design.md`  
**대상:** HMDA EDA contract, actual-source evidence, readiness artifacts  
**목적:** PR #19에서 확인된 provenance, 집계, 계약 drift, 비원자적 artifact 생성 문제를 재발 방지한다.

## 1. 테스트 원칙

- 공개 contract와 artifact invariant를 우선 검증한다.
- 단위 테스트와 process-level integration test를 분리한다.
- actual-source 데이터가 없는 CI에서도 deterministic fixture로 핵심 경로를 검증한다.
- 실제 source 검증은 별도 controlled job으로 실행한다.
- 생성 artifact는 clean revision, 동일 source fingerprint, 동일 실행에서 파생되어야 한다.

## 2. 품질 게이트

| Gate | 통과 조건 |
| --- | --- |
| Six-core contract | 6개 core column만으로 성공하고 누락·type mismatch는 fail-fast |
| Grain semantics | complete-key distinct count와 null-key coverage가 정확함 |
| Provenance | clean `HEAD`만 허용하고 (`git status --porcelain` 기준), evidence revision이 `HEAD`와 동일함 |
| Artifact consistency | JSON과 Markdown 핵심 지표가 동일함 |
| Atomicity | 두 번째 artifact 작성 실패 등 부분 실패 시 기존 JSON·Markdown pair가 훼손 없이 보존됨 |
| Readiness SSOT | YAML을 단일 원천으로 자동 생성하며, 개별 항목 합계와 Markdown 총계가 일치하고 수동 편집을 차단함 |
| Removed behavior | freshness 관련 query fragment 및 output key가 완전히 제거됨 |
| PR Scope Isolation | HMDA EDA 외 영역(`scripts/` 등 무관한 파일)의 우발적 변경 혼합을 차단함 |
| Expanded Type Families | FLOAT/REAL 및 무부호 정수형(UTINYINT 등) 추론 시 type mismatch 오탐 방지 |
| Code Distribution JSON | code distribution value의 Decimal 포함 객체를 JSON 직렬화 가능 타입으로 보장 |
| Dual Artifact Rollback | 두 번째 아티팩트 atomic swap 실패 시 첫 번째 아티팩트 롤백을 통한 모순 방지 |
| Deterministic Sampling | activity_year 카디널리티 초과 시 2차 정렬(activity_year ASC)로 결정론적 결과 보장 |

## 3. 테스트 매트릭스

### T-01 Six-core 최소 입력

- 입력: `activity_year,state_code,loan_purpose,action_taken,loan_amount,income`
- 기대: 분석 성공, `county_code` 미요구, six-core schema status 모두 valid
- 레벨: component

### T-02 Required column 누락 및 type mismatch

- 누락 fixture와 문자열형 `loan_amount` fixture를 각각 실행한다.
- 기대: `HMDADataValidationError`, partial evidence 미반환
- 레벨: component

### T-03 Complete-key grain

- complete row, 중복 row, 각 grain key가 null인 row를 혼합한다.
- 기대:
  - distinct count는 complete-key 조합만 포함
  - `null_key_rows`는 하나 이상 key가 null인 행 수
  - coverage는 `(row_count-null_key_rows)/row_count`
- 레벨: component

### T-04 Freshness 제거 회귀 (F-03 대응)

- `observed_at` 컬럼을 포함한 fixture를 입력으로 전달한다.
- DuckDB execute spy 또는 SQL AST/query builder 단위 테스트로 `MAX(observed_at)` execution fragment 및 `freshness` 검색어가 생성/실행 SQL에 일절 포함되지 않는지 검증한다.
- 생성 및 반환된 JSON/Markdown evidence 객체 내에 `freshness` 메타데이터 키가 존재하지 않아야 한다.
- 레벨: unit/component

### T-05 Dirty repository 차단 (F-01 대응)

- 기존 `git diff --quiet` 방식의 누락(staged, untracked 감지 불가)을 보완하여 `git status --porcelain` 기준 전체 파일 변경 상태를 검사한다.
- 임시 Git 저장소에서 다음 4가지 상태를 각각 구성 후 실행한다:
  1. clean tree → 정상 진행 및 exact revision 반환
  1. unstaged 수정 존재 → `EvidenceProvenanceError` 발생
  1. staged 수정 존재 → `EvidenceProvenanceError` 발생
  1. untracked 파일 존재 → `EvidenceProvenanceError` 발생
- 레벨: unit/integration

### T-06 Evidence revision 일치 (F-01 대응)

- evidence 생성 직전 `HEAD` commit hash를 구한다.
- 생성된 JSON 및 Markdown 내 `repository_revision`이 `HEAD`와 100% 동일한지 검증한다.
- `-dirty` 접미사가 포함된 값은 절대 허용하지 않고 검증 실패 처리한다.
- 레벨: integration

### T-07 JSON·Markdown 일관성

- JSON에서 row count, income null count, grain distinct count를 읽는다.
- Markdown parser 또는 명시적 marker로 동일 값을 비교한다.
- 절대 source path와 temp path가 두 artifact에 없어야 한다.
- 레벨: component

### T-08 Atomic write 실패 주입 (F-04 대응)

- 기존 정상 artifact pair (JSON + Markdown)가 존재하는 상태를 준비한다.
- 두 번째 artifact (Markdown) 임시 파일 쓰기 또는 `os.replace` 교체 단계에 의도적 I/O 예외를 주입한다.
- 기대: 예외 발생 시 기존 JSON과 Markdown pair가 모두 원본 상태 그대로 100% 보존됨 (부분 교체 방지).
- 두 파일 모두 임시 경로에 정상 생성·검증된 경우에만 atomic swap(`os.replace`)으로 함께 교체되는지 확인한다.
- 레벨: unit/integration

### T-09 Readiness 집계 및 SSOT 회귀 (F-02 대응)

- `readiness.yml`을 단일 원천(SSOT)으로 읽어 각 카테고리(Implementation, Verification 등)의 진행 수를 자동 합산한다.
- `0/0` (미시작/해당 없음) 항목의 총 분모 포함 여부 정책을 명시적 unit assertion으로 고정한다.
- 자동 생성된 Markdown 보고서의 총계(`X/Y`)가 YAML 합산치와 100% 일치해야 한다.
- Markdown 파일을 수동 편집한 경우, CI golden regeneration diff test에서 수동 변경이 검출되어 실패해야 한다.
- 레벨: unit

### T-10 Actual-source controlled job

- 조건: source fixture 또는 승인된 실제 파일 사용 가능 환경
- 실행:
  1. clean checkout 확인 (`git status --porcelain` 이 비어있음)
  1. 테스트·lint 실행
  1. evidence 생성
  1. `git diff --exit-code`로 생성물 최신성 검증
- PR head와 artifact revision이 다르면 실패한다.
- 레벨: CI integration

### T-11 Static chart contract

- activity year와 null baseline이 있으면 정확히 두 HTML 생성
- 빈 section은 파일을 생성하지 않음
- 파일명이 deterministic하고 HTML이 비어 있지 않음
- 출력 디렉터리 밖으로 path traversal이 발생하지 않음
- 레벨: component

### T-12 YAML portability

- YAML을 `yaml.safe_load`로 round-trip한다.
- Python-specific tag, 절대 경로, 비직렬화 객체가 없어야 한다.
- 레벨: unit

### T-13 PR Scope & Ownership Isolation (F-05 대응)

- HMDA EDA 관련 PR diff 내에 EDA 범위를 벗어나는 무관한 스크립트(예: `scripts/wsl-status.sh` 등)나 설정 변경 파일이 포함되어 있는지 검사한다.
- 허용된 파일 패스 패턴 외의 변경이 감지되면 PR scope warning 또는 validation failure를 발생시킨다.
- git diff 실패 시 False Green을 방지하도록 pytest.skip 또는 명시적 warning 처리를 수행한다 (N-02 대응).
- 레벨: integration/CI

### T-14 Expanded Numeric and Integer Type Families (M-01 대응)

- `loan_amount`, `income` 컬럼이 `FLOAT`, `REAL`로 추론되거나 `activity_year`, `action_taken`, `loan_purpose`가 `UTINYINT`, `USMALLINT`, `UINTEGER`, `UBIGINT`로 추론되는 DuckDB 스키마 입력 생성.
- 기대: `HMDADataValidationError` 발생 없이 `status="valid"` 판정 및 분석 성공.
- 레벨: unit/component

### T-15 Code Distribution Value Primitive Casting (M-02 대응)

- `action_taken`, `loan_purpose`, `state_code` 값이 DuckDB에서 `DECIMAL` 또는 비기본 타입으로 반환되는 상황을 시뮬레이션.
- 기대: `_collect_code_distributions` 반환 결과의 `value` 필드가 `json.dumps()` 실행 시 `TypeError` 없이 정상 직렬화됨.
- 레벨: unit

### T-16 Dual Artifact Atomic Replacement & Rollback (M-03 대응)

- `write_evidence` 실행 중 첫 번째 아티팩트(`json_path`) swap 성공 후 두 번째 아티팩트(`markdown_path`) swap 실패를 시뮬레이션.
- 기대: 예외 발생 시 첫 번째 교체된 `json_path`가 롤백되거나 두 파일 모두 이전 상태로 완전 보존되어 일관성이 깨지지 않음.
- 레벨: unit/integration

### T-17 Deterministic Activity Year Sampling (N-01 대응)

- `max_activity_years` 카디널리티 한계를 초과하는 다양한 `activity_year` 수치들을 가진 데이터셋 입력.
- DuckDB GROUPING SETS 쿼리 실행 시 `ORDER BY is_total DESC, activity_year ASC` 2차 정렬 조건 적용 검증.
- 레벨: unit

## 4. 권장 테스트 파일 구조

```text
tests/hmda_data/eda/
├── test_eda_contract.py
├── test_eda_grain.py
├── test_eda_removed_behaviors.py
├── test_eda_explorer.py
├── test_evidence_serialization.py
├── test_evidence_provenance.py
├── test_evidence_atomicity.py
├── test_readiness_generation.py
└── test_scope_isolation.py
```

## 5. CI 단계

```text
lint
  → PR Scope & ownership isolation check
  → focused component tests
  → provenance (`git status --porcelain`) / atomicity integration tests
  → readiness SSOT regeneration & total sum diff check
  → controlled actual-source job
  → git diff --exit-code
```

실제 source job을 실행할 수 없는 PR 환경에서는 상태를 `passing`으로 위장하지 않고 `not_run` 또는 `blocked`로 명시한다.

## 6. 완료 기준

- 모든 blocker(F-01, F-02)와 major finding(F-03, F-04) 및 scope finding(F-05)에 대응하는 실패 재현 테스트가 먼저 추가된다.
- 수정 전 테스트가 실패하고 수정 후 통과해야 한다.
- readiness와 evidence는 수동 복사/수정 없이 YAML SSOT 파이프라인에서 자동 생성된다.
- PR head, source hash, JSON, Markdown 사이에 단일 provenance chain이 성립한다.
