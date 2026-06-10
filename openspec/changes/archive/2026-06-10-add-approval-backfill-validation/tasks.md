## 1. Recovery 모델

- [x] 1.1 recovery 패키지와 public export를 추가한다.
- [x] 1.2 approved backfill request/result 모델을 추가한다.

## 2. Approval Gate 실행

- [x] 2.1 approval 상태를 먼저 검증하는 guard를 구현한다.
- [x] 2.2 승인 후 yellow taxi partition overwrite를 실행한다.
- [x] 2.3 overwrite 후 profile snapshot validation을 실행한다.

## 3. 테스트

- [x] 3.1 미승인 approval이 backfill 전에 실패하는 테스트를 추가한다.
- [x] 3.2 승인된 backfill이 snapshot을 재생성하는 테스트를 추가한다.

## 4. 검증

- [x] 4.1 OpenSpec artifact 상태를 확인한다.
- [x] 4.2 ruff, mypy, 관련 pytest를 실행한다.
