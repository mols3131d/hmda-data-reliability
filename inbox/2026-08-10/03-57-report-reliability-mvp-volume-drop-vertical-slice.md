---
type: report
title: Reliability MVP volume-drop vertical slice 작업 보고서
description: HMDA reliability volume-drop recovery vertical slice의 구현, 검증, 논리별 커밋과 Pull Request 생성 결과를 기록한다.
tags:
  - reliability
  - hmda
  - recovery
  - volume-drop
  - rpi
  - implementation
---

# Reliability MVP 작업 보고서

> [!NOTE]
> 오늘 작업은 `volume_drop` 탐지부터 승인된 recovery와 post-recovery verification까지의 deterministic reliability MVP vertical slice를 구현하고, 논리별 commit과 Pull Request로 전달하는 데 목적이 있었다.

## 결론

- OpenSpec Research → Plan → Apply → Review 흐름을 구현 완료 상태로 정리했다.
- 작업 branch `feat/reliability-mvp-volume-drop-vertical-slice`를 생성하고 논리별 6개 commit으로 분리했다.
- PR [#48](https://github.com/mols3131d/project-pivot/pull/48)을 `main` 대상으로 생성했다.
- 최종 검증은 `uv run pytest` 150 passed, Ruff, `ty`, Markdown validation을 모두 통과했다.
- 현재 working tree는 clean이며, PR은 open 상태다.

## 구현 내용

### HMDA ingestion

- `PartitionContentIdentity`와 `partition_content_identity()`를 추가했다.
- Row order와 volatile ingestion metadata에는 독립적이고, logical value와 duplicate multiplicity에는 민감한 identity를 제공한다.
- `expected_identity`를 partition replacement transaction 내부에서 비교한다.
- stale target은 `HMDAStalePartitionError`로 분류하고 mutation 없이 rollback한다.

### Recovery contract

- immutable `RecoveryProposal`을 추가했다.
- Approval과 실행 request가 exact proposal, candidate identity, before/after identity, validation evidence와 target actions를 공유하도록 했다.
- expected-after state는 overwrite 없이 verification을 재개한다.
- diverged state와 compare-and-replace race는 추가 validation과 approval이 필요한 상태로 차단한다.
- recovery 결과에 mutation state, reconciliation action과 content identity를 포함했다.

### Data Operations

- dbt run을 run-scoped target directory에서 실행하도록 변경했다.
- candidate와 failed run이 shared current artifact를 변경하지 않도록 분리했다.
- validated target artifact pair만 explicit promotion API로 current projection에 승격한다.
- process start failure, timeout, non-zero exit와 artifact failure에 command와 run target path를 포함한 context를 보존한다.
- artifact pair promotion 중 실패하면 last-known-good pair를 복구한다.

### Evaluation

- clean baseline, controlled `volume_drop`, candidate validation, external approval, recovery와 replay를 조합하는 evaluation API를 추가했다.
- post-recovery lifecycle을 다시 실행해 incident resolution을 확인한다.
- file-scoped source provenance와 safety failure false green을 regression test로 고정했다.
- mutation, failure stage, reconciliation과 artifact projection evidence를 evaluation report에 반영했다.

### Documentation and planning

- OpenSpec proposal, design, 5개 capability spec, approved plan review와 tasks를 작성했다.
- `tasks_completed: 25`, `tasks_total: 25`로 완료 상태를 기록했다.
- HMDA, Data Operations, Reliability canonical domain 문서를 구현된 contract에 맞게 갱신했다.

## 논리별 Commit

| Commit | 내용 |
| --- | --- |
| `54c0ab6` | OpenSpec reliability 변경 계획 추가 |
| `79d9da2` | HMDA partition identity와 serialized replacement 추가 |
| `56b0006` | dbt 실행 artifact isolation과 explicit promotion 추가 |
| `09c4ef1` | exact recovery proposal approval binding과 reconciliation 추가 |
| `43bea6a` | deterministic volume-drop recovery evaluation 추가 |
| `2bcf470` | canonical reliability recovery contract 문서화 |

## 검증 결과

| 검증 | 결과 |
| --- | --- |
| `uv run pytest` | 150 passed |
| `uv run ruff check src tests` | 통과 |
| `uv run ty check` | 통과 |
| `uv run rumdl check ...` | 통과 |
| OpenSpec strict validation | valid |
| Workspace diagnostics | 오류 없음 |
| Pre-commit hooks | 각 commit에서 통과 |

Independent quality/adversarial review에서 발견된 artifact pair partial promotion, safety-case false green, failed-run context, file-scope provenance, canonical incident ID와 stale race 분류 문제를 수정하고 focused test로 재검증했다.

## 전달 상태

- Branch: `feat/reliability-mvp-volume-drop-vertical-slice`
- Remote branch: push 완료
- Pull Request: [#48](https://github.com/mols3131d/project-pivot/pull/48)
- Base: `main`
- PR 상태: Open, non-draft
- Working tree: clean

## 후속 작업

- PR #48 review와 CI 결과 확인
- 승인 후 merge 및 OpenSpec change archive 여부 결정
- 필요 시 canonical specs sync와 후속 reliability incident type 범위 검토
