---
type: review
title: PR #264 HMDA Source Required-Column Validation Review
description: PR #264의 파일별 필수 컬럼 검증, 적재 실패 계약과 회귀 테스트를 검토한 보고서입니다.
tags:
  - domain:hmda-data
  - capability:ingestion
---

# PR #264 HMDA Source Required-Column Validation Review

> [!IMPORTANT]
> **Blocked** — 이번 코드 검토에서 현재 PR의 수정을 요구할 확인된 결함은 없습니다. 다만 이 리뷰 세션에서는 별도의 독립 DualVantage 검토를 실행하거나 그 원본 증거를 확인하지 못해 독립 리뷰 게이트 충족을 확정할 수 없습니다. 기존 독립 검토 증거 확인과 인간 리뷰가 다음 단계입니다.

- **Target** — [PR #264 · 혼합 원천 파일의 필수 컬럼 검증](https://github.com/mols3131d/hmda-data-reliability/pull/264)
- **Revision** — base `34519fec148dd2ab38ddf0cc0157c3d3ed9f7247` / reviewed head `d5344abfce98f0c573b32d6e301076c56b9670c8`
- **Scope** — 파일별 schema 검증, Full/Partition load 호출 순서·실패 상태, 신규 회귀 테스트, [ingestion 계약](../../openspec/specs/hmda-data-ingestion/spec.md), 현재 revision의 CI 증거.

## Findings

확인된 `current_required` finding 없음. 변경 목적과 직접 관계없는 기존 동작은 신규 결함으로 분류하지 않았습니다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | Source contract 정적 대조 | [`_common.py`](../../src/hmda_reliability/hmda_data/ingestion/_common.py)의 `validate_source_required_columns`가 각 파일을 기존 reader로 `DESCRIBE`하여 필수 컬럼 누락 시 파일 경로와 누락 컬럼을 담은 `HMDADataValidationError`를 발생시킵니다. |
| ✅ Pass | Full/Partition 실패 경계 정적 검토 | [Full load](../../src/hmda_reliability/hmda_data/ingestion/full_load.py)는 교체 후 검증하는 기존 계약을 유지합니다. [Partition load](../../src/hmda_reliability/hmda_data/ingestion/partition.py)는 staging 후, 실제 대상 partition 교체 전에 파일별 검증을 수행합니다. |
| ✅ Pass | 회귀 테스트 설계 검토 | [Full load 테스트](../../tests/hmda_data/test_ingestion.py)와 [Partition 테스트](../../tests/hmda_data/test_ingestion_partition.py)에 CSV/Parquet 조합, 입력 순서, 누락 파일의 오류 context, 유효한 NULL, 빈 원천, 실패 후 대상 데이터·provenance 보존 검증이 있습니다. |
| ✅ Pass | GitHub CI Lite | [Run 39138889869](https://github.com/mols3131d/hmda-data-reliability/actions/runs/39138889869)의 `check`가 reviewed head `d5344ab`에서 성공한 것을 GitHub에서 확인했습니다. |
| ⚪ Not Verified | 로컬 재실행 | 이번 리뷰 세션에서 pytest·Ruff·ty·Tach를 직접 실행하지 않았습니다. PR 본문의 `1,025 passed, 3 skipped` 등은 작성자가 제공한 실행 기록입니다. |
| ⚪ Not Verified | 독립 DualVantage coverage | PR 설명에는 Verifier·Challenger 검토 완료로 기재되어 있으나 이번 세션에서 독립 reviewer를 실행하지 않았고 원본 실행 증거도 직접 검증하지 못했습니다. GitHub 제출 review는 확인 시점에 0건이었습니다. |

## Risks and Limits

- Full load의 validation-after-replacement 동작으로 잘못된 원천이 실패 후 target에 남을 수 있습니다. 이는 [기존 정본 계약](../../openspec/specs/hmda-data-ingestion/spec.md)의 의도된 호환성 경계로, 이번 변경의 `current_required` finding은 아닙니다.
- 위 판정은 명시된 reviewed head의 코드에 한정됩니다. 보고서 추가 등으로 PR head가 달라지면 새 revision의 CI 상태를 별도로 확인해야 합니다.
- 인간 승인·병합 판단은 이 문서가 대체하지 않습니다. 이 문서는 비정본 작업 기록입니다.
