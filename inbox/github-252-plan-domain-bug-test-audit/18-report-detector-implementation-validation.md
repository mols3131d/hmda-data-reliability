---
type: report
title: Detector Implementation And Validation
description: PR 252의 마지막 detector 수정에 대한 test-first 실패·성공, 영향 검증과 독립 리뷰 근거를 기록합니다.
tags:
  - reliability
  - testing
---

# Detector Implementation And Validation

## Active Scope

[규칙별 결정](17-report-detector-contract-cases.md)과 [Change](../../openspec/changes/reliability-detection-positive-degradation/)를 따른다. Source 시작점은 `61900aad`이며 기존 네 단위는 보존한다. 비결정적 품질 평가는 제외한다. 기존 5/30 loop 이후 여섯 번째 구현 loop를 진행 중이다.

## Test-First Evidence

Production 수정 전 새 test를 working tree에 추가하고 아래 명령을 실행했다.

```bash
.venv/bin/python -m pytest tests/reliability/test_basic_incident_detection.py -q --tb=short
```

결과는 **13 failed / 14 passed**, 0.37s다. 모든 실패는 실제 반환 incident 목록의 assertion에서 발생했다. 무변화의 volume/null 두 오경보, 한 규칙만 악화됐을 때 다른 경보 혼입, zero-row baseline의 null 오경보, schema/freshness 결과의 오경보 혼입 및 column별 독립성을 검출했다. Positive threshold equality와 실제 양의 악화는 이미 통과했다.

Tach plugin은 새 테스트가 impact selection에서 빠질 수 있다고 경고했으나 이 실행에는 `--tach`를 사용하지 않았고 27개를 모두 실행했다. 전체 검증도 이 필터에 의존하지 않는다.

## Current Checkpoint

Volume/null 두 분기에 `<= 0` 제외 조건을 추가했다. 양수 threshold 비교·schema·freshness의 실행 로직은 유지했고 설명과 canonical Spec을 일치시켰다. Threshold 설정 형태와 공개 API는 그대로다.

Focused GREEN 명령은 위 module에 `tests/reliability/test_quality_gate.py`를 함께 지정했으며 **39 passed**, 0.30s다. 새 회귀 18개와 기존 기본 탐지 9개, 기존 quality gate 12개를 포함한다.

## Broader Validation

| Check | Result |
| --- | --- |
| Full non-resource suite, separate DAGRun excluded | 944 passed / 2 skipped, 36.73s; `pytest --ignore=tests/orchestration/test_airflow_dagrun.py -q -ra -n 2` |
| Ruff | 변경한 Python 3개 lint 및 format 통과 |
| Types and module boundaries | repository-wide `ty check`, `tach check` 통과; AST/negative-path 회귀는 전체 suite에 포함 |
| Wheel | 기존 환경의 offline wheel build 성공 |
| OpenSpec | `validate --all --strict --no-interactive`: 21 passed / 0 failed; Apply 1/1, all_done |
| Editor diagnostics | 변경한 Python 3개 오류 없음 |

Skip은 실제 zizmor audit cache prerequisite와 Windows npm/Node prerequisite 각 1건이다. 전체 suite에서 impact selection filter를 사용하지 않았다.

다음은 현재 별도로 실행 중인 실제 Airflow DAGRun 5개, 진행 중인 독립 review-lead assessment와 최종 base/head CI를 확인하는 것이다. 이 checkpoint에서는 전체 PR 완료를 선언하지 않는다.
