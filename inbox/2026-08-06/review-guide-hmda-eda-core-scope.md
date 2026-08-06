# HMDA EDA Core Scope 변경 사항 검토 가이드

이 문서는 `feat/hmda-eda-baseline-reduce-core-scope` 브랜치에서 방금 완료된 변경 사항을 사용자가 직접 확인하고 병합(Merge)을 결정하기 위한 행동 지침(Actionable Guide)입니다.

## 1. 자동화 테스트(CI) 결과 확인

가장 먼저 코드가 기존의 의도된 동작을 깨뜨리지 않았는지, 통합 테스트가 정상 작동하는지 확인합니다.

```bash
uv run pytest tests/hmda_data/eda/ -v
```

**👀 무엇을 확인해야 하나요?**

- 총 14개의 테스트가 모두 패스(GREEN)하는지 확인합니다.
- 특히 `test_eda_notebook.py`의 `test_valid_fixture_completes_notebook_rendering`과 `test_malformed_fixture_reports_notebook_failure`가 통과하는지 확인합니다. (오류 상황을 거짓으로 통과시키지 않고 제대로 잡아내는 것을 의미합니다)

## 2. Marimo 노트북 UI 및 동작 검토 (Interactive Check)

노트북 코드에 하드코딩되어 있던 Dead Code를 UI 위젯으로 교체했습니다. 이 부분이 의도대로 동작하는지 확인합니다.

```bash
uv run marimo edit notebooks/eda_mo.py
```

**👀 무엇을 확인해야 하나요?**

- 화면 상단 입력 범위 쪽에 **"샘플 데이터 사용" (UI 체크박스)** 가 생겼는지 확인합니다.
- 해당 체크박스를 토글(On/Off)했을 때, `data_path`가 `data/sample/hmda/year_2025.csv`와 `data/raw/hmda/year_2025.csv`로 올바르게 전환되는지 확인합니다.
- "EDA 계산 실행"을 체크했을 때 노트북 하단에 핵심 6개 컬럼에 대한 통계 정보만 깔끔하게 떨어지며, 이전의 불필요한 지표(anomaly, freshness 등)가 노출되지 않는지 확인합니다.

## 3. 코드 삭제 내역 검토 (Diff Check)

이번 작업의 주요 목적 중 하나인 "불필요한 코드 수축"이 제대로 반영되었는지 확인합니다.

```bash
git diff main...HEAD --stat
```

**👀 무엇을 확인해야 하나요?**

- 삭제된 파일 목록에 아래 항목들이 포함되어 있는지 눈으로 확인합니다.
  - `src/project_pivot/hmda_data/eda/fixture.py`
  - `src/project_pivot/hmda_data/eda/memory.py`
  - `scripts/prepare_hmda_eda_fixture.py`
  - `scripts/run_hmda_eda_memory.py`
  - `tests/hmda_data/eda/test_eda_memory.py` 등

## 4. 리뷰 문서 확인

AI 에이전트(Quality & Adversarial)가 남긴 리뷰 기록을 읽어보고, 수용된 위험(Accepted Risk)을 인지합니다.

- **리뷰 보고서**: `reviews/hmda-eda-baseline-reduce-core-scope.md`
- **인지해야 할 위험**: Memory workload 테스트 삭제로 인해, 이후 무거운 쿼리가 추가될 경우 1,350만 건 처리 시 OOM(Out of Memory) 방어막이 없다는 점이 기록되어 있습니다.

---

## ✅ 다음 단계 (Next Steps)

위 4가지 사항을 모두 확인하셨고 기대한 대로 동작한다면, 다음 명령어를 통해 OpenSpec 변경 사항을 완전히 닫고 병합할 수 있습니다.

1. **OpenSpec 아카이브**

   ```bash
   openspec archive --change "hmda-eda-baseline-reduce-core-scope"
   ```

1. **Main 브랜치 병합 (선택 사항)**
   GitHub PR을 생성하거나, 로컬에서 main 브랜치로 병합(Merge)합니다.
