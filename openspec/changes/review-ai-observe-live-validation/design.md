---
type: openspec-spec-driven-tdd-design
category: design
title: Observe Live Review Validation
description: 선택적 stage 사건과 live 소유 heartbeat를 분리하고 실제 source checkout에서 revision을 확인합니다.
---

## Technical Delta

[Proposal](proposal.md)과 [live validation 요구사항](specs/reliability-agentic-review/spec.md)을 전제로 한다.

### D1. Stage Event Boundary

Service는 고정 stage identity와 `stage_started`·`provider_started`·`provider_finished`·`stage_finished`의 네 phase, 가능한 typed status와 attempt count만 담은 immutable event를 선택적 observer로 전달한다. Observer에 input·본문·설정·예외 object를 전달하지 않는다. 관찰용 경과 시간은 reporter의 monotonic clock으로 계산하며 event나 기존 result·manifest shape에 추가하지 않는다.

`provider_started`는 logical `invoke` 직전에, `provider_finished`는 그 호출을 감싼 `finally`에서 발생시킨다. `stage_finished`는 checkpoint 저장 성공 또는 실패가 확정된 뒤 발생시켜 전송 종료와 단계 결과를 구별한다. 관찰자 예외는 관찰 경계에서 격리하며 실행·저장 코드로 전파하지 않는다. 일반 API의 observer 기본값은 없다.

### D2. Heartbeat Lifecycle

한국어 표시와 timer의 소유자는 `evaluation/live.py`다. Provider 호출은 원래 동기 실행 흐름에 남겨 두고 reporter context에서 하나의 보조 thread를 만들어 `Event.wait(interval)`로 대기한다. 기본 간격은 5초이며 테스트에서는 interval·clock을 주입한다. 제어 가능한 clock 검사와 별도로 Event 기반의 짧은 실제 timer로 provider 반환 전에 heartbeat가 관찰되는지 확인한다.

Reporter는 provider 시작·종료 사건에서 active 대기 flag만 켜고 끈다. 같은 thread는 단계 사이에도 존재하지만 대기 중이 아니면 heartbeat를 출력하지 않는다. 실행 전체의 context 종료는 `__exit__`에서 idempotent stop·join으로 정리한다. Flag 전환과 출력은 같은 lock으로 동기화해 완료 로그 뒤 heartbeat가 뒤늦게 나오는 race를 차단한다. 출력은 고정 한국어 label과 stage·상태·로컬 시간만 조립하고 flush한다. Provider error나 설정 object를 문자열로 출력하지 않는다.

### D3. Module-Owned Source Revision

기존 script의 위치 기반 root 계산을 그대로 이동하지 않는다. 새 모듈의 `parents[4]` 후보 아래 `src/hmda_reliability/review_ai/evaluation/live.py`가 실제 `__file__`과 일치하고 `pyproject.toml`·Git checkout 표시가 있는지 확인한 후 기존 HEAD·clean tracked tree 검사를 그 root에서 수행한다. Caller의 working directory는 자동 revision의 source가 아니다.

이 검사를 통과하지 못하는 wheel 설치에서는 명시적 project revision을 사용한다. 자동 검사 오류는 고정 문구로 노출하고 Git 출력·개인 절대 경로를 진행 로그에 전달하지 않는다. 모듈은 직접 실행할 때만 `main`을 호출하고 이전 script에 forwarding wrapper를 남기지 않는다.
