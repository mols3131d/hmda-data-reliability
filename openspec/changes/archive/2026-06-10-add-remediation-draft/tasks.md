## 1. Remediation 모델

- [x] 1.1 remediation 패키지와 public export를 추가한다.
- [x] 1.2 `RemediationDraft`와 request 모델을 추가한다.

## 2. LangGraph Workflow

- [x] 2.1 TypedDict state와 triage node를 구현한다.
- [x] 2.2 RCA node를 구현한다.
- [x] 2.3 remediation planning node와 workflow runner를 구현한다.

## 3. 테스트

- [x] 3.1 volume drop draft action 테스트를 추가한다.
- [x] 3.2 null spike dbt test suggestion 테스트를 추가한다.
- [x] 3.3 affected assets 보존과 JSON 직렬화 테스트를 추가한다.

## 4. 검증

- [x] 4.1 OpenSpec artifact 상태를 확인한다.
- [x] 4.2 ruff, mypy, reliability/foundation pytest를 실행한다.
