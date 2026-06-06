# Tasks

## 1. Contract 모델

- [x] 1.1 `project_pivot.reliability` 패키지를 추가한다.
- [x] 1.2 `Incident`, `Evidence`, `ProfileSnapshot`, `LineageEvidence`, `Approval` Pydantic 모델을 추가한다.
- [x] 1.3 severity, status, evidence source, approval status enum을 추가한다.
- [x] 1.4 approval 실행 가능 여부를 판단하는 helper를 추가한다.

## 2. Validation과 오류

- [x] 2.1 evidence 없는 incident를 거부하는 validation을 추가한다.
- [x] 2.2 approved approval의 `approved_by`, `approved_at` 필수 검증을 추가한다.
- [x] 2.3 contract validation 실패를 감싸는 custom exception을 추가한다.

## 3. Fixture와 테스트

- [x] 3.1 synthetic incident fixture를 추가한다.
- [x] 3.2 contract 생성, validation 실패, JSON 직렬화 테스트를 추가한다.
- [x] 3.3 approval gate helper 테스트를 추가한다.

## 4. 문서 연결

- [x] 4.1 architecture의 Incident Contract 설명을 실제 contract 명칭과 맞춘다.
- [x] 4.2 후속 OpenSpec 작업에서 이 contract를 참조하도록 작업 순서 메모를 유지한다.
