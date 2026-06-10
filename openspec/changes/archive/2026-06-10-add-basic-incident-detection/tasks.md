## 1. Detection 모델

- [x] 1.1 detection 패키지와 public export를 추가한다.
- [x] 1.2 threshold/request/result Pydantic 모델을 추가한다.

## 2. Rule Detector

- [x] 2.1 volume drop 탐지 rule을 구현한다.
- [x] 2.2 null spike 탐지 rule을 구현한다.
- [x] 2.3 schema drift 탐지 rule을 구현한다.
- [x] 2.4 freshness delay 탐지 rule을 구현한다.
- [x] 2.5 탐지 결과별 Evidence와 Incident 생성/연결을 구현한다.

## 3. 테스트

- [x] 3.1 정상 profile 비교 시 incident가 없는 테스트를 추가한다.
- [x] 3.2 4가지 rule별 incident/evidence payload 테스트를 추가한다.
- [x] 3.3 incident evidence_refs 연결 테스트를 추가한다.

## 4. 검증

- [x] 4.1 OpenSpec artifact 상태를 확인한다.
- [x] 4.2 ruff, mypy, reliability/foundation pytest를 실행한다.
