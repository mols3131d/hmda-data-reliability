---
type: review
title: DuckDB and SQL Primitive Test Audit
description: DuckDB 연결·metadata·mutation lock과 SQL quoting 테스트의 현행 계약, 독립 oracle, 보강 및 검증 근거를 기록합니다.
---

# DuckDB and SQL Primitive Test Audit

> [!NOTE]
> 담당 3개 파일을 전수 검토하고 연결 계약·SQL oracle 공백을 보강했습니다. Focused 25개 테스트가 통과했습니다. PR 전체의 독립 리뷰·CI·human review readiness는 이 보고서의 판정 범위 밖입니다.

- **Target:** PR [#271](https://github.com/mols3131d/hmda-data-reliability/pull/271)의 DuckDB/SQL primitive 테스트.
- **Revision:** `main@ea39a4fd6c8f483509cf00a1d1114feb4ef3b686`를 최초 PR head `f1cf36e5baf74f356333c7a7ff70240287e27c55`에 병합한 `4f2bebb4d5a5a6e64336e5df3c9c11b5da65f4ae` 위의 test working diff. Production source와 normative Spec은 변경하지 않았습니다.
- **Scope:** 아래 inventory 전체, 대응 [DuckDB source](../../src/hmda_reliability/data_platform/duckdb.py), [SQL source](../../src/hmda_reliability/data_platform/sql.py), [normative Spec](../../openspec/specs/data-platform-duckdb-access/spec.md), [domain boundary](../../docs/domains/data-platform.md).

## Findings

| ID | Severity | Finding | Action |
| --- | --- | --- | --- |
| F1 | 🟡 Minor | 연결 테스트는 file cleanup 한 건으로 read-only 거부·scope 종료·memory 격리·metadata 계약을 직접 구별하지 못했습니다. | 실제 DuckDB 연결로 다섯 scenario를 보강했습니다. |
| F2 | 🟡 Minor | SQL Hypothesis 두 oracle이 production의 `replace` 식을 그대로 반복했습니다. | 실제 parser가 반환한 원문과 exact 비교하도록 교체했습니다. |

확인한 production defect 또는 미결 normative Spec gap은 없습니다. F1/F2는 테스트 evidence gap이며 현재 보강 후 focused 실행을 마쳤습니다.

## Inventory And Contract Evidence

| File | Outcome | Exclusion |
| --- | --- | --- |
| [test_duckdb.py](../../tests/data_platform/test_duckdb.py) | 전체 검토. 기존 cleanup·alias/thread·nested/spawn·fork·release/body failure 검증 유지. 연결·metadata 보강 및 lock acquisition failure 확장. | 외부 writer·multi-host coordination과 ingestion/recovery/dbt caller의 lock 적용은 이 primitive의 책임 밖입니다. |
| [test_sql.py](../../tests/data_platform/test_sql.py) | 전체 검토. 고정 quoting/invalid-input 예시 유지. 생성 입력의 oracle 교체, 실제 I/O 테스트에 `component` 적용. | string literal의 NUL SQL text 지원은 Spec에 정의되지 않아 parser property 입력에서 제외합니다. 동적 값 binding을 대체하는 helper로 확대하지 않습니다. |
| [__init__.py](../../tests/data_platform/__init__.py) | read-only 전체 검토. module docstring뿐이며 fixture·import side effect·state가 없습니다. | tests write boundary에 따라 수정하지 않았습니다. |

| Contract | Scenario And Independent Oracle | Level |
| --- | --- | --- |
| Managed connection lifetime | 정상/`ValueError` body 이후 실제 연결의 `SELECT`가 `ConnectionException`을 냅니다. body 예외도 그대로 관찰합니다. | component |
| Isolated in-memory connection | 첫 연결에만 만든 고정 table을 둘째 연결은 찾지 못하며 첫 연결의 `(7,)`은 유지됩니다. 두 연결의 실제 database path는 `None`입니다. | component |
| Read-only connection | file DB의 `(7,)`을 읽고 `INSERT (9)`는 `InvalidInputException`으로 거부합니다. 재접속해 원래 row가 그대로임을 확인합니다. 실제 file path도 비교합니다. | component |
| Schema/table metadata | 고정 SQL로 quote 포함 schema/table을 생성합니다. schema ensure를 두 번 호출하고 empty count `0`, duplicate와 NULL 포함 count `3`, 고정 column 집합을 비교합니다. | component |
| Cleanup | 기존 실제 DB file 생성·scope 종료 후 file 삭제 검증을 유지합니다. | component |
| Canonical mutation lock | relative/symlink 경로의 실제 thread contention, nested success/exception 후 outer 배타성, fork child의 별도 획득을 유지합니다. | component |
| Lock failure meaning | mkdir 준비와 실제 flock 획득의 `OSError`를 통제해 typed failure·body 미진입·원인 exception identity를 확인합니다. release failure와 body failure 우선순위는 기존 검증을 유지합니다. | component |
| In-memory mutation lock | 기존 `None` 경계가 file open을 하지 않는지 확인합니다. public lock/error re-export 검증도 유지합니다. | component |
| Identifier/literal quoting | 손으로 작성한 exact 문자열 및 empty/NUL identifier 거부 예시는 unit입니다. 생성 입력은 실제 DuckDB가 해석한 column 이름·literal 값과 원래 입력을 exact 비교합니다. quote+semicolon+comment 형태의 고정 예시도 항상 실행합니다. | unit / component |

SQL property oracle은 escape algorithm을 재구현하지 않습니다. quoted schema/table metadata 시나리오도 고정 SQL로 만든 table을 production qualification helper가 정확히 찾는지 확인하므로 writer/reader가 같은 helper를 공유하지 않습니다.

## Historical Adoption

[Historical review](01-review-historical/data-platform/README.md)는 `3ab899100fc0b35e23d464bd761f3b144a978ae7`에 대한 자료로 취급했습니다.

| Historical Item | Decision | Current Evidence |
| --- | --- | --- |
| DuckDB assessment의 read-only write 거부 미검증 | accepted | 현행 test에도 직접 거부 검증이 없어 F1로 보강했습니다. |
| SQL assessment의 production과 동일한 expected 식 | accepted | 현행 property 두 건에서 동일 식을 확인하고 F2로 교체했습니다. |
| P1 analytics branch oracle | separate owner | [dbt audit](03-review-dbt.md)가 현재 fixture·SQL과 대조해 최종 수용 여부와 조치를 소유합니다. 이 보고서에서 중복 finding으로 세지 않습니다. |

## Validation

실행 환경은 해당 worktree의 `.venv`, Python 3.13.13, DuckDB 1.5.5입니다. 아래 결과는 위 revision과 이 보고서의 test diff에 대한 로컬 근거입니다.

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | Focused tests | `uv run --no-sync pytest tests/data_platform/test_duckdb.py tests/data_platform/test_sql.py -q` → `25 passed, 1 warning in 5.51s`. warning은 기존 fork test에서 발생한 multi-threaded process의 `fork()` DeprecationWarning입니다. |
| ✅ Pass | Ruff lint | `uv run --no-sync ruff check tests/data_platform/test_duckdb.py tests/data_platform/test_sql.py` → `All checks passed!`. |
| ✅ Pass | Ruff format | `uv run --no-sync ruff format --check tests/data_platform/test_duckdb.py tests/data_platform/test_sql.py` → `2 files already formatted`. |
| ✅ Pass | Diff whitespace | `git diff --check` → exit `0`. |
| ✅ Pass | Counterexample detection | production file 수정 없이 별도 Python process에서 identifier escaping 생략, literal escaping 생략, `read_only=False` 강제를 각각 주입했습니다. 대응 단일 test의 `pytest.main(['-q', '-p', 'no:tach', target])`는 세 경우 모두 exit `1`로 실패했습니다. 아래 재현 조합을 사용했습니다. |
| ⚪ Not Verified | PR-wide validation | 관련 package 통합 실행·fresh independent review·현재 remote CI는 PR coordinator가 확인합니다. |

| Transient Mutation | Target | Observed Result |
| --- | --- | --- |
| `sql.quote_identifier = lambda value: '"' + value + '"'` | `test_quote_identifier_preserves_generated_content` | `1 failed in 0.42s` |
| `sql.quote_string_literal = lambda value: "'" + value + "'"` | `test_quote_string_literal_preserves_generated_content` | `1 failed in 0.43s` |
| 원본 `duckdb.connect` 호출 전 keyword `read_only=False` 고정 | `test_duckdb_read_only_connection_rejects_writes` | `1 failed in 0.27s` |

Transient mutation은 `uv run --no-sync python`이 시작한 독립 `.venv/bin/python -c` process에서 module attribute에만 적용했으며 production tree를 수정하지 않았습니다.

다음은 실제 실행한 재현 명령입니다. `target`은 각 mutation과 대응하는 test 하나만 선택합니다.

```bash
uv run --no-sync python - <<'PY'
import subprocess
import textwrap

mutants = [
    ('identifier_without_escaping', '''
import hmda_reliability.data_platform.sql as sql
sql.quote_identifier = lambda value: '"' + value + '"'
target = 'tests/data_platform/test_sql.py::test_quote_identifier_preserves_generated_content'
'''),
    ('literal_without_escaping', '''
import hmda_reliability.data_platform.sql as sql
sql.quote_string_literal = lambda value: "'" + value + "'"
target = 'tests/data_platform/test_sql.py::test_quote_string_literal_preserves_generated_content'
'''),
    ('read_only_ignored', '''
import hmda_reliability.data_platform.duckdb as platform
original = platform.duckdb.connect
def connect(*args, **kwargs):
    kwargs['read_only'] = False
    return original(*args, **kwargs)
platform.duckdb.connect = connect
target = 'tests/data_platform/test_duckdb.py::test_duckdb_read_only_connection_rejects_writes'
'''),
]
for name, setup in mutants:
    code = textwrap.dedent(setup) + "\nimport pytest\nraise SystemExit(pytest.main(['-q', '-p', 'no:tach', target]))\n"
    result = subprocess.run(['.venv/bin/python', '-c', code], text=True, capture_output=True)
    print(name, 'pytest_exit=', result.returncode)
    for line in result.stdout.splitlines():
        if line.startswith('FAILED ') or 'failed in ' in line:
            print(line)
    assert result.returncode == 1, result.stdout + result.stderr
PY
```

## Risks And Limits

- 기존 contention 검증은 event handshake와 bounded wait를 사용합니다. 임의 scheduler starvation에 대한 형식적 증명이 아니며 단일 Linux host의 cooperative lock을 검증합니다.
- NUL literal, WAL 삭제의 개별 실패, 없는 metadata row에 대한 내부 branch 등은 명시된 핵심 scenario의 증거를 늘리지 않아 새 테스트를 만들지 않았습니다. NUL identifier 거부는 유지합니다.
- 이 보고서는 하위 영역 담당자의 implementation self-review입니다. fresh independent review와 PR 전체 acceptance를 대신하지 않습니다.
