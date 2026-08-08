# PR #19 심층 코드 리뷰 보고서

**파일명:** `pr-19-hmda-eda-contract-evidence-readiness-deep-review.md`  
**대상:** `mols3131d/project-pivot` PR #19  
**작성일:** 2026-08-07 (KST)  
**판정:** **Changes Requested**

## 1. 요약

PR #19는 HMDA EDA를 six-core contract로 축소하고, complete-key grain 계산, YAML/정적 HTML 탐색, JSON·Markdown evidence 통합을 도입한다. 핵심 계산 로직의 방향은 적절하지만, actual-source evidence provenance와 readiness 집계에 신뢰성 결함이 남아 있어 현재 상태로는 Foundation 완료 근거로 사용하기 어렵다.

## 2. 긍정적 변경

- `county_code`를 required EDA contract에서 제거했다.
- grain distinct group count에서 null key 행을 명시적으로 제외했다.
- `duration_seconds`가 distribution, numeric summary, grain 계산까지 포함한다.
- actual-source JSON과 Markdown을 동일 evidence 객체에서 생성한다.
- Marimo 의존 경로를 제거하고 YAML 및 standalone HTML 출력으로 단순화했다.

## 3. 주요 발견

### F-01 — Evidence provenance 불충분 · Blocker

커밋된 evidence의 `repository_revision`은 PR head가 아닌 이전 revision이며 `-dirty`가 붙어 있다. dirty working tree의 실제 변경 내용은 복원할 수 없으므로 해당 evidence는 리뷰 대상 코드를 재현하거나 입증하지 못한다.

또한 dirty 판정이 `git diff --quiet`에만 의존하면 staged 변경과 untracked 파일을 놓칠 수 있다.

**필수 조치**

- `git status --porcelain`이 비어 있지 않으면 evidence 생성을 실패시킨다.
- clean PR head에서 actual-source evidence를 다시 생성한다.
- evidence revision과 현재 `HEAD` 일치를 CI에서 검증한다.

### F-02 — Readiness 총계 불일치 · Blocker

YAML 항목 합계는 Implementation `186/189`, Verification `150/152`이지만 Markdown에는 각각 `182/189`, `146/152`로 기록되어 있다.

**필수 조치**

- YAML을 readiness의 단일 원천으로 지정한다.
- Markdown을 YAML에서 자동 생성한다.
- 개별 항목 합계와 총계가 일치하는 회귀 테스트를 추가한다.

### F-03 — 제거된 freshness 계산 잔존 · Major

사양은 freshness를 EDA 범위에서 제거했지만 `observed_at` 컬럼이 있으면 여전히 `MAX(observed_at)`을 계산한다. 결과를 반환하지 않으므로 불필요한 scan이며 계약과 구현이 불일치한다.

**필수 조치**

- freshness 관련 query fragment를 제거한다.
- `observed_at`이 포함된 입력에서도 freshness 계산 및 출력이 없음을 검증한다.

### F-04 — JSON/Markdown 쓰기 비원자성 · Major

JSON 저장 후 Markdown 저장이 실패하면 두 artifact가 서로 다른 실행 결과를 가질 수 있다.

**필수 조치**

- 두 파일을 임시 경로에 완전히 작성·검증한 후 `os.replace`로 교체한다.
- 두 번째 파일 쓰기 실패를 주입해 기존 artifact pair가 보존되는지 검증한다.

### F-05 — 변경 범위 혼합 · Minor

HMDA EDA 변경에 `scripts/wsl-status.sh`가 포함되어 있어 리뷰와 revert 단위가 불필요하게 커졌다.

**권고 조치**

- 별도 PR로 분리한다.
- CI에서 PR scope label 또는 경로 기반 ownership check를 적용한다.

## 4. 병합 조건

1. clean PR head 기반 actual-source evidence 재생성
1. staged/untracked를 포함하는 dirty-tree 차단
1. readiness Markdown 자동 생성 및 합계 테스트
1. freshness query 완전 제거
1. evidence pair atomic write 적용
1. actual-source 생성 경로를 포함한 CI 검증 추가

## 5. 최종 판단

계산 로직은 개선됐으나 evidence와 readiness의 신뢰 계층에 blocker가 남아 있다. 위 병합 조건을 충족한 뒤 재리뷰하는 것이 타당하다.
