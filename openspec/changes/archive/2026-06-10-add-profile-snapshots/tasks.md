## 1. Profile 계산 모듈

- [x] 1.1 reliability profiling 패키지와 public export를 추가한다.
- [x] 1.2 DuckDB table schema metadata 조회와 deterministic schema hash 계산을 구현한다.
- [x] 1.3 partition row count, null rate, freshness 계산을 구현한다.
- [x] 1.4 계산 결과를 `ProfileSnapshot` contract로 반환한다.

## 2. 테스트

- [x] 2.1 profile snapshot 정상 생성 테스트를 추가한다.
- [x] 2.2 null rate, freshness, JSON 직렬화 테스트를 추가한다.
- [x] 2.3 schema hash 재현성과 schema 변경 감지 테스트를 추가한다.

## 3. 검증

- [x] 3.1 OpenSpec artifact 상태를 확인한다.
- [x] 3.2 profile snapshot 테스트와 관련 foundation 테스트를 실행한다.
