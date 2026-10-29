---
type: openspec-spec-driven-tdd-design
category: design
title: Budget Staged Review Execution
description: 전송의 phase timeout과 협력적 실행 예산을 기존 동기 호출 경계에 적용합니다.
---

## Technical Delta

Runtime의 기존 timeout_seconds와 Python API 기본값은 유지한다. 선택적 connect_timeout_seconds·read_timeout_seconds를 추가하고 SDK 공개 Timeout으로 connect/read/write/pool을 설정한다. 호출별 budget_seconds는 logical invoke의 retry·backoff를 포함하며 요청마다 남은 예산으로 phase 한도를 줄인다. SDK retry는 0이다. APITimeoutError를 APIConnectionError보다 먼저 분류한다.

StagedExecutionSettings는 ReviewAISettings의 prompt 제한과 분리한다. 단계의 deadline은 단계 시작+stage_budget과 workflow 시작+workflow_budget 중 빠른 값이다. service와 adapter의 monotonic clock을 주입해 실제 대기 없는 테스트를 수행한다. 반환된 응답은 Runtime에서 시간 초과만으로 버리지 않고 service가 exact raw를 저장한 뒤 예산을 확인한다. SDK가 반환하지 않은 미완성 body는 보존할 수 없다.

Phase timeout은 연결·쓰기·읽기·풀의 각 대기 제한으로 총 wall time과 다르다. 동기 호출이 deadline을 넘길 수 있으므로 예산은 후속 호출 진입과 결과 채택을 제어한다. 강제 취소용 thread·process framework는 도입하지 않는다.

새 phase 설정은 기존 sanitized configuration에 optional로 추가하고 과거 누락값은 None으로 읽는다. Staged manifest에 별도 optional execution_settings와 elapsed_ms, 단계 기록에 budget_seconds·elapsed_ms를 추가한다. 현재 실행 검증은 실제·예상 configuration을 같은 typed schema로 정규화한다. 기존 prompt·canonical input·과거 저장 파일은 변경하지 않는다.

## Live Defaults

Live staged는 connect 10초·read 300초·단계 360초·전체 1200초·retry 0회를 시작값으로 둔다. 명시적 READ_TIMEOUT이 최우선이며 staged에서 생략하면 기존 TIMEOUT의 명시값, 그것도 없으면 300초다. Structured는 새 phase를 명시하지 않으면 None으로 두어 기존 TIMEOUT fallback을 유지한다. 쓰기·풀은 기존 TIMEOUT 기본 30초를 따른다. Python Runtime 및 structured 기본 30초·retry 1회는 유지한다. 시작값은 검증된 모델 성능이나 단계별 최대 시간을 보장하지 않는다.
