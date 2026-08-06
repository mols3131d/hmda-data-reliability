---
type: openspec-spec-driven-tdd-tasks
category: tasks
title: "HMDA EDA core scope reduction tasks"
description: "6개 core column EDA, 최소 Notebook과 actual-source evidence로 Foundation 범위를 닫는다."
tasks_completed: 0
tasks_total: 21
---

> [!NOTE]
> Core contract를 먼저 실패로 고정한 뒤 계산·public surface를 축소하고, Notebook·문서·actual-source evidence를 같은 범위로 정렬한다. 기존 extension 삭제와 direct reference 정리는 plan approval 전에 완료됐다.

## Tasks

### 1. Core Evidence Contract

- [x] 1.1 **RED** — EDA contract test를 6개 core type compatibility와 core evidence key 기준으로 변경한다.
  - **Covers:** `HMDA required schema baseline`, `Volume and null baseline`, `Core code distributions`, `Core numeric summaries`, `MVP grain alignment`
  - **Done when:** 현재 구현이 `county_code`, anomaly, freshness, schema hash 또는 null-key grain 차이로 의도한 이유에서 실패한다.

- [x] 1.2 **GREEN** — `analyze_hmda_csv`의 type validation과 반환 evidence를 core contract에 맞춘다.
  - **Done when:** source metadata, duration, observed schema, core type compatibility, volume, null, distributions, numeric summaries와 grouping-key coverage만 반환하고 관련 test가 통과한다.

- [x] 1.3 **REFACTOR** — anomaly, freshness, schema hash와 Profile mapping 계산 경로를 제거하고 read-only·connection close 구조를 단순화한다.
  - **Done when:** 성공·input·parse·query failure test가 유지되고 제거된 helper와 dead code가 없다.

### 2. Fixture And Memory Removal

- [x] 2.1 **RED** — top-level `analyze_hmda_csv` compatibility와 fixture·memory export 제거를 검증하는 import contract test를 작성한다.
  - **Covers:** `Reusable EDA computation boundary`
  - **Done when:** 현재 EDA namespace의 제거 대상 export 때문에 의도한 failure를 확인한다.

- [x] 2.2 **GREEN** — representative fixture·manifest·memory module, runner script와 EDA namespace export를 제거한다.
  - **Done when:** `analyze_hmda_csv`는 기존 top-level path에서 import되고 제거 API는 repository에서 참조되지 않는다.

- [x] 2.3 **REFACTOR** — fixture·memory 전용 test, marker usage와 문서 참조를 제거한다.
  - **Done when:** 기본 test 설정과 남은 EDA test가 삭제된 subsystem을 전제하지 않고 small deterministic source만 사용한다.

### 3. Minimal Notebook

- [x] 3.1 **RED** — `test_eda_notebook.py`의 계획 함수를 valid·invalid subprocess integration test로 전환한다.
  - **Covers:** `Minimal notebook rendering`
  - **Done when:** 현재 불완전한 Notebook graph가 small deterministic source의 valid smoke에서 의도한 이유로 실패한다.

- [x] 3.2 **GREEN** — Notebook의 input, 실행 trigger와 evidence dependency graph를 복구하고 core section을 렌더링한다.
  - **Done when:** valid source가 schema, volume, null, distribution, numeric summary와 grouping-key coverage section을 완료하고 invalid source가 명시적으로 실패한다.

- [x] 3.3 **REFACTOR** — Notebook rendering adapter를 공유 계산과 분리하고 anomaly·freshness·Profile mapping UI를 제거한다.
  - **Done when:** Notebook에 별도 계산 계약이나 제거된 evidence section이 남지 않는다.

### 4. Documentation And Runtime Evidence

- [x] 4.1 `docs/references/hmda_eda.md`를 core metric, 책임 경계와 validation command 기준으로 갱신한다.
  - **Done when:** fixture·memory·freshness·Profile mapping 설명이 제거되고 metric denominator와 limitation이 명확하다.

- [x] 4.2 Foundation EDA·readiness Markdown과 YAML을 축소된 canonical spec에 맞춘다.
  - **Done when:** `docs/development/foundation/eda.md`, `readiness.md`, `readiness.yml`이 상세 contract를 복제하지 않고 같은 완료 범위를 가리킨다.

- [x] 4.3 실제 HMDA source를 한 번 read-only 실행하고 최신 observation을 EDA reference에 기록한다.
  - **Covers:** `Actual-source observation`
  - **Done when:** source identifier, 실행 시각·환경, row count, activity-year 범위, duration, observation과 limitation이 기록된다.

### 5. Validation

- [x] 5.1 Focused EDA component·import·failure-boundary test를 실행한다.
  - **Done when:** 관련 pytest가 모두 통과하고 제거된 memory·stress workload는 실행 대상에 없다.

- [x] 5.2 Notebook static check와 valid·invalid runtime smoke를 실행한다.
  - **Done when:** 종료 가능한 command가 timeout 없이 기대한 status와 output을 반환한다.

- [x] 5.3 변경된 Python, test와 Markdown에 대해 ruff, type diagnostics와 rumdl을 실행한다.
  - **Done when:** 변경 범위의 정적 검사가 통과하거나 환경 제약이 명시된다.

- [x] 5.4 직접 관련된 HMDA ingestion, Gold mart grain과 reliability profile contract regression test를 실행한다.
  - **Done when:** EDA 책임 축소가 인접한 존재 계약, grouping rule과 profile boundary를 깨지 않았음을 확인한다.

### 6. Post-Review Fixes

- [x] 6.1 **REFACTOR** — `test_eda_notebook.py`의 상대 경로 의존성을 `Path(__file__)` 기반 절대 경로로 변경한다.
  - **Done when:** `notebook_path`가 테스트 파일 위치를 기준으로 안전하게 해석된다.

- [x] 6.2 **RED/GREEN** — `test_eda_notebook.py`의 False Green 단언문(`"evidence" in content`)을 제거하고 출력된 HTML에서 `<marimo-error>` 또는 관련 오류 메시지가 없음을 확인하는 등 런타임 오류 부재를 증명하는 방식으로 수정한다.
  - **Done when:** Marimo 소스 코드 임베딩에 속지 않고 렌더링 성공 여부를 확실히 검증한다.

- [x] 6.3 **REFACTOR** — `notebooks/eda_mo.py`의 하드코딩된 `data_is_sample = True` 상수를 `mo.ui.checkbox` 위젯으로 교체한다.
  - **Done when:** UI를 통해 샘플 데이터와 Raw 데이터 간 동적 스위칭이 가능하며 더 이상 도달 불가능한 분기가 존재하지 않는다.

## Self-Review

- [x] 모든 관련 Requirement와 Scenario가 구현 및 테스트에 반영되었는지 확인한다.
- [x] Design의 Decision과 Boundary를 지키면서 중복과 불필요한 복잡성을 제거한다.
- [x] 관련 테스트, 실패 경로와 정적 검사가 통과하는지 확인한다.
- [x] 필요한 문서, 설정과 운영 절차를 갱신한다.
- [x] 알려진 제약과 후속 작업을 명시한다.
