---
type: review
title: SDK Retry Implementation Review
description: SDK 재시도 분류 회귀 다섯 사례의 실제 실행 경계·독립 oracle과 negative-control 근거를 독립 검토한 결과입니다.
tags:
  - testing
  - runtime-ai
---

# SDK Retry Implementation Review

> [!NOTE]
> **Assessment: clear.** 독립 review-lead가 quality·adversarial의 분석을 대조했다. 현재 범위의 `current_required`, 필요한 scope 결정 또는 specialist coverage gap은 없다.

- **Target:** [PR #258](https://github.com/mols3131d/hmda-data-reliability/pull/258)의 SDK retry 테스트와 계획·실행 근거.
- **Revision:** baseline `a8864328e8a92316d32cad386746c3c5f4b983cd` → `eb71f46e23a532d66c1a5ff8ce85c1af03965c03`. 테스트 Git blob `d7cc1fdcae6ca840cc56efb82a416e6bb88a0c81`.
- **Scope:** 변경 테스트·직접 연결된 SDK/adapter·기존 Spec·Inbox 문서 2개. 후속 artifact 경로 변경과 CI 전달 상태는 호출자가 별도로 확인한다.

## Findings

채택된 material finding은 없다. 실제 SDK 오류 변환과 production adapter의 retry 판단이 테스트 경로에 남아 있고, HTTP만 대체한다. 고정 호출 횟수·public attempt 수·typed error·정확한 content가 서로 다른 오류를 구분한다. 기존 budget 0 세 사례와 SDK hidden retry 비활성화 검증도 유지한다.

문서는 다섯 새 사례와 세 mutation의 검출 범위로 주장을 제한한다. Live provider나 모든 가능한 오류 분류를 검증한 것으로 확대하지 않는다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | Independent static review | quality/adversarial 모두 완료; lead가 source·Spec·safeguard와 후보를 대조 |
| ✅ Pass | State identity | baseline/head·테스트 blob·제한된 diff 및 `git diff --check` 직접 확인 |
| ✅ Pass | Raw caller evidence inspection | [실행 근거](01-report-sdk-retry-validation.md)의 실제 script/log를 확인해 격리 40 passed, mutation별 1/2/2 failed와 import guard·실제 실패·원본 provider hash 보존을 대조 |
| ⚪ Not Verified | Reviewer runtime rerun | reviewer 환경의 uv 및 interpreter 부재로 collection 전 exit 127; log 검토를 직접 재실행으로 표현하지 않음 |

## Limits

Lint·type·Runtime AI suite와 mutation 실행은 호출자의 검증이며 reviewer 자체 실행과 구분한다. 전체 suite·live provider·후속 revision의 CI는 이 assessment가 검증하지 않았다. 소스·테스트·설정·Spec의 수정 없이 검토했다. 인간의 Ready 전환·승인·병합을 대신하는 판정은 아니다.
