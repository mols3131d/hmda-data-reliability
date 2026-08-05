---
title: 'hmda-eda-baseline-review'
date: '2026-07-30'
type: 'code-review-summary'
---

## Summary

| 🟩 `PASS` | 🟥 `FAIL` | 🟧 `ERROR` | ⬜ `SKIP` |
| :---: | :---: | :---: | :---: |
| 3 | 1 | 0 | 0 |

검토 범위: `add-hmda-eda-baseline` 변경의 [notebooks/eda_mo.py](../../../../../project-pivot/notebooks/eda_mo.py), OpenSpec proposal/design/spec/tasks.

`p1` 1건. `ignore_errors=true`가 파싱 실패 행을 조용히 제외하고 그 결과를 volume 및 null baseline으로 표시한다. 파싱 손실을 경고하거나 reader를 fail-fast로 전환해야 한다.

검증: sample CSV HTML export 성공, baseline 섹션 5개 렌더링, `python -m ruff check notebooks/eda_mo.py` 통과, malformed CSV에서 3개 물리 행 중 1개가 제외되는 것을 재현했다.

## Details

| 🔴 `p0` | 🟠 `p1` | 🟡 `p2` | 🟢 `p3` | 🔵 `p4` |
| :---: | :---: | :---: | :---: | :---: |
| 0 | 1 | 0 | 0 | 0 |

---

### 🟠 [hmda-eda-ignored-parse-errors](hmda-eda-ignored-parse-errors.md)

[notebooks/eda_mo.py:81-83](../../../../../project-pivot/notebooks/eda_mo.py#L81-L83), [notebooks/eda_mo.py:153-181](../../../../../project-pivot/notebooks/eda_mo.py#L153-L181)

- **파싱 손실 baseline**: `ignore_errors=true`가 손상 행을 제외하지만, volume 및 null baseline에 제외 건수와 파싱 성공 행 기준이 표시되지 않는다.

  ---> **손실 가시화**: reader를 fail-fast로 전환하거나 물리 입력 행 수와 reader row count 차이를 경고로 출력한다.
