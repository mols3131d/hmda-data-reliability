# Dependency and Runtime CI Reinforcement Specification

## 1. 개요

저장소의 의존성(Dependencies), 락파일(Lockfile), 빌드 시스템 및 런타임 환경의 정합성을 보장하기 위한 CI 게이트 보강 사항을 정의합니다.

## 2. 현행 상태 및 문제점

1. **암묵적 락 검증:**
   - 현재 [.github/workflows/ci-lite.yml](../../../.github/workflows/ci-lite.yml)의 `Sync dependencies` 단계는 `uv sync --locked`를 사용하므로 락파일이 불일치하면 실패하지만, 락파일 드리프트가 원인인지 명시적인 진단 단계가 분리되어 있지 않습니다.
   - [pyproject.toml](../../../pyproject.toml)만 수정되고 [uv.lock](../../../uv.lock)이 갱신되지 않은 PR을 사전에 단 1ms 만에 명확히 식별할 수 있는 `uv lock --check` 검증이 누락되어 있습니다.
1. **도구 런타임 버전 비결정성:**
   - [scripts/bootstrap.py](../../../scripts/bootstrap.py) 및 [docs/development/tooling/openspec.md](../../../docs/development/tooling/openspec.md)에서 OpenSpec 패키지가 `@latest`로 참조되어 있어, 향후 브레이킹 체인지 배포 시 CI와 로컬 환경 간 불일치가 발생할 수 있습니다.
   - CI Lite에서는 특정 안정화 버전(`@1.12.0`)을 고정하여 재현성을 보장해야 합니다.

## 3. 보강 설계 (Reinforcement Design)

### 3.1 락파일 드리프트 검증 게이트

`uv sync` 이전에 `uv lock --check`를 명시적으로 실행하여, [pyproject.toml](../../../pyproject.toml)과 [uv.lock](../../../uv.lock)의 100% 동기화 상태를 1ms 내에 확인하고 차단합니다.

```yaml
      - name: Verify dependency lock
        if: steps.scope.outputs.python == 'true'
        run: uv lock --check
```

### 3.2 패키징 및 빌드 시스템 무결성 검증

[pyproject.toml](../../../pyproject.toml)의 `[build-system]` (`uv_build`) 설정 또는 패키지 메타데이터 오류를 조기 검출하기 위해 패키지 빌드 검증을 추가합니다:

```yaml
      - name: Verify package build
        if: steps.scope.outputs.python == 'true'
        run: uv build --wheel --out-dir /tmp/dist
```

- 임시 디렉터리(`/tmp/dist`)에 빌드하여 워크스페이스 오염을 방지합니다.
- 소요 시간은 약 0.3초 내외로 CI 지연을 유발하지 않습니다.

### 3.3 Node 도구 런타임 버전 핀

CI에서 실행되는 외부 Node 도구들은 메이저/마이너 버전을 고정하여 공급망 위험과 런타임 비결정성을 차단합니다:

- Biome: `@biomejs/biome@2` (기존 유지)
- Tombi: `tombi@1` (기존 유지)
- OpenSpec: `@fission-ai/openspec@1.12.0` (신규 고정)

## 4. Failure → Evidence 매핑

| 실패 유형 | 검증 대상 | 검증 명령 | 병합 차단 여부 |
| --- | --- | --- | --- |
| **락파일 드리프트** | [pyproject.toml](../../../pyproject.toml), [uv.lock](../../../uv.lock) | `uv lock --check` | ✅ Blocking |
| **패키지 빌드 결함** | `src/hmda_reliability/`, `pyproject.toml` | `uv build --wheel --out-dir /tmp/dist` | ✅ Blocking |
| **런타임 의존성 불일치** | 전체 Python 패키지 의존성 그래프 | `uv sync --locked` | ✅ Blocking |
