## Why

MVP는 synthetic incident case가 기대대로 탐지되고 조치되는지 한 번에 확인할 수 있어야 한다. 현재 각 기능 테스트는 분리되어 있어 최종 `evaluation_report.md` 산출물이 없다.

## What Changes

- synthetic case별 기대 incident, 실제 detection, action 성공 여부를 집계하는 evaluation 모델을 추가한다.
- 성공률과 case별 결과를 Markdown report로 작성한다.
- report 출력 경로를 호출자가 지정할 수 있게 하며 MVP 기본 산출물은 `scratch/` 아래에 둔다.

## Capabilities

### New Capabilities

- `evaluation-report`: synthetic case 결과를 집계하고 Markdown 평가 보고서를 생성한다.

### Modified Capabilities

- 없음

## Impact

- `src/project_pivot/reliability/evaluation/` 모듈이 추가된다.
- `tests/reliability/test_evaluation_report.py`가 추가된다.
- 새 dependency는 없다.
