# OpenSpec CI Admission Specification

## 1. 개요

OpenSpec 규격(`openspec/specs/**`), 작업 제안(`openspec/changes/**`), 스키마(`openspec/schemas/**`), 설정 파일([openspec/config.yaml](../../../openspec/config.yaml))의 변경이 `main` 브랜치로 병합되기 전에 유효성을 결정론적으로 검증하는 CI 게이트를 정의합니다.

## 2. 변경 감지 (Classifier) 설계

### 2.1 [.github/workflows/classify_changes.sh](../../../.github/workflows/classify_changes.sh)

- **신규 플래그:**
  - `openspec`: OpenSpec 트리 내 모든 파일의 변경 여부 (`true` / `false`)
  - `openspec_archived`: `openspec/changes/archive/**` 하위 파일 변경 여부 (`true` / `false`)

- **분류 로직:**

  ```bash
  case "$path" in
    openspec/changes/archive/*)
      openspec=true
      openspec_archived=true
      ;;
    openspec/*)
      openspec=true
      ;;
  esac
  ```

- **출력 추가 (`write_outputs`):**

  ```bash
  echo "openspec=$openspec"
  echo "openspec_archived=$openspec_archived"
  ```

## 3. CI Lite 워크플로 단계 ([.github/workflows/ci-lite.yml](../../../.github/workflows/ci-lite.yml))

- **배치 위치:** `Set up Python` 이전 또는 마크다운 단계 직후
- **조건:** `steps.scope.outputs.openspec == 'true'`
- **실행 명령:**

  ```yaml
      - name: Validate OpenSpec
        if: steps.scope.outputs.openspec == 'true'
        env:
          ARCHIVED: ${{ steps.scope.outputs.openspec_archived }}
        run: |
          npx --yes @fission-ai/openspec@1.12.0 validate --all --strict
          if [[ "$ARCHIVED" == 'true' ]]; then
            npx --yes @fission-ai/openspec@1.12.0 validate --archived
          fi
  ```

- **특징:**
  - `ubuntu-latest`에 내장된 Node.js/npm 환경을 활용하여 별도 액션 설치 없이 즉시 실행
  - 버전 고정(`@1.12.0`)으로 실행 일관성 및 재현성 확보
  - 전수 검증 소요 시간 약 1.5~2.0초로 CI 오버헤드 최소화

## 4. 로컬 Git Hook 연계 ([lefthook.yml](../../../lefthook.yml))

푸시 시점에 로컬에서 사전 오류를 포착할 수 있도록 `pre-push`에 경량 훅을 추가합니다:

```yaml
pre-push:
  commands:
    openspec-check:
      glob: "openspec/**"
      run: npx --yes @fission-ai/openspec@1.12.0 validate --all --strict
```

## 5. 회귀 테스트 ([tests/test_ci_classifier.py](../../../tests/test_ci_classifier.py))

다음 시나리오를 단위 테스트로 추가하여 분류 로직의 회귀를 방지합니다:

1. `openspec/config.yaml` 변경 시 `openspec == true`, `openspec_archived == false`
1. `openspec/specs/orchestration-pipeline/spec.md` 변경 시 `openspec == true`
1. `openspec/changes/archive/2026-08-26-data-operations-rename-runtime-settings/tasks.md` 변경 시 `openspec == true`, `openspec_archived == true`
1. 일반 Python 또는 문서 파일 변경 시 `openspec == false` 유지
