---
type: report
title: "MVP Baseline Remediation"
description: "첫 current-revision baseline의 실패 원인과 허용된 최소 test remediation을 기록한다."
---

# MVP Baseline Remediation

## Observed Result

`da579b84f670c8149a679cf3040d1466c2cf8a9b` baseline: **602 passed, 3 failed, 1 skipped**, 166.60 seconds. Log/JUnit은 `.local/pr239/proofs/da579b84f670c8149a679cf3040d1466c2cf8a9b/baseline/`에 보존한다. Windows npm/Node test의 platform skip은 Linux에서 미검증이며 PASS로 바꾸지 않는다.

## Research

`tests/scripts/test_ci_classifier.py`의 세 active-Change test가 `orchestration-quality-gate`의 실제 repository 존재를 가정한다. 해당 directory가 없으므로 classifier는 active path에 bulk fallback을 반환하고 canonical Spec에서 related Change를 찾지 못한다. `.github/workflows/classify_changes.sh`의 fail-safe behavior는 타당하며 test setup이 mutable inventory에 의존한다.

Observer 없이 focused classifier module에서도 같은 실패를 재현한다. Baseline의 Data Lake/Airflow/Recovery/Review AI 실행 성공은 baseline 실패를 상쇄하지 않는다.

## Plan And Admission

- **Disposition:** `current_required`, baseline prerequisite gap.
- **Scope:** 기존 classifier test helper와 active/absent/mixed OpenSpec fixture만 수정한다.
- **Approach:** optional working root와 `tmp_path` tree를 사용하여 실제 classifier를 실행한다. 기존 target/bulk assertion을 보존한다.
- **Validation:** focused classifier, related scripts suite, Ruff/format/type, OpenSpec strict; independent review 후 새 SHA에서 baseline과 focused rerun을 실행한다.
- **Exclusion:** production classifier 변경, CI scope 확장, dependency 변경, assertion 완화와 skip 추가.

## Loop Transition

Outer Loop 3/30의 runtime Review에서 baseline failure를 확인해 Research/Plan으로 되돌렸다. Remediation은 active `data-operations-prove-current-revision-mvp` Change가 소유하며 `prj-spec-driven-tdd-rpi`가 test implementation 구간을 제어한다. New capability나 delta Spec은 없다.

## Targeted Validation

- `uv run pytest tests/scripts/test_ci_classifier.py -q -p no:sugar --tb=short`: **49 passed** after fixture correction; before correction **3 failed, 46 passed**.
- `uv run pytest tests/scripts`: existing script import setup produced 4 collection errors (`ModuleNotFoundError: No module named 'scripts'`).
- `uv run python -m pytest tests/scripts -q -p no:sugar --tb=short -ra`: **121 passed, 1 skipped**. Python module invocation includes repository root; no import/config patch was made. Windows skip remains Not Verified.
- Ruff check/format and `ty check tests/scripts/test_ci_classifier.py`: passed.
- Old baseline persisted Airflow evidence: all five observations captured without capture error. Recovered database has 10 raw and staging rows, zero income nulls and two mart groups. These observations remain historical until a new final SHA is tested.
