# HMDA EDA OOM 준비성 검토 보고서

- 검토일: 2026-07-31
- 대상: [`notebooks/eda_mo.py`](../notebooks/eda_mo.py)
- 기준: [`Python 데이터 파이프라인 OOM 테스트 가이드`](../docs/references/python-data-pipeline-oom-testing-guide.md)
- 범위: HMDA 원천 CSV를 대상으로 하는 Marimo EDA의 메모리 안정성 검증 준비 상태

## 결론

현재 노트북은 DuckDB 내부 메모리 설정과 기본 EDA 기능을 갖췄지만, 대표 workload가 정해진 **process 전체** 메모리 예산에서 완료됨을 증명하지 못한다. 따라서 현재 상태를 OOM-safe 또는 memory-budget 검증 통과로 표현해서는 안 된다.

특히 기본 입력은 약 4.76 GiB의 전체 CSV이며, DuckDB `memory_limit`만으로 Python·Marimo·native allocation까지 제한되지 않는다. 노트북은 UI smoke 용도로 유지하고, 계산 경로와 memory-budget test를 별도로 구성해야 한다.

## 검토 결과

| 우선순위 | 발견 사항 | 근거 | 영향 | 권고 조치 |
| --- | --- | --- | --- | --- |
| P1 | process-level hard limit, swap 정책, timeout이 없다. | 노트북은 DuckDB `memory_limit="2GB"`와 `threads=2`만 설정한다. | DuckDB 밖의 Python·Marimo·native 메모리가 process 예산을 초과할 수 있다. 성공 또는 실패만으로 OOM 원인을 판단할 수도 없다. | 별도 process를 `systemd-run` 또는 container memory limit으로 실행하고, swap-off와 timeout을 적용한다. DuckDB limit은 process limit보다 낮게 둔다. |
| P1 | memory-budget test와 대표 fixture가 없다. | pytest marker에는 `unit`, `component`, `integration`만 있고, EDA를 호출하는 test가 없다. | 현재 EDA 경로의 예산 준수, 반복 실행 peak RSS, 결과 정확성을 CI에서 검증할 수 없다. | EDA 계산을 일반 Python public entrypoint로 분리한다. 미리 준비한 대표 fixture로 `@pytest.mark.memory` test를 만들고 schema·row count·null·연도별 count invariant를 검증한다. |
| P2 | 집계 결과를 `fetchall()`로 Python heap에 전부 적재한다. | `GROUPING SETS` 결과를 `fetchall()`로 받아 `activity_year_counts`를 만든다. | 정상 HMDA의 연도 cardinality는 작을 것으로 예상되지만, 비정상 입력에서 고유 `activity_year`가 많으면 결과 자체가 메모리 pressure가 된다. | `activity_year`의 허용 범위/cardinality를 계약으로 검증하거나 반환 행 수 상한을 둔다. 대표 fixture에 해당 cardinality를 기록한다. |
| P2 | temp disk와 DuckDB connection lifecycle이 명시적으로 관리되지 않는다. | spill directory가 공용 `TMPDIR`/`/tmp`이고, connection close 경로가 없다. | 반복 실행 중 spill 파일과 native resource 정리 시점이 불명확하며 temp disk 예산을 검증할 수 없다. | 실행별 전용 temp directory를 사용하고, `finally`에서 connection을 닫는다. memory test에서 temp disk 사용량 및 한계를 기록한다. |
| P3 | EDA reference의 입력 계약이 구현과 다르다. | 문서는 다른 fallback 경로와 `ignore_errors=true`를 설명하지만 구현은 full raw path 및 fail-fast다. | 운영자가 문서대로 실행하면 입력 범위와 parse-integrity 기대가 달라진다. | 문서를 구현의 fallback, fail-fast 동작, 전체 파일 실행 비용에 맞춰 정정한다. |

## 기준 대비 현황

| 가이드 기준 | 현황 |
| --- | --- |
| eager full-table materialization 회피 | 부분 충족. 원천은 DuckDB relation/view로 유지하지만 집계 결과에 `fetchall()`을 사용한다. |
| DuckDB 내부 memory limit과 thread 제한 | 충족. `2GB`, 2 threads를 설정한다. |
| process 전체 hard limit | 미충족. |
| swap, timeout, temp disk 정책 | 미충족. |
| representative fixture의 schema·row 폭·skew·cardinality 기록 | 미충족. |
| correctness와 memory-budget test 분리 | 미충족. |
| 결과 schema·row 수·business invariant 검증 | 미충족. 노트북 화면 출력만 존재한다. |
| peak RSS·elapsed time·반복 실행 기록 | 부분 충족. elapsed time만 `eda_evidence`에 저장한다. |
| notebook smoke와 memory gate 분리 | 미충족. |

## 권장 실행 순서

1. EDA의 DuckDB query와 evidence 생성을 일반 Python entrypoint로 추출한다. 노트북은 해당 entrypoint의 입력 UI와 결과 표시만 담당한다.
1. 원천 특성을 반영한 버전 고정 대표 fixture를 측정 구간 밖에서 준비한다. schema, row 수, 문자열 폭, null rate, `activity_year` cardinality, 파일 수를 함께 기록한다.
1. `memory` pytest marker와 별도 CI job을 추가한다. process hard limit, DuckDB/Polars threads, temp directory, timeout을 명시한다.
1. 결과의 schema, row count, required-column null rate, activity-year count, freshness 상태를 검증한다. output이 있을 경우 완료 후에만 검증한다.
1. 동일 fixture로 세 번 실행해 peak RSS 최대값, elapsed time, temp disk 사용량과 실행 환경을 저장한다. 3회 최대 peak가 hard limit의 85%를 넘으면 개선 대상으로 분류한다.

## 검증 증거와 한계

- `uv run python -m py_compile notebooks/eda_mo.py` 통과
- `uv run marimo check notebooks/eda_mo.py` 통과
- 기본 원천 CSV는 `data/raw/hmda/year_2025.csv`이며 크기는 5,114,432,389 bytes(약 4.76 GiB)다.
- 실제 전체 원천 또는 representative fixture에 process hard limit을 적용한 실행은 수행하지 않았다. 따라서 peak RSS, temp disk, timeout, 결과 invariant, OOM 안정성은 미검증이다.

## 범위 경계

이 보고서는 EDA의 메모리 검증 준비성만 다룬다. 원천 데이터 변경, Bronze 적재, dbt 실행, `ProfileSnapshot` 영구화, reliability lifecycle 변경은 포함하지 않는다.
