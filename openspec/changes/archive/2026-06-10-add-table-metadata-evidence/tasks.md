## 1. Metadata 모델

- [x] 1.1 metadata 패키지와 public export를 추가한다.
- [x] 1.2 metadata evidence request 모델을 추가한다.

## 2. Evidence Builder

- [x] 2.1 DuckDB table schema와 row count 조회를 구현한다.
- [x] 2.2 `EvidenceSource.TABLE_METADATA` Evidence 생성을 구현한다.
- [x] 2.3 metadata 조회 오류를 도메인 예외로 감싼다.

## 3. 테스트

- [x] 3.1 metadata evidence payload 테스트를 추가한다.
- [x] 3.2 존재하지 않는 table 오류 wrapping 테스트를 추가한다.

## 4. 검증

- [x] 4.1 OpenSpec artifact 상태를 확인한다.
- [x] 4.2 ruff, mypy, 관련 pytest를 실행한다.
