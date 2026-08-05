---
title: "세션 종료 후 보존 사항과 검증 경계"
description: "다음 세션이 이어받아야 할 사실, 검증 결과와 미검증 hard-limit 경계를 기록한다."
date: 2026-07-31
---

# 세션 종료 후 보존 사항과 검증 경계

## 보존해야 할 구현 사실

- manifest는 schema, null map, expected invariant, activity-year cardinality/skew,
  file integrity를 실제 validation에서 강제한다.
- evidence validation은 7개 required EDA column을 모두 확인한다.
- malformed auxiliary output은 pass가 아니라 failed run으로 기록된다.
- per-run temporary directory는 success/failure 모두 cleanup 대상이다.
- report provenance는 fixture directory, manifest digest와 file digest를 포함한다.
- representative fixture 결과와 full-source memory safety는 별개의 주장이다.

## 실행된 validation

- HMDA EDA correctness slice: **32 passed, 1 deselected**
- Ruff: **통과**
- strict mypy: package/test와 standalone runner 모두 **통과**
- 변경 파일 Pylance diagnostics: **error 없음**
- 보고서 `rumdl fmt`: **통과**
- rumdl 실행 시 repository 설정의 `MD054: style` unknown-option warning이 표시됐다.

## 반드시 후속 실행할 hard-limit 검증

실제 documented hard-limit 환경에서 다음 runner를 별도로 실행해야 한다.

```bash
uv run python scripts/run_hmda_eda_memory.py
```

fixture가 없다면 먼저 다음을 실행한다.

```bash
uv run python scripts/prepare_hmda_eda_fixture.py
```

실행 후 다음 artifact를 보존한다.

- `fixture.manifest_sha256`
- 선언된 모든 fixture file의 SHA-256과 size
- systemd hard-limit, swap 0, timeout evidence
- DuckDB memory limit과 thread 수
- 세 run의 exit/resource/output status
- peak RSS, elapsed time, temp disk usage, failure reason
- 최종 assessment

## 미검증 경계

- 이번 보고서 작성 시점에는 실제 systemd user hard-limit 3-run workload를 다시
  실행하지 않았다.
- 따라서 5M-row 대표 fixture의 3 GiB process budget 통과를 주장하지 않는다.
- full source 약 4.8 GiB의 memory safety는 검증하지 않았다.
- raw HMDA source data와 reliability lifecycle은 이번 작업의 변경·검증 대상이 아니다.
