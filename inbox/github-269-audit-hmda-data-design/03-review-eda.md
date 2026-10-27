---
type: review
title: HMDA EDA Test Design Audit
description: 현행 EDA 세 테스트 모듈을 Spec과 구현에 대조하고 수치 oracle 보강 및 evidence pair cleanup 결함의 후속 경계를 기록합니다.
---

# HMDA EDA Test Design Audit

> [!NOTE]
> EDA 세 모듈의 전수 검토와 허용 범위의 테스트 보강을 완료했다. Historical H6의 수치 oracle 공백을 보완했으며, H5의 cleanup 후 JSON/Markdown 불일치는 현재도 재현된다. H5의 production 수정과 최종 회귀 검증은 [#277](https://github.com/mols3131d/hmda-data-reliability/pull/277)에 인계한다.

- **Target:** HMDA Data의 EDA 계산, portable observation과 explorer 계약.
- **Revision:** `main@ea39a4fd6c8f483509cf00a1d1114feb4ef3b686`을 반영한 `150d565a6be06bc71ca0c446ad26e8143523d780`와 이 PR의 EDA test working diff. Production 재현은 해당 revision의 source를 수정하지 않고 실행했다.
- **Scope:** [test_eda.py](../../tests/hmda_data/eda/test_eda.py), [test_eda_evidence.py](../../tests/hmda_data/eda/test_eda_evidence.py), [test_eda_explorer.py](../../tests/hmda_data/eda/test_eda_explorer.py)의 모든 test body와 fixture 사용을 검토했다. 관련 [EDA Spec](../../openspec/specs/hmda-data-eda-descriptive-evidence/spec.md), [analysis.py](../../src/hmda_reliability/hmda_data/eda/analysis.py), [explorer.py](../../src/hmda_reliability/hmda_data/eda/explorer.py), [EDA public exports](../../src/hmda_reliability/hmda_data/eda/__init__.py), [run_actual_source.py](../../scripts/run_actual_source.py)를 대조했다.

## Findings

| ID | Severity | Finding | Action |
| --- | --- | --- | --- |
| F1 / H5 | 🟡 Minor | 기존 pair의 두 replace가 성공한 후 backup cleanup이 실패하면 JSON old / Markdown new가 남는다. 기존 production defect다. | #277에서 commit/rollback 경계를 수정하고 cleanup 장애 회귀를 추가한다. |
| F2 / H6 | 🟡 Minor | 기존 numeric test가 p25/p75, 음수 보존과 null 제외를 충분히 구별하지 못했다. | 두 field의 exact 전체 summary로 보강했고, 일시적 네 변이의 검출을 확인했다. |

## Historical Adoption

원본 [historical EDA review](01-review-historical/hmda-data/eda.md)의 F1/F2를 전체 audit의 H5/H6에 대응시켰다. 과거 실행 결과를 현재 성공 근거로 재사용하지 않았다.

| ID | Disposition | Current Evidence | Resolution |
| --- | --- | --- | --- |
| H5 / historical F1 | `accepted` | 현재 writer의 backup unlink 장애에서 `OSError`, JSON 100행 / Markdown 200행을 재현했다. | 문제의 존재는 채택했으며 production 수정은 #277에 이관한다. 이 PR에는 알려진 red test를 추가하지 않았다. |
| H6 / historical F2 | `accepted` | 원래 assertion은 income의 count/min/median/max만 검사했다. p25/p75와 loan_amount 전체 결과를 검사하지 않았다. | 기존 test를 음수·빈 값·`NA`·비대칭 값의 exact oracle로 교체했다. Oracle gap 대응을 완료했으며 기존 production 계산 오류를 발견했다는 의미는 아니다. |

`rejected`, `deferred`, `obsolete`에 해당하는 EDA historical finding은 없다. H5의 채택 여부와 다른 PR에서의 수정 대기는 서로 다른 상태다.

## File Verdicts

| File | Verdict | Change And Limit |
| --- | --- | --- |
| [test_eda.py](../../tests/hmda_data/eda/test_eda.py) | `reviewed-and-hardened` | 기존 20개 test body 전체를 검토했다. Distribution의 세 field·null 분모, 두 numeric summary, missing/type mismatch와 duration assertion을 보강했다. Parameterization 후 21개 case다. |
| [test_eda_evidence.py](../../tests/hmda_data/eda/test_eda_evidence.py) | `reviewed-with-follow-up` | Provenance, portability, Git isolation, main wiring와 pair rollback의 모든 test body를 검토했다. 기존 pair overwrite 실패와 Markdown provenance/duration을 보강해 8개 case가 됐다. H5 production 결함은 남아 있다. |
| [test_eda_explorer.py](../../tests/hmda_data/eda/test_eda_explorer.py) | `reviewed-and-hardened` | 기존 두 test body를 모두 검토했다. 전체 YAML·Unicode·key order, HTML embedded data와 빈/한쪽 evidence 및 기존 파일 보존을 검사해 5개 case가 됐다. |

모든 test는 `component` marker를 유지한다. 실제 local CSV, DuckDB, Git repository와 chart artifact I/O가 계약을 소유하므로 단순 call mock보다 해당 경계를 직접 실행한다. Shared fixture와 production·Spec·공용 설정은 변경하지 않았다.

## Scenario And Oracle Coverage

### Descriptive Analysis

아래 test는 모두 [test_eda.py](../../tests/hmda_data/eda/test_eda.py)에 있다. 같은 동작을 반복하는 새 test 대신 기존 assertion과 작은 fixture를 우선 보강했다.

| Test | Scenario | Independent Oracle And Assessment |
| --- | --- | --- |
| `test_eda_evidence_uses_ingestion_csv_parse_contract` | Normal / regression | CSV option 일치와 filename column 부재를 검사한다. Reader와 같은 상수를 비교하는 부분은 단독 semantic proof가 아니며, baseline과 분포 fixture가 `NA`/빈 값의 실제 해석을 별도로 고정한다. |
| `test_eda_evidence_csv_options_do_not_mutate_parse_contract` | Regression / isolation | 반환된 nullstr list를 바꿔도 다음 reader SQL과 원래 parse 설정이 변하지 않는다. |
| `test_analyze_hmda_csv_returns_core_code_distributions` | Normal / boundary | 세 field 전체의 고정 count/share를 비교한다. `NA`와 빈 state를 제외하되 분모는 전체 5행이며, 31/99를 관측 code로 보존한다. |
| `test_analyze_hmda_csv_returns_numeric_summaries_without_clipping` | Boundary / regression | 서로 다른 두 field의 음수·NULL·비대칭 네 값에서 사람이 계산한 12개 통계값을 고정한다. |
| `test_analyze_hmda_csv_omits_anomalies_key` | Invariant / policy | 음수·0·양수에도 `anomalies` key가 없다. 수치 보존은 바로 위 전체 oracle이 별도로 검증한다. |
| `test_analyze_hmda_csv_returns_mart_grain_alignment_evidence` | Normal | 중복 complete key를 포함한 3행의 distinct 2, null 0, coverage 1을 고정한다. |
| `test_analyze_hmda_csv_six_core_source_without_county_code_succeeds` | Boundary / scope | Six-core CSV가 성공하고 county_code가 required/null metric에 들어가지 않는다. |
| `test_analyze_hmda_csv_grain_alignment_excludes_null_keys_from_distinct_count` | Boundary | 일부 grain key가 없는 4행에서 distinct 1, incomplete 2, coverage 1/2을 고정한다. |
| `test_analyze_hmda_csv_rejects_invalid_descriptive_column_without_partial_evidence` | Failure | Income missing과 incompatible VARCHAR를 각각 실제 CSV로 실행하고 `HMDADataValidationError`가 income을 식별하는지 검사한다. |
| `test_eda_public_api_compatibility` | Regression | 공개 함수 세 개와 제거된 workload helper 두 개의 export 경계를 고정한다. |
| `test_supports_expanded_type_families` | Regression / internal support | 지원 type-family 집합을 검사한다. 모든 unsigned/FLOAT 타입의 실제 CSV inference 실행을 입증하지는 않는다. |
| `test_code_distributions_converts_non_primitive_types_for_json` | Serialization regression | DuckDB 반환값만 Decimal로 대체해 JSON-safe 문자열을 검사한다. 실제 source에서 허용되지 않는 Decimal categorical type의 수용 증거는 아니다. |
| `test_activity_year_sampling_order_has_secondary_sort` | Regression / internal support | SQL의 secondary ordering을 확인한다. 실제 연도별 반환 순서는 baseline evidence가 별도로 고정한다. |
| `test_analyze_hmda_csv_observed_at_does_not_trigger_freshness` | Policy regression | Extra observed_at column이 freshness 결과나 freshness SQL을 만들지 않는다. |
| `test_analyze_hmda_csv_returns_baseline_evidence` | Normal / integration boundary | 고정 3행의 전체 row/year/null/schema/source/resource metadata를 비교하고 JSON 직렬화 및 duration 존재·비음수를 확인한다. |
| `test_analyze_hmda_csv_fails_without_partial_evidence_and_closes_connection` | Parse failure / lifecycle | 잘못된 UTF-8 source의 오류 전달, connection close와 원천 byte 보존을 검사한다. |
| `test_analyze_hmda_csv_closes_connection_without_changing_source` | Normal / lifecycle | 성공 뒤에도 실제 source bytes를 보존하고 열린 connection을 닫는다. |
| `test_analyze_hmda_csv_closes_connection_after_query_failure` | Query failure / lifecycle | Aggregate boundary 장애를 전달하고 connection을 닫는다. Domain 계산은 mock하지 않는다. |
| `test_analyze_hmda_csv_rejects_unbounded_activity_years` | Boundary / failure | 3개 year를 상한 2로 분석하면 cardinality validation failure가 난다. |
| `test_analyze_hmda_csv_rejects_missing_input` | Failure | 없는 파일은 원인을 식별하는 `FileNotFoundError`로 실패한다. |

수치 oracle의 non-null 값은 loan_amount `[-100, -20, 40, 200]`, income `[-9, 1, 5, 101]`이다. 각 field의 count는 4이며 `(min, p25, median, p75, max)`는 각각 `(-100, -40, 10, 80, 200)`, `(-9, -1.5, 3, 29, 101)`이다. Production SQL이나 quantile 함수를 test에서 다시 호출해 정답을 만들지 않는다.

### Portable Observation

아래 test는 모두 [test_eda_evidence.py](../../tests/hmda_data/eda/test_eda_evidence.py)에 있다.

| Test | Scenario | Independent Oracle And Assessment |
| --- | --- | --- |
| `test_write_evidence_generates_consistent_json_and_markdown` | Normal / portability | JSON의 고정 provenance, duration, source projection과 Markdown의 고정 지표·metadata를 확인한다. 기계별 절대 경로가 양쪽에 없다. |
| `test_repository_revision_returns_exact_head_when_clean` | Normal / isolation | 독립 임시 Git repository의 실제 HEAD와 exact equality를 비교한다. |
| `test_repository_revision_raises_on_dirty_tree` | Failure / provenance | Staged, unstaged, untracked 세 dirty 상태를 실제 Git으로 만들고 명시적 오류를 확인한다. |
| `test_write_evidence_restores_pair_on_second_replace_failure` | Failure / regression | 최초 생성과 기존 pair overwrite 중 Markdown replace 실패를 각각 주입한다. 신규 pair는 없고, 기존 pair는 두 원래 byte와 일치하며 임시/backup 파일을 남기지 않는다. |
| `test_main_preserves_actual_source_analysis_and_provenance_contract` | Wiring regression | Source, limits, temp path와 portable metadata의 exact 전달을 검사한다. 실제 전체 원천의 재분석이나 fingerprint 계산 자체의 증거는 아니다. |

Autouse fixture는 `GIT_*`만 격리하며 다른 test의 repository 상태에 기대지 않는다. 기존 pair에서 **replace 실패**와 두 replace 성공 뒤 **cleanup 실패**는 별도 분기다. 보강한 rollback test의 통과가 F1 해결을 뜻하지 않는다.

### Explorer Projection

아래 test는 모두 [test_eda_explorer.py](../../tests/hmda_data/eda/test_eda_explorer.py)에 있다.

| Test | Scenario | Independent Oracle And Assessment |
| --- | --- | --- |
| `test_export_eda_evidence_yaml_returns_valid_yaml` | Normal / serialization | 실제 분석 evidence 전체와 parse한 YAML을 비교하며 순서와 한글 보존을 별도로 확인한다. 정답은 projection의 입력이지 YAML writer의 재실행이 아니다. |
| `test_render_eda_static_charts_generates_files` | Normal / local artifact | 정확한 두 output 이름, HTML의 Vega-Lite embedded volume/null 데이터와 측정 field를 검사한다. 파일 존재만으로 성공을 판단하지 않는다. |
| `test_render_eda_static_charts_skips_unavailable_slices_and_preserves_other_files` | Boundary / regression | 빈 evidence, volume-only, null-only 세 경우에서 생성 이름과 실제 directory contents를 비교하고 기존 unrelated file의 bytes를 보존한다. |

## F1 — Minor: Evidence Pair Cleanup Failure

### Locations

- [run_actual_source.py](../../scripts/run_actual_source.py)
  - `write_evidence`, 현재 146행의 Markdown replace 뒤 148행의 backup unlink와 149행의 공통 rollback 분기.
- [EDA Spec](../../openspec/specs/hmda-data-eda-descriptive-evidence/spec.md)
  - `Portable actual-source observation` / `Observation consistency`.

### Evidence

아래 명령은 repository root에서 실행한다. 임시 directory에서만 artifact를 만들며 production 파일은 수정하지 않는다. `Path.unlink`의 해당 backup cleanup만 일시적으로 실패시킨다.

```bash
uv run --no-sync python - <<'PY'
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from scripts.run_actual_source import write_evidence

with TemporaryDirectory() as tmp:
    root = Path(tmp)
    json_path, markdown_path = root / "evidence.json", root / "evidence.md"
    args = dict(json_path=json_path, markdown_path=markdown_path,
                source_id="probe.csv", source_sha256="probe-sha",
                repository_revision="150d565a", observed_at="2026-10-25T00:00:00Z")
    evidence = dict(row_count=100, duration_seconds=0.5,
                    null_counts={"income": 0}, grain={"distinct_group_count": 10})
    write_evidence(evidence, **args)
    real_unlink = Path.unlink

    def fail_backup_unlink(path, *args, **kwargs):
        if path == json_path.with_suffix(".json.bak"):
            raise OSError("injected backup cleanup failure")
        return real_unlink(path, *args, **kwargs)

    with patch.object(Path, "unlink", fail_backup_unlink):
        try:
            write_evidence({**evidence, "row_count": 200}, **args)
        except OSError as error:
            print(type(error).__name__ + ": " + str(error))
    print("JSON row_count:", json.loads(json_path.read_text())["evidence"]["row_count"])
    print(next(line for line in markdown_path.read_text().splitlines()
               if "Total Row Count:" in line))
PY
```

Observed output:

```text
OSError: injected backup cleanup failure
JSON row_count: 100
- Total Row Count: 200
```

### Impact

Caller가 실패를 받더라도 같은 observation의 JSON과 Markdown이 서로 다른 row count를 가리킨다. 이는 기존 writer의 consistency 결함이다. 이번 테스트 변경에서 새로 발생한 문제는 아니다.

### Action

[#277](https://github.com/mols3131d/hmda-data-reliability/pull/277)에서 두 artifact 교체의 완료와 backup cleanup을 분리한다. Cleanup 실패를 이미 게시한 새 pair 한쪽만 되돌리는 rollback으로 보내지 않아야 한다. 최종 오류 전파·잔여 backup 정책은 owning 구현에서 정하고, 선택한 정책과 무관하게 두 target의 지표·provenance가 모두 old 또는 모두 new인지를 회귀 oracle로 사용한다. Replace 실패와 cleanup 실패의 test는 분리해 유지한다.

## Validation

검증일은 2026-10-25이며 전용 worktree와 `.venv`에서 `uv run --no-sync`로 실행했다. 최초 module baseline은 29개 case였다. 변경 뒤 34개 case이며 아래 수치는 local evidence다.

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | 최초 EDA baseline | `uv run --no-sync pytest tests/hmda_data/eda/` → `29 passed in 1.64s`. |
| ✅ Pass | 변경 EDA 세 모듈 | 같은 command → `34 passed in 2.57s` (`21 + 8 + 5`). |
| ✅ Pass | Ruff lint | `uv run --no-sync ruff check tests/hmda_data/eda/` → `All checks passed!`. |
| ✅ Pass | Ruff format | `uv run --no-sync ruff format --check tests/hmda_data/eda/` → `3 files already formatted`. |
| ✅ Pass | Scoped type check | `uv run --no-sync ty check tests/hmda_data/eda/` → `All checks passed!`. |
| ✅ Pass | Numeric oracle negative controls | 기존 분석 경로를 실행한 뒤 `_collect_numeric_summaries` 결과만 일시적으로 바꿨다. `swap-quartiles`, `null-quartiles`, `clip-negative`, `count-null` 네 경우 모두 강화한 test의 `AssertionError`로 `DETECTED`였다. Production source 파일은 수정하지 않았다. |
| ❌ Fail | H5 consistency probe | 위 self-contained command의 JSON 100 / Markdown 200. Probe 자체가 정상 종료했다는 사실을 consistency 성공으로 해석하지 않는다. |
| ⚪ Not Verified | 실제 전체 HMDA 원천 observation | Fixture correctness와 writer 경계를 검토했다. Controlled actual-source run은 수행하지 않았다. |
| ⚪ Not Verified | Browser / offline rendering | HTML embedded spec/data를 검사했다. 실제 browser 실행, 외부 renderer CDN 가용성과 offline HTML 동작은 확인하지 않았다. |

Negative control은 검출력을 확인하는 일시적 실험이며 정상 suite에 domain mock을 추가하지 않았다. 수치 계산은 각 실험에서도 실제 DuckDB로 먼저 수행했다. Assertion이 실패하지 않는 변이는 실험 실패로 처리했다.

## Risks And Limits

전체 입력 공간의 완전성이나 성능·OOM 안전성은 이 검토의 완료 조건이 아니다. Empty source와 모든 값이 NULL인 core field는 CSV type inference와 schema compatibility 정책에 영향을 받으므로 여기서 새로운 acceptance 계약을 만들지 않았다. Resource lifecycle은 열린 in-memory DuckDB connection과 source bytes를 검사하며 별도 persistent database를 입력받는 API는 없다.

Chart의 embedded numeric assertion은 현재 정상 fixture의 비영 volume과 zero-null baseline을 고정한다. Nonzero null-only fixture는 생성 분기와 파일 보존을 검증하며, 해당 수치가 browser에서 표시되는지는 입증하지 않는다. HTML의 `var spec`를 읽는 검사이므로 Altair의 HTML serialization 형식이 바뀌면 이 test의 extraction 경계를 함께 검토해야 한다.

이 문서는 EDA 소유 세 module의 검토·보강 결과다. PR 전체 검증, 독립 review와 최종 head의 readiness는 [최종 audit report](05-report-hmda-data-audit.md)가 소유한다.
