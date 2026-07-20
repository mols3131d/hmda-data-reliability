## Arguments from Context

- `summary_file_path`: **required**. 이전 단계에서 생성한 summary file
  - 미지정: autopilot이면 마지막 review summary, 아니면 사용자에게 요청
- `finding`: 상세화할 finding. 기본값: summary file의 모든 finding
- `domain`: finding 영역을 나타내는 slug

## Procedure

각 finding에 대해 순서대로 실행:

1. `domain`과 `finding` slug 결정.
2. `python3 ./scripts/create_finding.py --summary-file "{summary_file_path}" --domain "{domain}" --finding "{finding}"` 실행.
3. LLM은 생성된 `{domain}-{finding}.md`를 템플릿 주석에 따라 작성:
   - 검증된 문제와 위치
   - 영향
   - 실행 가능한 수정안
   - 수정 검증 방법
4. 플레이스홀더와 작성 지침 주석 제거.

## Validation

`@./validation-file.md`
