## Arguments from Context

- `summary_file_path`: **required**. 이전 단계에서 생성한 summary file
  - 미지정: autopilot이면 마지막 review summary, 아니면 사용자에게 요청
- `finding`: 상세화할 finding. 기본값: summary file의 모든 finding
- `domain`: finding 영역을 나타내는 slug

## Procedure

각 finding에 대해 순서대로 실행:

1. `domain`과 `finding` slug 결정.
2. `<PYTHON_EXEC> ./scripts/create_finding.py --summary-file "<summary_file_path>" --domain "<domain>" --finding "<finding>"` 실행.
3. LLM은 생성된 `<domain>-<finding>.md`를 템플릿 주석에 따라 작성:
   - 검증된 문제와 위치
   - 영향
   - 실행 가능한 수정안
   - 수정 검증 방법
4. 플레이스홀더와 작성 지침 주석 제거.

## Validation

1. 작성된 각 `<domain>-<finding>.md` 파일의 무결성을 검증합니다.

   ```bash
   <PYTHON_EXEC> ./scripts/validate_finding.py "<summary_file_dir>/<domain>-<finding>.md"
   ```

2. 검증 에러(`FAIL: ...`) 발생 시, 출력되는 키워드를 확인하여 문서 수정 후 다시 검증합니다.
