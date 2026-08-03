# Reliability

품질 이상을 기록하고, 위험 작업을 승인 뒤 실행하도록 경계를 둔다.

## 기준

- `Incident`: 문제가 무엇인지 기록한다.
- `Evidence`: 판단 근거를 남긴다.
- `ProfileSnapshot`: partition 상태를 비교한다.
- `LineageEvidence`: 영향 범위를 연결한다.
- `Approval`: 위험 작업의 실행 여부를 결정한다.

관찰과 lifecycle은 읽기 전용으로 둔다. partition overwrite와 backfill은 승인된 별도 recovery에서 실행하고, evaluation도 별도로 둔다.
baseline 공급과 approval 결정은 lifecycle 외부의 책임으로 둔다.

구현 위치: `src/project_pivot/reliability/`  
검증 위치: `tests/reliability/`
