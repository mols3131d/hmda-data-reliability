---
type: review
title: Data Platform dbt Test Audit
description: dbt analytics 테스트 전체와 정본 계약을 대조하고 metric·grain·staging type·quality failure oracle 보강 및 검출 근거를 기록합니다.
---

# Data Platform dbt Test Audit

> [!NOTE]
> Legacy P1을 수용하고, 추가로 확인한 grain·staging type·quality failure oracle 공백을 테스트만으로 보강했다.
> 실제 dbt를 포함한 module 3개 test와 격리한 세 metric mutant 검출을 확인했다. 이 문서는 구현 작업자의 설계 대조 기록이며 새 revision의 독립 리뷰는 별도다.

- **Target:** [dbt test module](../../tests/dbt/test_analytics_foundation.py), [새 design map](../../tests/dbt/test_analytics_foundation.design.md), [analytics Spec](../../openspec/specs/data-platform-dbt-analytics/spec.md)과 [dbt project](../../dbt/).
- **Revision:** Baseline main `ea39a4fd6c8f483509cf00a1d1114feb4ef3b686`; initial PR head `f1cf36e5baf74f356333c7a7ff70240287e27c55`; main 병합 anchor `4f2bebb4d5a5a6e64336e5df3c9c11b5da65f4ae` 위의 미커밋 test 변경. 최종 commit·CI의 증거는 통합 검증 문서가 소유한다.
- **Scope:** 현행 `tests/dbt` 추적 파일 전체 1개, 추가한 design 1개 및 위 test의 모든 helper·fixture. 운영 runner·promotion·Airflow composition은 읽기/쓰기 범위에 포함하지 않았다.

## Findings

아래는 착수 시 확인한 oracle gap과 이번 조치다. 검토한 production SQL에서 해당 의미의 실제 결함은 발견하지 않았다.

| ID | Severity | Finding | Action |
| --- | --- | --- | --- |
| F1 | 🟡 Minor | Legacy P1: action 2·여섯 자리 반올림·eligible numeric NULL의 평균 의미를 기존 fixture가 구별하지 못했다. | `accepted`; TX 3행과 손계산 tuple을 추가해 해결, 세 mutant 검출 |
| F2 | 🟡 Minor | 기존 두 grain은 state와 purpose가 함께 달라지고 year는 하나여서 세 차원의 grain을 독립적으로 구별하지 못했다. | 같은 state/purpose의 다른 year와 같은 year/state의 다른 purpose를 추가해 해결 |
| F3 | 🟡 Minor | Staging Spec의 integer/string type은 numeric 두 column과 달리 직접 확인하지 않았다. | Spec이 선언한 9개 column type과 eligible NULL row의 고정 값을 확인해 해결 |
| F4 | 🟡 Minor | 성공 build만으로는 source/model 필수 값, mart grain NULL·duplicate의 quality test 실패를 확인하지 못했다. | 성공 build 후 controlled corruption과 정확한 네 실패 contract를 확인해 해결 |
| F5 | 🟡 Minor | Metric helper의 `int()` 변환이 fractional count 같은 잘못된 DB 값을 기대 정수로 바꿔 숨길 수 있었다. | Fetch한 원값을 직접 비교하고 typing-only `cast`만 유지해 해결 |

## Inventory And Contract Coverage

두 revision에서 `git ls-tree -r --name-only <revision> -- tests/dbt`와 현행 `git ls-files tests/dbt`를 대조했다. Baseline main과 initial head의 추적 파일은 모두 아래 Python module 하나였다. 새 design은 이번 보강으로 추가한다.

| File | Review Outcome | Contract·Oracle·Boundary |
| --- | --- | --- |
| [test_analytics_foundation.py](../../tests/dbt/test_analytics_foundation.py) | 전체 검토·보강 | 두 기존 test, 모든 local helper와 CSV fixture를 대조하고 세 번째 negative test를 추가했다. Profile 선언, real CLI status, staging type·NULL, 다섯 mart tuple, grain count, manifest 직접 edge와 두 번 build의 고정 결과를 확인한다. |
| [test_analytics_foundation.design.md](../../tests/dbt/test_analytics_foundation.design.md) | 신규 support·검토 | Scenario→test와 산술 oracle, local isolation, 명시적 exclusion을 현재 code에 연결한다. 실행 log는 이 보고서가 소유한다. |

Source 대조는 [source 선언](../../dbt/models/sources.yml), [staging SQL](../../dbt/models/staging/stg_hmda_loans.sql), [staging quality schema](../../dbt/models/staging/schema.yml), [mart SQL](../../dbt/models/marts/mart_hmda_loan_outcomes.sql), [mart quality schema](../../dbt/models/marts/schema.yml), [schema macro](../../dbt/macros/generate_schema_name.sql), [project 설정](../../dbt/dbt_project.yml), [profile](../../dbt/profiles.yml)에 걸쳐 수행했다. Fixture가 연결하는 [ingestion query](../../src/hmda_reliability/hmda_data/ingestion/_source_query.py)와 [full load](../../src/hmda_reliability/hmda_data/ingestion/full_load.py)는 setup의 metadata/NULL 의미 확인에만 사용했다. 현재 정본 Spec을 기준으로 판단했으며, HMDA 전환 전 archived taxi design의 구식 경로·fallback을 계약으로 채택하지 않았다.

| Contract | Scenario And Independent Oracle | Outcome Or Exclusion |
| --- | --- | --- |
| Caller-provided path | Default 없는 환경 변수 profile 표현과 주입한 tmp DB에서 실제 dbt debug/build | 유지; missing-variable error 문구는 고정하지 않음 |
| Source·lineage | Manifest의 raw source 존재와 source→staging→mart 직접 dependency | 유지; downstream consumer의 traversal algorithm은 이 module 밖 |
| Staging preservation·types | 10행 유지, Spec의 9개 type, nullable state/county 및 complete-key invalid numeric의 고정 NULL row | 보강; 일반 type coercion 입력 전체를 열거하지 않음 |
| Eligible mart population | NULL state 행 제외; TX의 numeric NULL·county NULL 행은 application에 포함 | 보강; 필수 year/purpose NULL은 quality가 build를 차단하므로 mart-only projection은 별도 실행하지 않음 |
| Full grain·metric | 같은 state/purpose의 2024/2025, 같은 year/state의 purpose 1/31, 같은 year/purpose의 CA/TX, 다섯 고정 tuple | 보강; `mart_grain_key`의 문자열 포맷은 Spec이 정하지 않으므로 고정하지 않음 |
| Approval·denial·rate·average | Action 1/2 승인, 3/7 거절, 4 neither; TX count 3·approval 2·rate `0.666667`·평균 `150000/75` | 보강; all-null numeric grain은 이번 최소 regression에서 제외 |
| Quality failure | `source_year=NULL`, duplicate NY mart row, TX grain key NULL 뒤 `dbt test` exit 1과 정확한 네 `fail` | 신규; source/staging의 모든 필수 column별 mutation을 반복하지 않음 |
| Deterministic rebuild | 두 번 build 모두 count/unique count `(5,5)`와 동일한 다섯 고정 tuple | 유지·확장; 운영 규모와 incremental materialization 성능은 미검증 |
| Isolation·cleanup | 각 test의 `tmp_path` 아래 DB/target/log; synchronous CLI 종료 후 DB 조회 | 공유 DB/artifact 또는 실제 network dependency 없음; external/multi-host coordination은 이 module 밖 |

## Legacy Disposition

[Historical review](01-review-historical/data-platform/README.md)의 dbt 소유 finding은 P1 하나다. `3ab899100fc0b35e23d464bd761f3b144a978ae7`의 과거 판단을 현행 구현·fixture와 대조했고, initial head에서도 action 2와 반복소수 rate 및 complete-key invalid numeric 입력이 없어 **accepted**로 판정했다. 기존 SQL은 이미 올바른 `IN (1,2)`, `round(...,6)`, `avg(...)`를 사용하므로 production defect가 아니라 test oracle gap이다. Historical 제안의 `1/3 → 0.333333` 대신 `2/3 → 0.666667`을 사용해 절삭과 반올림도 산술적으로 구별한다. 기존 action 3·7의 denial 예시는 유지했다. DuckDB/SQL/artifact의 historical 관찰은 각 소유 lane의 보고서가 판정하며 이 문서에서 중복 수용하지 않는다.

## Mutation Evidence

실제 dbt project를 `TemporaryDirectory`로 복사하고 복사본의 mart SQL만 변경했다. 보강한 build test를 직접 호출해 실제 dbt debug/build 2회 이후 [고정 metric assertion](../../tests/dbt/test_analytics_foundation.py#L75)이 실패하는지 확인했다. 셋 모두 SQL 실행은 성공했고 동일 test 함수의 metric 비교에서 검출됐다. Pytest collection/plugin을 포함한 별도의 세 test 실행으로 세지 않는다.

| Mutant | Observed TX Tuple Difference | Detection |
| --- | --- | --- |
| `IN (1,2)` → `IN (1)` | Approval `1`, rate `0.333333` | 고정 tuple과 불일치 |
| `round(...,6)` 제거 | Rate `0.6666666666666666` | 고정 `0.666667`과 불일치 |
| 두 `avg(x)` → `avg(coalesce(x,0))` | Averages `100000.0`, `50.0` | 고정 `150000.0`, `75.0`과 불일치 |

다음은 실행한 재현 명령이다. 작업 directory는 `/home/mols3131d/workspaces/hmda-data-reliability.worktrees/pr271-data-platform`이었다. 각 복사본은 context 종료 때 제거됐으며 repository의 [mart SQL](../../dbt/models/marts/mart_hmda_loan_outcomes.sql)은 수정하지 않았다.

```sh
uv run --no-sync python - <<'PY'
import importlib.util
import shutil
import tempfile
import traceback
from pathlib import Path

root = Path.cwd()
spec = importlib.util.spec_from_file_location('dbt_audit_test', root / 'tests/dbt/test_analytics_foundation.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
original = (root / 'dbt/models/marts/mart_hmda_loan_outcomes.sql').read_text()
rounded = '''round(
        1.0 * sum(case when action_taken in (1, 2) then 1 else 0 end)
        / nullif(count(*), 0),
        6
    )'''
unrounded = '''1.0 * sum(case when action_taken in (1, 2) then 1 else 0 end)
        / nullif(count(*), 0)'''
assert rounded in original
mutants = {
    'omit_action_2': original.replace('action_taken in (1, 2)', 'action_taken in (1)'),
    'remove_six_place_rounding': original.replace(rounded, unrounded),
    'numeric_null_as_zero': original.replace('avg(loan_amount)', 'avg(coalesce(loan_amount, 0))').replace('avg(income)', 'avg(coalesce(income, 0))'),
}
for name, sql in mutants.items():
    with tempfile.TemporaryDirectory(prefix='pr271-dbt-mutant-') as temporary:
        sandbox = Path(temporary)
        copied = sandbox / 'dbt'
        shutil.copytree(root / 'dbt', copied, ignore=shutil.ignore_patterns('target', 'logs', '.user.yml'))
        (copied / 'models/marts/mart_hmda_loan_outcomes.sql').write_text(sql)
        module.DBT_PROJECT_DIR = copied
        case = sandbox / 'case'
        case.mkdir()
        try:
            module.test_dbt_build_creates_artifacts_lineage_and_idempotent_mart(case)
        except AssertionError as error:
            last = traceback.extract_tb(error.__traceback__)[-1]
            assert last.name == 'test_dbt_build_creates_artifacts_lineage_and_idempotent_mart', traceback.format_exc()
            tx = [row for row in module._mart_metric_rows(case / 'hmda_reliability.duckdb') if row[1] == 'TX']
            print({'mutant': name, 'result': 'detected_by_fixed_mart_oracle', 'assertion_line': last.lineno, 'observed_TX': tx}, flush=True)
        else:
            raise AssertionError(f'mutant survived: {name}')
PY
```

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | 현행 inventory・source/spec 대조 | Baseline/initial head의 추적 Python 1개 전체와 신규 design 1개, 위 source/config 8개 및 Spec 대조 |
| ✅ Pass | 실제 dbt 포함 focused module | `uv run --no-sync pytest tests/dbt/test_analytics_foundation.py` → `3 passed in 33.64s`; integration 2개와 profile component 1개. Ruff의 줄 접기 전 동일 동작 code에서 실행 |
| ✅ Pass | Final raw-value oracle | Coordinator가 `8bf4e6b095aac7377ac0b22052711c96d929f926`의 마지막 `cast` 변경까지 포함해 `uv run --no-sync pytest tests/data_platform tests/dbt -q` 실행: `43 passed, 1 warning in 21.75s`. dbt 3개를 포함하며 기존 fork warning 1건. Ruff·format·ty 재검사도 통과 |
| ✅ Pass | Metric mutant 검출 | 위 direct-call harness exit 0; 세 변형 모두 metric assertion line 75에서 검출 |
| ✅ Pass | Python lint·format | `uv run --no-sync ruff check tests/dbt/test_analytics_foundation.py`, `uv run --no-sync ruff format --check tests/dbt/test_analytics_foundation.py` 통과 |
| ✅ Pass | Whitespace | `git diff --check -- tests/dbt` 통과 |
| ✅ Pass | Markdown | 새 design과 이 보고서에 `uv run --no-sync rumdl check` 통과 |
| ⚪ Not Verified | CI·독립 리뷰 | [통합 보고서](05-report-current-audit.md)에서 current state와 별도 근거를 확인하며 이 module 결과로 대체하지 않음 |

## Risks And Limits

이 lane에서 production·Spec·공용 설정 변경이 필요한 defect 또는 #277에 새로 넘겨야 할 결함은 확인하지 못했다. Data Operations의 quality gate·candidate adoption, 실제 Airflow composition, 공유 CI dbt routing은 예약된 cross-domain 범위다. 세 mutant는 선택한 metric gap의 검출 근거이며 전체 SQL mutation score 또는 모든 가능한 잘못된 구현의 검출을 주장하지 않는다.
