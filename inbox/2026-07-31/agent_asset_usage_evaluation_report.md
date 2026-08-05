---
title: "Agent Asset 사용 평가 보고서"
description: "HMDA EDA baseline 작업에서 agent asset 선택, instruction 준수, 검증과 완료 hygiene를 평가한 보고서"
date: 2026-07-31
---

# Agent Asset Usage Evaluation Report

## Executive Summary

> [!IMPORTANT]
> 이번 HMDA EDA 작업에서 agent assets는 전반적으로 높은 수준으로 사용되고
> 지켜졌다. 종합 평가는 **8.7/10**이다. 특히 OpenSpec, Marimo code mode,
> Python fact-grounding, testing과 commit hook을 실제 작업 흐름에 연결한 점이
> 강점이다. 다만 초기 OpenSpec CLI 환경 오류, 몇 차례의 임시 경로 실수,
> 첫 구현에서 bounded grouping 순서를 충분히 검증하지 못한 점은 개선 대상이다.

이 보고서는 이번 세션의 대화 기록, 실행 결과, 변경된 code와 validation 결과를
기준으로 agent로서 다음 항목을 평가한다.

- 적절한 asset와 workflow를 선택했는가
- asset의 제약과 routing 지침을 실제 행동에 반영했는가
- 변경 전 사실을 확인하고 변경 후 실행 가능한 검증을 수행했는가
- 오류를 숨기지 않고 원인에 맞게 복구했는가
- 불필요한 탐색, 복잡성, 변경을 얼마나 억제했는가

## Overall Assessment

| Dimension | Score | Assessment |
| --- | ---: | --- |
| Asset routing | 8.5/10 | OpenSpec, Marimo, Python, testing, Markdown과 commit 관련 asset을 대부분 적절히 선택했다. |
| Instruction adherence | 8.5/10 | 한국어, scoped edit, read-first, validation-first 원칙을 대체로 지켰다. 일부 초기 우회가 있었다. |
| OpenSpec workflow | 8.5/10 | Change status, delta sync, strict validation, archive까지 완료했다. CLI 장애 시 manual fallback이 길어졌다. |
| Marimo workflow | 9.5/10 | live kernel을 code mode로 조회·수정·실행했고 notebook 파일 직접 편집을 피했다. |
| Python fact grounding | 9.0/10 | runtime snippet, Pylance facts, focused tests와 hook 결과로 결론을 확인했다. |
| Test and validation discipline | 9.0/10 | 첫 edit 후 좁은 test를 실행했고, 최종에는 domain suite·Marimo·Ruff·ty·OpenSpec을 모두 통과시켰다. |
| Simplicity and scope control | 8.0/10 | 공유 entrypoint와 작은 runner로 책임을 분리했지만 탐색과 반복 smoke가 다소 길었다. |
| Git and completion hygiene | 9.0/10 | selective staging, pre-commit hook 복구, clean commit과 archive를 완료했다. |

### Score Meaning

- `9.0-10.0`: asset가 작업 routing과 검증을 실질적으로 주도함
- `8.0-8.9`: 높은 품질이나 일부 우회 또는 재작업이 있음
- `7.0-7.9`: 핵심 결과는 얻었으나 asset 사용이 부분적임
- `<7.0`: asset가 형식적으로만 적용되거나 검증이 약함

## What Was Done Well

### 1. Applicable assets were loaded before implementation

작업 시작 전에 다음 범주의 asset을 읽었다.

- OpenSpec change implementation workflow
- Marimo notebook authoring과 live-kernel pairing
- Python fact-grounded coding
- Project pytest workflow
- Markdown와 document workflow
- Minimal implementation 판단을 위한 simplicity guidance

이 순서는 “먼저 구현하고 나중에 규칙을 맞추는” 방식이 아니라, 변경 대상과
validation 경계를 먼저 정하는 방식으로 작동했다.

### 2. OpenSpec was treated as the source of behavior

Change의 proposal, design, specification, tasks를 읽고 다음 구현 순서를
세웠다.

1. 작은 characterization test
1. 공유 EDA entrypoint
1. Marimo integration
1. deterministic fixture
1. process-level memory runner
1. 문서와 spec sync
1. archive와 commit

실제로 change는 `33/33` task 완료 상태가 되었고, main spec에 delta를
동기화한 뒤 archive했다. 최종 OpenSpec strict validation은 `17 passed,
0 failed`였다.

### 3. Marimo asset constraints were followed correctly

Notebook이 live kernel과 연결된 상태였기 때문에 notebook 파일을 직접 수정하지
않고 Marimo code mode를 사용했다. 다음 작업이 모두 kernel context에서 수행됐다.

- cell graph와 cell status 조회
- 계산 cell의 code 확인
- 공유 entrypoint 호출로 cell 교체
- cell 실행과 dependency 재실행
- valid fixture와 malformed fixture smoke
- 실행 후 notebook state 복원

이 점은 단순히 파일 내용만 맞춘 것이 아니라, notebook의 reactive graph와
사용자 session state를 보존하려 한 올바른 asset 사용이었다.

### 4. Fact-grounded routing was visible in decisions

추측으로 malformed CSV를 고르지 않고 DuckDB runtime snippet으로 어떤 입력이
확실히 parse failure를 만드는지 확인했다. 닫히지 않은 quote가 DuckDB에서
수용되는 것을 관찰한 뒤 invalid UTF-8 fixture로 test를 바꿨다.

또한 다음 결과는 실제 실행 evidence로 확인했다.

- valid fixture의 schema, null, freshness
- malformed fixture의 `exception` 상태와 partial evidence 제거
- activity-year cardinality bound failure
- normal, parse failure, query failure에서 connection close
- systemd 128 MiB OOM probe의 실제 `oom-kill`
- 5M-row memory workload 3회 결과

### 5. Validation ladder was strong

첫 substantive edit 뒤 바로 좁은 characterization test를 실행했고, 실패가
발생할 때 같은 slice를 고쳤다. 이후 validation을 단계적으로 넓혔다.

- focused EDA tests
- fixture tests와 memory assessment helper tests
- memory worker smoke
- systemd runner 3회 baseline
- full-source observation
- HMDA domain suite
- Marimo check
- Ruff
- `ty check`
- OpenSpec strict validation
- pre-commit hooks

특히 commit hook에서 발견된 DuckDB config type 오류를 우회하지 않고 annotation을
보강해 hook을 통과시킨 점은 asset이 마지막 안전망으로 작동한 사례다.

## Asset-by-Asset Evaluation

### OpenSpec assets

#### OpenSpec usage result: 높음

- Change status와 task progress를 확인했다.
- CLI가 처음 `node` 부재로 실패했을 때 artifact를 직접 읽어 작업을 계속했다.
- 이후 Node runtime을 찾아 CLI status, instructions, strict validation을 실행했다.
- delta spec과 main spec의 차이를 직접 비교했다.
- main spec sync 후 archive directory로 이동했다.
- active change 0개를 확인했다.

#### OpenSpec improvement

초기 `node` 부재를 확인한 뒤 CLI 재시도 경로를 더 일찍 정리할 수 있었다. 또한
archive 전에 sync가 필요한지 판단하는 과정에서 직접 diff와 여러 read를 사용해
조금 길어졌다. 다음에는 초기 환경 probe를 먼저 하고, `status → delta/main
compare → sync → validate → archive` 순서를 한 번에 고정하는 편이 낫다.

### Marimo assets

#### Marimo usage result: 매우 높음

- live kernel을 source of truth로 취급했다.
- notebook file에 직접 patch하지 않았다.
- code mode로 cell edit와 run을 수행했다.
- reactive state가 stale인 상황에서 한 transaction에 모든 동작을 넣지 않고,
  UI value update와 analysis cell run을 분리해 복구했다.

#### Marimo improvement

초기 smoke에서 `ctx.globals`와 UI value의 timing을 잘못 가정해 몇 번의 추가
호출이 필요했다. 향후에는 code mode의 cell 실행과 UI update를 처음부터 별도
단계로 두고, 각 단계 후 status를 확인하면 더 짧아진다.

### Python fact-grounded assets

#### Python usage result: 높음

- Python environment를 먼저 구성했다.
- Pylance runtime snippet으로 DuckDB behavior를 확인했다.
- syntax, type, lint, focused test를 구분했다.
- 함수 signature를 크게 바꾸지 않고 public entrypoint를 추가했다.

#### Python improvement

처음 구현한 `duckdb_config` annotation이 `ty` stub의 정확한 union과 맞지 않아
commit hook에서 늦게 발견됐다. DuckDB type stub을 첫 구현 전에 확인했다면
재시도가 줄었을 것이다.

### Testing assets

#### Testing usage result: 높음

- correctness와 memory workload를 marker로 분리했다.
- 기본 test에서 memory workload를 제외했다.
- parse, query, missing input, source immutability, connection lifecycle,
  cardinality bound를 별도 test로 고정했다.
- helper 판정 로직에 threshold, temp disk, timeout/resource failure test를
  추가했다.

#### Testing improvement

일부 테스트는 구현 후 경계가 드러난 뒤 추가됐다. 특히 grouping 결과 정렬과
manifest ordering은 characterization test에 더 일찍 포함할 수 있었다.

### Markdown and document assets

#### Markdown usage result: 높음

- Markdown formatter와 rumdl check를 실행했다.
- heading hierarchy와 internal link validation을 실행했다.
- 완료 보고서도 BLUF 구조, 표, interpretation boundary와 risk를 포함하도록
  작성했다.

#### Markdown improvement

rumdl 설정에 `MD054` unknown option warning이 반복되었다. 이번 문서 품질에는
영향이 없었지만, repository Markdown tooling 설정 자체의 후속 정리가 필요하다.

### Git and completion assets

#### Git usage result: 높음

- commit convention을 확인했다.
- selective staging을 사용했다.
- pre-commit hook 실패를 수정 후 재실행했다.
- OpenSpec archive와 implementation을 한 commit으로 기록했다.
- 완료 보고서는 별도 documentation commit으로 기록했다.

최종 관련 commit:

- `34e264c` `feat: HMDA EDA 공유 계산과 메모리 검증 추가`
- `36ea300` `docs: HMDA EDA 완료 보고서 추가`

## Adherence Findings

### Explicitly followed

- 작업 전 관련 asset과 project context를 읽었다.
- 변경 전 local hypothesis와 discriminating check를 세웠다.
- `apply_patch`를 사용해 source를 수정했다.
- notebook은 live code mode를 통해 변경했다.
- 첫 edit 이후 좁은 실행 검증을 수행했다.
- 실패 결과를 숨기지 않고 원인별로 수정했다.
- unrelated user change를 되돌리지 않았다.
- commit hook과 strict validation을 우회하지 않았다.
- session 종료 전 report를 남기고 working tree 상태를 확인했다.

### Partial adherence or deviations

| Finding | Impact | Improvement |
| --- | --- | --- |
| OpenSpec CLI가 없는 초기 환경에서 manual artifact reading으로 우회 | 낮음 | 시작 시 Node/CLI availability를 먼저 probe |
| `TMPDIR`가 빈 값인 shell에서 두 번 temporary path가 잘못 구성됨 | 낮음 | shell command에 `${TMPDIR:-/tmp}`를 사용 |
| 첫 grouping query가 DuckDB output order를 충분히 고정하지 못함 | 중간 | bounded aggregate의 ordering invariant를 첫 characterization test에서 고정 |
| `ty` config type이 commit hook에서 늦게 발견됨 | 낮음 | DuckDB stub 또는 `ty check`를 첫 public API edit 직후 실행 |
| Notebook smoke가 UI state timing을 처음에 잘못 다룸 | 낮음 | UI update와 cell run을 처음부터 별도 transaction으로 분리 |
| 전체 탐색과 progress update가 다소 길어짐 | 낮음 | local hypothesis 확정 후 더 빨리 edit로 진입 |

## Scope And Integrity Notes

이번 평가는 agent가 직접 수행한 변경과 validation을 대상으로 한다. 현재
working tree에는 이번 보고서와 무관한 untracked 빈 agent file이 존재할 수
있으므로, 그것은 평가 대상에 포함하지 않았고 수정·삭제하지 않았다.

또한 asset의 “사용”은 단순히 skill 이름을 언급했다는 의미가 아니라 다음 중
하나 이상의 실행 evidence가 있는 경우로만 인정했다.

- 해당 workflow의 지침을 읽음
- 지침에 맞는 tool path를 선택함
- 지침이 요구한 validation을 실행함
- 실패 시 지침의 경계 안에서 복구함

## Final Judgment

이번 작업은 agent assets를 형식적으로 참조한 수준을 넘어 실제 routing, edit,
validation과 recovery에 사용한 사례다. 특히 Marimo live-kernel 경계, OpenSpec
계약, process memory enforcement, pre-commit type check를 실제 행동에 반영한
점은 강하게 평가할 수 있다.

다만 첫 시도부터 모든 경계를 완벽히 포착한 것은 아니다. temp path, DuckDB
ordering, type stub과 UI timing에서 작은 재작업이 발생했다. 이 문제들은 모두
숨기지 않고 실행 결과로 확인한 뒤 수정했으며, 최종 산출물의 검증 상태에는
남아 있지 않다.

**최종 평가: 8.7/10.**

가장 큰 다음 개선은 “첫 구현 직후 `ty check`와 output ordering invariant를
동시에 실행하는 것”이다. 이 두 가지를 앞당기면 현재 수준의 correctness와
asset adherence를 유지하면서 탐색 및 재작업 시간을 줄일 수 있다.
