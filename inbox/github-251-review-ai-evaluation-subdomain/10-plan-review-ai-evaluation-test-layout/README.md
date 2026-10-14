---
type: plan
title: Review AI Evaluation Test Layout Bundle
description: PR #251 평가 테스트 재배치의 조사, 실행 계획과 셀프 리뷰를 연결한다.
---

# Review AI Evaluation Test Layout

PR #251 평가 테스트 재배치를 위한 10번 번들이다. 평가 테스트 두 파일과 golden fixture를 `tests/review_ai/evaluation/`로 이동했다. 테스트 본문과 fixture byte는 유지했다.

- [00 Research](00-research.md) — 기존 테스트 설계, oracle, marker와 경로 소비자 조사
- [01 Review](01-review.md) — 최초 계획 revision의 발견 사항과 수정 이력
- [02 Improvement Plan](02-plan-improvement.md) — 리뷰를 반영한 이동 범위, 실행 순서와 검증 기준

## Local Validation

- 이동 전후 수집된 52개 case의 파일 경로를 매핑하면 node ID와 marker가 일치한다.
- 이동 후 두 module은 **52 passed**, `tests/review_ai tests/runtime_ai`는 **187 passed**다. 선택 Langfuse SDK test도 별도 실행에서 **1 passed**다.
- 세 파일의 SHA-256은 이동 전후 같고, CI selector는 새 경로를 `tests/review_ai`로 분류한다.

원격 CI와 review의 revision별 근거는 [PR #251](https://github.com/mols3131d/hmda-data-reliability/pull/251)이 소유한다.
