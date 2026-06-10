## 1. Impact 모듈

- [x] 1.1 impact 패키지와 public export를 추가한다.
- [x] 1.2 dbt manifest nodes/sources parser와 asset index를 구현한다.
- [x] 1.3 downstream transitive traversal을 구현한다.
- [x] 1.4 `LineageEvidence`와 affected assets incident copy 생성을 구현한다.

## 2. 테스트

- [x] 2.1 source에서 staging/mart downstream을 계산하는 테스트를 추가한다.
- [x] 2.2 model name/node id asset 해석 테스트를 추가한다.
- [x] 2.3 `LineageEvidence`와 incident affected assets 연결 테스트를 추가한다.

## 3. 검증

- [x] 3.1 OpenSpec artifact 상태를 확인한다.
- [x] 3.2 ruff, mypy, reliability/foundation pytest를 실행한다.
