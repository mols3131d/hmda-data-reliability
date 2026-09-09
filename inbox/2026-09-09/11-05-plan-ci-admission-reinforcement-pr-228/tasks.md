# CI Admission Reinforcement Tasks (PR #228)

## 1. Workstream 1: OpenSpec CI Admission

- [x] **1.1 변경 분류기([.github/workflows/classify_changes.sh](../../../.github/workflows/classify_changes.sh)) 갱신**
  - `openspec` 및 `openspec_archived` 감지 로직 및 환경변수 출력 추가
  - `openspec/**` 전체 경로 매핑
- [x] **1.2 분류기 회귀 테스트([tests/test_ci_classifier.py](../../../tests/test_ci_classifier.py)) 보강**
  - `openspec/config.yaml`, `openspec/specs/**`, `openspec/changes/archive/**` 변경 시 플래그 검증 테스트 추가
- [x] **1.3 CI Lite 워크플로([.github/workflows/ci-lite.yml](../../../.github/workflows/ci-lite.yml)) 검증 단계 추가**
  - `Validate OpenSpec` step 추가 (`npx --yes @fission-ai/openspec@1.12.0 validate --all --strict`)
  - 아카이브 변경 시 `openspec validate --archived` 조건부 실행 추가
- [x] **1.4 로컬 Git Hook([lefthook.yml](../../../lefthook.yml)) 연계**
  - `pre-push`에 `openspec-check` 추가

## 2. Workstream 2: Dependency & Runtime CI

- [x] **2.1 의존성 락 무결성 검증 단계 추가**
  - [.github/workflows/ci-lite.yml](../../../.github/workflows/ci-lite.yml)에 `uv lock --check` 추가
- [x] **2.2 패키지 빌드 무결성 검증 단계 추가**
  - [.github/workflows/ci-lite.yml](../../../.github/workflows/ci-lite.yml)에 `uv build --wheel --out-dir /tmp/dist` 추가

## 3. Workstream 3: Verification & Integration

- [x] **3.1 로컬 검증 실행**
  - `uv run pytest tests/test_ci_classifier.py` 실행 및 통과 확인 (44 passed)
  - `bash .github/workflows/classify_changes.sh` 로컬 동작 테스트 통과
  - `inbox` 아티팩트 유효성 검증 (`scripts/validate_inbox_artifacts.py`) 통과
- [ ] **3.2 커밋 및 푸시**
  - 규약 준수 커밋 메시지 작성 후 `agent/ci/openspec-and-dependency-admission`에 푸시
- [ ] **3.3 PR [#228](https://github.com/mols3131d/hmda-data-reliability/pull/228) 설명 갱신 및 검증 결과 반영**
