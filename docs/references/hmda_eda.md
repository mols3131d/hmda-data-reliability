# HMDA Raw EDA

[`notebooks/eda_mo.py`](../../notebooks/eda_mo.py)는 HMDA CSV 원천 파일의 구조와 기본 품질 지표를 읽는 Marimo EDA 노트북이다. 입력 파일과 데이터베이스를 수정하지 않고, 화면과 메모리 내 `eda_evidence`만 생성한다.

## Scope

| Included | Excluded |
| --- | --- |
| CSV schema, 전체 행 수, 컬럼별 null, `activity_year`별 행 수 | 원천 다운로드, Bronze 적재, dbt 실행 |
| 원천 `observed_at` 기준 freshness | incident 판정, remediation, recovery, 장기 모니터링 |
| JSON-serializable EDA evidence | `ProfileSnapshot` 저장 또는 lifecycle 실행 |

Bronze 적재 계약은 [`HMDA Data`](../domains/hmda-data.md), profile과 incident lifecycle은 [`Reliability`](../domains/reliability.md)를 따른다.

## Input

노트북은 `HMDA_EDA_DATA_PATH` 환경 변수의 CSV를 읽는다. 환경 변수가 없으면 코드 fallback은 `data/year_2025_sample.csv`다. 해당 경로는 배포된 샘플 파일을 보장하지 않으므로, 실행 환경에서는 분석할 CSV 경로를 명시한다.

```bash
HMDA_EDA_DATA_PATH=data/raw/hmda/year_2025.csv uv run marimo edit notebooks/eda_mo.py
```

| Item | Value |
| --- | --- |
| Read scope | 파일 전체 |
| CSV header | 사용 |
| Type inference sample | 200,000 rows |
| Null strings | `NA`, 빈 문자열 |
| Parse error handling | `ignore_errors=true` |

`ignore_errors=true`는 파싱 불가 행이 있어도 읽기를 계속한다. 따라서 측정된 행 수와 null 비율은 성공적으로 파싱된 행 기준이며, 원천 파일의 물리적 행 수와 다를 수 있다.

## Measurements

| Area | Output | Meaning |
| --- | --- | --- |
| Schema | 컬럼명, DuckDB inferred type, `schema_hash` | 정렬된 schema payload의 SHA-256 hash |
| Volume | `row_count` | 읽힌 전체 행 수 |
| Partition volume | `activity_year_counts` | `activity_year`가 있을 때 연도별 행 수 |
| Null | `null_counts`, `null_rates` | 각 컬럼의 null 수와 $0$~$1$ 비율 |
| Freshness | `freshness.freshness_at` | `observed_at`가 있을 때 timestamp로 변환 가능한 최대값 |

`activity_year`가 없으면 partition volume은 미측정으로 표시한다. `observed_at`가 없거나 유효한 timestamp가 없으면 freshness는 `unmeasured`이며 값은 `null`이다.

## Freshness Boundary

| Time | Interpretation |
| --- | --- |
| `observed_at` 최대값 | 원천 데이터 관측 시각. 노트북의 source freshness 측정값 |
| 파일 수정 시각 | filesystem metadata. source freshness 아님 |
| Bronze `ingested_at` | 적재 시각. raw-table EDA 경로에서 별도 측정 |

## Evidence Shape

노트북은 다음 구조의 JSON-serializable `eda_evidence`를 accordion으로 표시한다.

```json
{
	"source": {
		"path": "...",
		"scope": "full_file",
		"csv_options": { "header": true, "nullstr": ["NA", ""], "sample_size": 200000, "ignore_errors": true }
	},
	"row_count": 0,
	"activity_year_counts": [],
	"null_counts": {},
	"null_rates": {},
	"schema": { "columns": [], "schema_hash": "sha256:..." },
	"freshness": { "status": "measured|unmeasured", "source_column": "observed_at|null", "freshness_at": "timestamp|null" }
}
```

`source.path`는 실행 환경의 입력 경로다. evidence는 저장된 profile이나 production 결과가 아니라, 해당 실행의 원천 탐색 기록이다.

## Profile Mapping

`eda_evidence`는 `ProfileSnapshot`과 일부 측정값 이름을 공유하지만, 그 자체로 contract를 만족하지 않는다.

| EDA evidence | `ProfileSnapshot` field | Note |
| --- | --- | --- |
| `row_count` | `row_count` | 직접 사용 가능 |
| `null_rates` | `null_rates` | 직접 사용 가능 |
| `schema.schema_hash` | `schema_hash` | 직접 사용 가능 |
| `freshness.freshness_at` | `freshness_at` | `unmeasured`이면 contract용 값 없음 |

`ProfileSnapshot`에는 위 측정값 외에 `snapshot_id`, `asset_name`, `partition`, `observed_at`, `freshness_at`가 필요하다. lifecycle 비교는 raw DuckDB table에서 `ProfileSnapshotRequest`를 통해 별도로 생성한다.
