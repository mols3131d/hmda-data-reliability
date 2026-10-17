---
type: report
title: PR 252 Cloud Validation And Confirmed Findings
description: 고정 revision에서 실행한 도메인 테스트, 결함 재현과 남은 검증 경계를 기록합니다.
tags:
  - reliability
  - testing
---

# Cloud Validation And Confirmed Findings

**기존 테스트 548 passed / 4 failed / 1 skipped. 제품 결함 세 종류, zero-threshold 오탐과 SDK 테스트 공백을 재현했다. Airflow 통합 검증은 미완료이므로 전체 정상 또는 merge-ready로 판정하지 않는다.** Production 수정은 이 문서 감사 PR에 섞지 않고 아래 후속 작업으로 분리한다.

검증일: 2026-10-15. GitHub PR head `b9f9c7657f1d65e5b583ed16afd035ec218e1ed6`, source baseline `8bc62fa6ec995f2e57456d55712b36ff11b1f1d9`. 이 둘의 차이는 Inbox 문서이며 본 보고서 작성 중 source/test/spec 변경은 없다.

## Execution Evidence

Private clone 인증을 사용할 수 없어 GitHub connector에서 exact head의 파일을 읽어 실행 snapshot을 구성했다. 내려받은 353개 파일은 Git blob SHA와 모두 일치했다. 이는 Git checkout이 아니며 Git 기반 telemetry 경고가 있었다. Python 3.13.16에서 `uv sync --locked`로 고정 의존성을 설치했다(DuckDB 1.5.5, pytest 9.1.1, dbt-core 1.12.3, Airflow 3.3.0). 외부 LLM 호출은 수행하지 않았다.

| Check | Result | Evidence |
| --- | --- | --- |
| Schema recovery focused | Pass | candidate/executor/schema-drift evaluator: 31 passed, 3.04s |
| Existing detector tests | Pass | `test_basic_incident_detection.py`: 9 passed, 0.09s |
| Seven-domain suite | Fail | 548 passed, 4 failed, 1 skipped, 82.68s |
| Airflow DAGRun serial retry | Fail | 같은 파일의 5 tests failed, 54.76s; 병렬 실행만의 문제는 아님 |
| Contract probes | Expected RED | detector 3, HMDA 1, Review AI 2: 6 failed, 1.24s; 기존 suite 실패 수와 별개 |
| Schema unlock fault injection | Reproduced | target expected-after=True인데 error stage=before_target_mutation; replay=already_restored |
| SDK mapping negative control | Survived | 실제 SDK model kwarg를 잘못 바꾼 격리 copy에서도 Runtime AI 31 passed |
| Optional Langfuse integration | Not Verified | `langfuse._task_manager.media_manager`가 없어 1 skip; 해당 optional dependency 미설치 |

실행 명령은 repository root 기준이다. Focused 결과는 full suite에 중복 포함되므로 합산하지 않는다.

```bash
uv sync --locked
uv run --no-sync pytest tests/reliability/test_schema_recovery_candidate.py tests/reliability/test_schema_recovery_executor.py tests/reliability/test_schema_drift_evaluation.py -q
uv run --no-sync pytest tests/reliability/test_basic_incident_detection.py -q
uv run --no-sync pytest tests/reliability tests/data_operations tests/hmda_data tests/data_platform tests/dbt tests/review_ai tests/runtime_ai tests/orchestration -n 2 -q -ra
uv run --no-sync pytest tests/orchestration/test_airflow_dagrun.py -q -ra
```

### Airflow Execution Limit

첫 실행에서 `test_disabled_analytics_is_skipped_without_asset_update`, `test_quality_gate_blocks_analytics_with_incident_evidence`, `test_success_promotes_candidate_and_records_analytics_update`, `test_dbt_failure_preserves_current_without_analytics_update`가 실패했다. Serial retry에서는 `test_raw_failure_blocks_gate_and_analytics_without_events`도 실패했다.

실제 Airflow `InProcessTestSupervisor.start`의 `psutil.Process()`가 `NoSuchProcess`를 발생시켰다. Repository 없이 `os.getpid()`, `/proc/<pid>` 존재 확인, `psutil.Process()`만 실행해도 현재 PID의 proc 항목이 없고 같은 오류가 재현됐다. 따라서 이 실패를 도메인 코드 회귀로 분류하지 않는다. 별도로 SQLite `database disk image is malformed`도 발생했으며 정확한 원인은 확정하지 못했다. 이 제한을 피하려고 production task나 psutil을 monkeypatch하여 PASS를 만들지 않았다. 정상 proc/filesystem을 제공하는 runner에서 **5개 DAGRun tests 전체를 다시 실행**해야 한다. 병렬 실행의 raw-failure 1 pass만으로 해당 계약 검증을 완료 처리하지 않는다.

## Confirmed Findings And Follow-up

아래 owner는 후속 변경의 책임 도메인이지 특정 담당자의 수락 또는 risk acceptance가 아니다. 후속 PR은 아직 생성하지 않았다. 모두 미해결 상태다.

| ID | Severity | Finding | Follow-up owner / acceptance oracle |
| --- | --- | --- | --- |
| R-HMDA-01 | Major | 재적재 CSV 컬럼 순서가 바뀌면 호환 타입 값이 조용히 뒤바뀜 | HMDA ingestion: 이름별 정렬 또는 명시적 거부; 값·다른 partition 보존 회귀 |
| R-REV-01 | Major | 일부 JSON parser 오류가 typed failure와 invocation 저장을 우회 | Review AI: 제한 내 parser 실패를 validation_failed로 기록; provider 1회·persisted provenance 검증 |
| R-SCH-01 | Major | commit 뒤 lock 해제 실패를 변경 전 실패로 보고 | Reliability + Data Platform: committed 상태와 failure stage 정합성; evaluator evidence 및 replay 회귀 |
| R-DET-01 | Minor | threshold=0이면 변화가 없는 metric도 incident 생성 | Reliability detection: 변화 없음=0건, 양의 악화만 검출 |
| R-TD-02 | Minor | 실제 SDK adapter mapping 오류를 기존 테스트가 놓침 | Runtime AI tests: fake SDK client로 실제 adapter kwargs/오류/응답 검증 |

### R-HMDA-01 — Positional Partition Insert

[`partition.py`](../../src/hmda_reliability/hmda_data/ingestion/partition.py)의 `_replace_partition_rows`가 `INSERT INTO target SELECT * FROM stage`를 사용한다. [`hmda-data-ingestion`](../../openspec/specs/hmda-data-ingestion/spec.md)의 source value preservation과 불일치한다.

동일 DuckDB에 `loan_amount,income = 350000,120`인 CSV를 먼저 적재한 뒤, 헤더를 `income,loan_amount`로 바꾸고 각 값은 원래 이름에 맞게 유지하여 재적재했다. 반환 count는 1인데 target의 `loan_amount,income`은 `(120,350000)`으로 바뀌었다. 기본 `preserve_source_metadata=False`에서 재현했으며 ordered-schema safeguard가 있는 True 경로까지 일반화하지 않는다. 입력 파일끼리의 `UNION ALL BY NAME`은 기존 target 순서 정렬을 보장하지 않는다. 기존 count 중심 재적재 테스트로는 이 손상을 검출하지 못한다.

### R-REV-01 — Parser Exceptions Escape Evidence Persistence

[`service.py`](../../src/hmda_reliability/review_ai/service.py)의 `_parse_output`은 JSONDecodeError/TypeError/ValidationError만 처리한다. 10,000단 중첩 JSON(20,001 bytes)은 RecursionError, 5,000자리 integer JSON(5,006 bytes)은 ValueError로 빠져나갔다. 둘 다 설정의 max_output_bytes 미만이었다. Public `review_null_spike`에서 provider는 정확히 1회 호출됐으나 persisted JSON은 없었다. [`reliability-agentic-review`](../../openspec/specs/reliability-agentic-review/spec.md)의 started invocation evidence 및 schema-invalid 처리 경계 위반이다. Provider stub으로 response boundary만 주입했으며 실제 외부 LLM behavior를 검증한 것은 아니다.

### R-SCH-01 — Committed Mutation Reported As Pre-mutation Failure

[`schema_executor.py`](../../src/hmda_reliability/reliability/recovery/schema_executor.py)는 lock context 전체의 DuckDBMutationLockError를 before_target_mutation으로 분류한다. [`duckdb.py`](../../src/hmda_reliability/data_platform/duckdb.py)는 성공한 body 뒤 unlock/close 실패도 같은 예외로 노출한다.

Target lock의 LOCK_UN에서만 OSError를 주입했다. 반환 error metadata는 `failure_stage=before_target_mutation`, `mutation_state=None`, `reconciliation_action=retry_same_approval`인데 DB identity는 expected_after와 일치했다. Fault를 제거하고 replay하면 `already_restored / resume_verification`이었다. 즉 안전한 replay guard는 남아 있고 승인 우회나 이중 mutation을 입증한 것은 아니다. [`schema_drift.py`](../../src/hmda_reliability/reliability/evaluation/schema_drift.py)의 catch 경로가 `target_mutated=False`로 전달하는 부분은 정적으로 확인했으며 evaluator까지의 fault-injection은 별도 후속 회귀로 남긴다.

### R-DET-01 — Zero Threshold False Positives

[이전 정적 리뷰](06-review-reliability-detection-boundaries.md)를 실제 `detect_basic_incidents` 호출로 확인했다. Row count=100, income null rate=0.2가 동일하고 두 threshold가 0이면 volume_drop/null_spike 모두 발생했다. Row만 99로 줄인 경우와 null만0.21로 늘린 경우에도 변화 없는 다른 metric을 오탐했다. 기본 threshold의 기존 9 tests는 통과했다. Zero의 의미는 후속 owner가 명시해야 한다. 이 감사는 drop/spike를 실제 악화로 해석하지만 inclusive threshold 문구만으로 변화 없음까지 허용한다고 해석할 여지가 있으므로, 0을 금지할지 또는 양의 변화에만 적용할지 계약과 함께 결정한다. Baseline에 없는 column 처리 R-DET-02는 계속 spec 결정이 필요한 Note이며 확정 버그로 올리지 않는다.

### R-TD-02 — SDK Adapter Negative Control

[`test_provider.py`](../../tests/runtime_ai/test_provider.py)의 RecordingTransport는 request/wire payload를 검사하지만 실제 [`provider.py`](../../src/hmda_reliability/runtime_ai/provider.py)의 `_OpenAIChatCompletionTransport.create`가 SDK kwargs를 별도로 구성한다. Source와 Runtime AI tests를 임시 directory로 복사한 뒤 **그 adapter의** `model=request.model` 하나만 `model="audit-wrong-model"`로 교체했다. 기존 31 tests가 모두 통과했고 session 종료 시 import된 provider 경로가 해당 격리 copy임을 assertion으로 확인했다. 이 결과는 테스트 공백의 증거이며 현재 정상 mapping 자체가 잘못됐다는 주장은 아니다. 실제 SDK client를 fake로 두고 adapter를 통과하는 deterministic tests가 적절하다.

## Reproduction Recipes

아래 probe는 감사용 임시 파일로 저장해 같은 locked 환경에서 실행한다. Production 또는 기존 tests를 수정하지 않는다. Contract probe의 expected result는 현재 구현에서 RED다.

```bash
uv run --no-sync pytest /tmp/pr252_probes.py -q -s
uv run --no-sync python /tmp/pr252_lock_probe.py
```

### Contract Probes — `/tmp/pr252_probes.py`

```python
"""Temporary audit probes; expected contracts, no production mutation."""
from datetime import UTC, datetime
from pathlib import Path
import duckdb
import pytest
from hmda_reliability.hmda_data.ingestion import load_hmda_loans_partition
from hmda_reliability.reliability import DetectionRequest, DetectionThresholds, ProfileSnapshot, detect_basic_incidents, RemediationDraftRequest, create_remediation_draft
from hmda_reliability.review_ai.service import review_null_spike
from hmda_reliability.review_ai.contracts import PromptIdentity
from hmda_reliability.runtime_ai.contracts import ProviderResponse
from hmda_reliability.runtime_ai.settings import RuntimeAISettings

def profile(**kw):
    values=dict(snapshot_id='audit-profile',asset_name='raw.hmda_loans',partition='2025',observed_at=datetime(2026,10,15,tzinfo=UTC),row_count=100,null_rates={'income':0.2},schema_hash='stable',freshness_at=None,freshness_status='unavailable')
    values.update(kw)
    return ProfileSnapshot(**values)

@pytest.mark.parametrize(('updates','expected'),[({},[]),({'row_count':99},['volume_drop']),({'null_rates':{'income':0.21}},['null_spike'])])
def test_zero_threshold(updates,expected):
    results=detect_basic_incidents(DetectionRequest(baseline=profile(),current=profile(**updates),thresholds=DetectionThresholds(volume_drop_ratio=0,null_spike_delta=0)))
    assert [r.incident.incident_type for r in results]==expected

def test_reordered_partition_preserves_values(tmp_path):
    p=tmp_path/'year_2025.csv'
    p.write_text('activity_year,loan_purpose,action_taken,loan_amount,income,state_code,county_code\n2025,1,1,350000,120,CA,06001\n')
    with duckdb.connect(str(tmp_path/'test.duckdb')) as con:
        assert load_hmda_loans_partition(con,[p],2025)==1
        assert con.execute('SELECT loan_amount,income FROM raw.hmda_loans').fetchall()==[(350000,120)]
        p.write_text('activity_year,loan_purpose,action_taken,income,loan_amount,state_code,county_code\n2025,1,1,120,350000,CA,06001\n')
        assert load_hmda_loans_partition(con,[p],2025)==1
        assert con.execute('SELECT loan_amount,income FROM raw.hmda_loans').fetchall()==[(350000,120)]

@pytest.mark.parametrize('content',['['*10000+'0'+']'*10000,'{"n":'+'1'*5000+'}'],ids=['deep-json','huge-int'])
def test_invalid_json_resource_limits_are_persisted(tmp_path,content):
    d=detect_basic_incidents(DetectionRequest(baseline=profile(null_rates={'income':0.01}),current=profile(null_rates={'income':0.21})))[0]
    draft=create_remediation_draft(RemediationDraftRequest(incident=d.incident,evidence=d.evidence))
    class Provider:
        calls=0
        def invoke(self,messages):
            self.calls+=1
            return ProviderResponse(content=content,attempt_count=1,latency_ms=1)
    provider=Provider()
    settings=RuntimeAISettings(base_url='http://localhost:11434/v1',api_key='test-only',model='audit-model')
    assert len(content.encode())<settings.max_output_bytes
    try:
        result=review_null_spike(incident=d.incident,evidence=[d.evidence],draft=draft,prompt_identity=PromptIdentity(),project_revision='b9f9c7657f1d65e5b583ed16afd035ec218e1ed6',settings=settings,provider=provider,artifact_root=tmp_path,invocation_id_factory=lambda:'audit-json')
    finally:
        print('provider_calls=',provider.calls,'persisted_json=',list(tmp_path.rglob('*.json')))
    assert result.status=='validation_failed'
    assert result.invocation_path is not None and result.invocation_path.exists()
```

### Unlock Probe — `/tmp/pr252_lock_probe.py`

```python
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import runpy, fcntl
from hmda_reliability import reliability
from hmda_reliability.data_platform.duckdb import DuckDBConnectionManager
helpers=runpy.run_path('tests/reliability/test_schema_recovery_executor.py')
with TemporaryDirectory() as d:
    request=helpers['_request'](Path(d),target_state='before')
    original=fcntl.flock
    def fault(file,operation):
        if operation==fcntl.LOCK_UN and Path(file.name).name==f'.{request.target_database_path.name}.mutation.lock':
            raise OSError('audit injected unlock failure')
        return original(file,operation)
    with patch('fcntl.flock',fault):
        try:
            reliability.execute_approved_schema_recovery(request)
        except reliability.SchemaRecoveryValidationError as e:
            print('error_metadata',vars(e))
    with DuckDBConnectionManager(request.target_database_path) as c:
        actual=reliability.create_table_state_identity(c,request.proposal.table_name)
    print('target_matches_committed_after',actual==request.proposal.expected_after_state)
    replay=reliability.execute_approved_schema_recovery(request)
    print('replay',replay.mutation_state,replay.reconciliation_action)
```
