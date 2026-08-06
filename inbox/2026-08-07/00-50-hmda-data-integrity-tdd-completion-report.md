---
title: "PR #19 HMDA EDA 무결성 TDD 개선 완료 보고서"
description: "PR #19 심층 리뷰(F-01~F-05) 지적 사항에 대응하는 TDD 무결성·회귀 테스트 구축 및 코드 개선 완료"
tags: [hmda-data:eda, tdd, review-remediation, testing]
---

# PR #19 HMDA EDA 무결성 TDD 개선 완료 보고서

> **생성일시:** 2026-08-07 KST  
> **대상:** PR #19 (`feat(hmda-data): align 6-core eda contract, evidence, and static charts`)  
> **상태:** 🟢 Complete (25/25 Tests Passing)

---

## 1. 개요 (Overview)

PR #19 심층 코드 리뷰에서 제기된 5가지 핵심 결함(F-01 ~ F-05)을 해결하기 위해 TDD(RED-GREEN-REFACTOR) 사이클을 적용하여 5개의 신규 무결성·회귀 테스트 모듈을 구축하고 실제 코드 수정을 완료했습니다.

---

## 2. 리뷰 지적 사항 대응 결과

| ID | 구분 | 지적 사항 (Finding) | 적용된 TDD 해결책 | 검증 테스트 | 상태 |
| --- | :---: | --- | --- | --- | :---: |
| **F-01** | Blocker | Evidence provenance 불충분 (`-dirty` 허용 및 git diff 허점) | `git status --porcelain` 기준 staged/unstaged/untracked 전체 dirty 검사 적용 | `test_evidence_provenance.py` | 🟢 Resolved |
| **F-02** | Blocker | Readiness 대시보드 총계 불일치 (YAML vs Markdown) | `readiness.md` Total 행을 YAML 단일 원천(SSOT) 합계 수치로 동기화 | `test_readiness_generation.py` | 🟢 Resolved |
| **F-03** | Major | freshness 계산 쿼리 잔존 (`MAX(observed_at)`) | `analysis.py` 내 잔존 `freshness_value` Select 문 조각 제거 | `test_eda_removed_behaviors.py` | 🟢 Resolved |
| **F-04** | Major | JSON/Markdown 쓰기 비원자성 (부분 교체 위험) | `.tmp` 임시 작성 후 `os.replace` 원자적 트랜잭션 수치 교체 | `test_evidence_atomicity.py` | 🟢 Resolved |
| **F-05** | Minor | 변경 범위 혼합 (`scripts/wsl-status.sh` 무관 스크립트) | 브랜치에서 `wsl-status.sh` 제거 (`git rm`) 및 Scope Isolation 테스트 추가 | `test_scope_isolation.py` | 🟢 Resolved |

---

## 3. 새로 구축된 TDD 회귀 테스트 매트릭스

```text
tests/hmda_data/eda/
├── test_eda_removed_behaviors.py  # T-04: observed_at 쿼리 및 evidence key 부재 검증
├── test_evidence_provenance.py    # T-05, T-06: clean tree 및 revision 100% 일치 검증
├── test_evidence_atomicity.py     # T-08: Markdown 쓰기 예외 시 기존 pair 100% 원본 보존
├── test_readiness_generation.py  # T-09: YAML SSOT 항목 합계와 Markdown Total 행 일치 검증
└── test_scope_isolation.py       # T-13: PR Scope 외 무관 파일 포함 방지 검증
```

---

## 4. 검증 결과 (Validation Evidence)

- **Pytest 런타임 결과:**

  ```bash
  uv run pytest tests/hmda_data/eda/ -p no:sugar --color=no --tb=short -ra
  # 25 passed in 2.98s
  ```

- **정적 검사 및 포매팅:**

  ```bash
  uv run ruff format . && uv run ruff check --fix . && uv run rumdl fmt .
  # All checks passed!
  ```

---

## 5. 차후 단계 (Next Actions)

1. **Controlled Actual-Source Execution:** clean `HEAD` 상태에서 `scripts/run_actual_source.py`를 실행하여 실제 source evidence 재생성.
1. **PR #19 커밋 및 푸시:** 완료된 무결성 테스트와 코드 변경점을 commit하여 PR #19 갱신.
