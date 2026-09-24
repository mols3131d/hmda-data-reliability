---
type: review
title: "PR #245 Review: Review AI Utility Evaluation"
description: "PR #245의 bounded context, utility evaluation evidence, create-only store와 revision provenance를 검토하고 병합 전 결함과 검증 한계를 기록합니다."
tags:
  - "domain:review-ai"
  - "capability:reliability-agentic-review"
  - "pull-request"
---

# PR #245 Review: Review AI Utility Evaluation

> [!IMPORTANT]
> **Blocked** — 현재 head에서 병합 전 수정이 필요한 Major finding 3건과 Minor finding 2건을 확인했습니다. 또한 `review-quality`와 `review-adversarial` specialist capability를 이 런타임에서 사용할 수 없어 formal dual-perspective 독립 검토 gate를 완료하지 못했습니다.

- **Target** — [PR #245: `feat(review-ai): prove MVP utility evaluation`](https://github.com/mols3131d/hmda-data-reliability/pull/245)
- **Revision** — base `1cff7550ad88e5506b96c49882bf915f51662e4d` → head `17d6dbe21daef38f78cd8ab6631c1e56b5b4672a`
- **Scope** — 변경된 Review AI 구현·테스트·offline proof runner·OpenSpec delta와 직접 연결된 prompt/provenance/store 경계를 검토했습니다. Live provider 호출은 실행하지 않았습니다.

PR 상태는 검토 시점에 `OPEN`, `Draft`, `CLEAN`, `MERGEABLE`이었고, [CI Lite check](https://github.com/mols3131d/hmda-data-reliability/actions/runs/35223279640/job/105208433524)은 해당 head에서 성공했습니다.

## Findings

| ID | Severity | Finding | Action |
| --- | --- | --- | --- |
| F1 | 🟠 Major | Bounded context가 provider canonical input과 invocation provenance의 원본 `Evidence.payload`를 제한하지 않음 | Provider input과 저장 evidence를 bounded projection만 사용하도록 변경하고 raw payload 회귀 테스트 추가 |
| F2 | 🟠 Major | Human utility 점수와 control/comparison evidence가 실제 output에 연결되지 않아 false-green proof를 허용함 | 실제 control/output 또는 검증 가능한 digest를 binding하고, 모든 control의 rubric completeness와 expected contribution을 독립 검증 |
| F3 | 🟠 Major | `load_proof()`가 `proof_id`를 검증하지 않아 artifact root 밖의 파일을 읽을 수 있음 | 안전한 ID 검증과 root-bound path construction을 `load_proof()`에도 적용 |
| F4 | 🟡 Minor | directory fsync 실패가 보고되어도 이미 연결된 final evidence 파일이 남음 | fsync 실패 시 final path를 rollback하거나 indeterminate durability를 명시적으로 다룸 |
| F5 | 🟡 Minor | proof case의 Git revision이 실제 `AgenticReviewInput.project_revision`과 묶이지 않음 | 동일 revision을 input까지 전달하고 case/input/digest 일치 invariant를 검증 |

## Details

### F1 · Bounded context가 provider input을 실제로 제한하지 않음

🟠 Major

#### F1 Locations

- [`src/hmda_reliability/review_ai/prompt.py`](../../src/hmda_reliability/review_ai/prompt.py#L98)
  - `build_canonical_input`
  - 원본 `evidence[*].payload` projection과 `review_context` 추가
- [`src/hmda_reliability/review_ai/service.py`](../../src/hmda_reliability/review_ai/service.py#L261)
  - `_ReviewSession._build_record`
- [`openspec/changes/review-ai-utility-evaluation/tasks.md`](../../openspec/changes/review-ai-utility-evaluation/tasks.md#L19)
  - provider user data와 invocation evidence가 같은 bounded context projection을 사용해야 한다는 task

#### F1 Evidence

`build_canonical_input()`은 bounded `review_context`를 추가하지만 동시에 allowlist의 `payload` 전체를 `canonical_input["evidence"]`에 복사합니다. `_build_record()`는 이 canonical input을 그대로 invocation evidence에 저장합니다.

직접 재현한 결과도 `raw_log`가 provider canonical input에는 존재하고 bounded context facts에서는 제거되었습니다(`raw_log_in_provider_input=True`, `raw_log_in_bounded_context=False`, prompt 103,944 bytes).

#### F1 Impact

`max_context_bytes`는 context projection만 제한하고 provider에 전달·저장되는 원본 payload에는 적용되지 않습니다. 따라서 raw log, unbounded field 또는 bounded context allowlist 밖의 정보가 provider 입력과 provenance에 포함될 수 있어 새 Review Context safety contract를 충족하지 않습니다.

#### F1 Action

Provider canonical input과 invocation provenance에서 원본 `Evidence.payload`를 제거하고 bounded projection을 canonical source로 사용합니다. raw/unbounded payload와 allowlist 밖 field가 provider message 및 persisted record에 남지 않는 회귀 테스트를 추가해야 합니다.

### F2 · Utility 평가가 실제 output과 연결되지 않음

🟠 Major

#### F2 Locations

- [`src/hmda_reliability/review_ai/evaluation.py`](../../src/hmda_reliability/review_ai/evaluation.py#L111)
  - `UtilityControl`
- [`src/hmda_reliability/review_ai/evaluation.py`](../../src/hmda_reliability/review_ai/evaluation.py#L226)
  - `validate_quality_basis`
- [`src/hmda_reliability/review_ai/evaluation.py`](../../src/hmda_reliability/review_ai/evaluation.py#L192)
  - `UtilityProofCase`와 proof bundle link validation
- [`scripts/run_review_ai_utility_proof.py`](../../scripts/run_review_ai_utility_proof.py#L82)
  - hard-coded positive/negative control와 baseline/candidate score 생성

#### F2 Evidence

`UtilityControl`은 expected outcome과 `HumanUtilityEvaluation`의 점수·label만 보존하며 실제 positive/negative output, output digest 또는 expected contribution을 보존하지 않습니다. `validate_quality_basis()`는 평가 점수에서 `pass`/`fail`을 계산해 expected label과 비교할 뿐 실제 control 내용은 확인하지 않습니다.

Runner는 positive control에 모든 점수 `2`, negative control에 모든 점수 `0`, baseline에 `0`, candidate에 `2`를 미리 넣습니다. `UtilityProofCase`의 baseline/candidate output digest와 `expected_contributions`는 저장되지만 comparison 또는 bundle validation에서 해당 output과의 일치 여부를 검증하지 않습니다.

추가로 불완전한 negative control(`scores=()`)도 `passed()`가 `False`라는 이유로 expected `fail`과 일치하여 `quality_basis.valid=True`가 됩니다. 즉 `negative_is_complete=False`인데도 observed outcome은 `fail`이고 failure code가 없습니다.

#### F2 Impact

임의의 output이나 불완전한 negative control에도 `compared`/`accept` proof가 생성될 수 있습니다. 이 evidence는 사람이 실제 utility를 평가했다는 사실과 candidate output의 utility contribution을 독립적으로 증명하지 못해 MVP Utility Proof를 false green으로 만들 수 있습니다.

#### F2 Action

Control과 baseline/candidate evaluation을 실제 output 또는 검증 가능한 output digest·fixture identity에 연결하고, output의 contribution kind와 `expected_contributions`를 독립 oracle로 검증해야 합니다. 모든 control은 다섯 criterion이 완전해야 하며, negative control은 단순 restatement fixture라는 내용도 재구성 가능해야 합니다.

### F3 · `load_proof()` path traversal

🟠 Major

#### F3 Locations

- [`src/hmda_reliability/review_ai/evaluation_store.py`](../../src/hmda_reliability/review_ai/evaluation_store.py#L95)
  - `load()`은 `path_for()`를 통해 `_SAFE_ID`를 확인함
- [`src/hmda_reliability/review_ai/evaluation_store.py`](../../src/hmda_reliability/review_ai/evaluation_store.py#L100)
  - `load_proof()`는 `proof_id`를 검증하지 않고 path를 조립함

#### F3 Evidence

`load_proof()`는 `f"{proof_id}.json"`을 artifact root 하위 path에 직접 삽입합니다. 반면 `path_for()`와 `load()`는 `_SAFE_ID.fullmatch()`로 traversal token을 차단합니다.

#### F3 Impact

호출자가 `../../`가 포함된 proof ID를 제공하면 configured `artifact_root` 밖의 JSON 파일을 읽어 `UtilityProofBundle`로 parse하려고 시도할 수 있습니다. Utility evidence store의 artifact 경계와 caller가 기대하는 read scope가 깨집니다.

#### F3 Action

`proof_id`에 동일한 safe-ID 검증을 적용하고, `path_for_proof()` 같은 단일 root-bound helper를 `write_proof()`와 `load_proof()`가 함께 사용하도록 변경해야 합니다.

### F4 · Directory fsync 실패 후 final evidence 잔여

🟡 Minor

#### F4 Locations

- [`src/hmda_reliability/review_ai/evaluation_store.py`](../../src/hmda_reliability/review_ai/evaluation_store.py#L75)
  - hard link 후 `_fsync_directory()` 호출
- [`src/hmda_reliability/review_ai/store.py`](../../src/hmda_reliability/review_ai/store.py#L100)
  - 기존 invocation store의 fsync 실패 rollback 비교 기준

#### F4 Evidence

`UtilityEvidenceStore._write()`는 temporary file을 fsync한 뒤 final path로 hard link하고 directory fsync를 수행합니다. Directory fsync에서 `OSError`가 나면 outer handler가 `UtilityEvidenceStoreError`를 반환하지만 final path를 unlink하지 않습니다. 기존 invocation store는 같은 단계에서 final path를 rollback합니다.

#### F4 Impact

호출자는 write failure를 받지만 evidence 파일은 남습니다. 재시도는 create-only identity collision으로 실패할 수 있고, 실제 artifact가 durable한지 caller가 판정할 수 없는 상태가 됩니다.

#### F4 Action

Directory fsync 실패 시 final link를 rollback하는 경로를 추가하고, rollback 실패도 명시적으로 보존·보고해야 합니다. fsync 실패를 주입하는 store regression test가 필요합니다.

### F5 · Proof revision provenance가 실제 input과 불일치

🟡 Minor

#### F5 Locations

- [`scripts/run_review_ai_utility_proof.py`](../../scripts/run_review_ai_utility_proof.py#L168)
  - CLI가 현재 Git HEAD를 `UtilityProofCase.project_revision`에 기록
- [`scripts/run_review_ai_utility_proof.py`](../../scripts/run_review_ai_utility_proof.py#L231)
  - `_build_review_input()`에 input 생성
- [`scripts/run_review_ai_utility_proof.py`](../../scripts/run_review_ai_utility_proof.py#L239)
  - input `project_revision`은 고정 문자열

#### F5 Evidence

`main()`은 `_current_revision()`을 `build_representative_utility_proof()`에 전달하지만, builder 내부의 `AgenticReviewInput`은 항상 `"utility-proof-fixture-revision"`을 사용합니다. `UtilityProofCase.project_revision`과 input revision의 일치를 검증하는 invariant도 없습니다.

#### F5 Impact

Proof가 현재 Git revision에서 생성됐다고 표시되어도 실제 input snapshot provenance를 그 revision에 귀속할 수 없습니다. 동일한 case/output digest를 다른 revision에 잘못 attribution할 수 있어 replay evidence의 신뢰성이 낮아집니다.

#### F5 Action

revision을 `_build_review_input()`까지 전달하고 input, case, output/comparison evidence가 같은 non-empty revision을 사용하도록 contract와 test를 연결해야 합니다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | Focused Review AI tests | `UV_CACHE_DIR=/tmp/uv-cache uv run --no-sync pytest -q tests/review_ai tests/scripts/test_review_ai_utility_proof.py` → `101 passed` |
| ✅ Pass | Offline representative proof | temporary artifact root에서 `rubric_v1` controls와 comparison `compared`/`accept` 생성 확인 |
| ✅ Pass | Ruff | changed Review AI/script 범위 `ruff check` 통과, `ruff format --check` → `26 files already formatted` |
| ✅ Pass | Type check | changed Review AI/script 범위 `ty check` 통과 |
| ✅ Pass | Diff hygiene | `git diff --check 1cff755..HEAD` 통과 |
| ✅ Pass | Remote CI | PR head `17d6dbe...`의 CI Lite check 성공 ([run 35223279640](https://github.com/mols3131d/hmda-data-reliability/actions/runs/35223279640/job/105208433524)) |
| ❌ Fail | Full repository suite | `644 passed, 1 skipped, 5 failed`; 5건 모두 `tests/orchestration/test_airflow_dagrun.py`의 60초 Airflow timeout으로 변경 범위 밖에서 발생 |
| ⚪ Not Verified | OpenSpec strict validation | pinned OpenSpec command가 30초 이상 무출력 대기하여 중단 |
| ⚪ Not Verified | Live provider proof | PR의 명시적 offline boundary에 따라 provider 호출을 실행하지 않음 |

## Risks and Limits

- `review-lead`가 요구한 `review-quality`와 `review-adversarial` specialist 결과를 이 런타임에서 받을 수 없어 formal dual-perspective 독립 검토는 완료되지 않았습니다. 직접 분석은 그 coverage의 대체로 취급하지 않았습니다.
- Full suite timeout은 PR 변경 파일이 아닌 기존 orchestration 실행 경로의 환경·런타임 제한으로 보이며, Review AI focused suite의 실패로 분류하지 않았습니다.
- PR/GitHub 상태와 CI는 위에 기록한 exact head에서 재확인했으며, 이후 head가 변경되면 이 보고서의 revision-specific 판단은 stale로 취급해야 합니다.
