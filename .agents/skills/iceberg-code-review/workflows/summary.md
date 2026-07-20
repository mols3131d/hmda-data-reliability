## Arguments from Context

- `review_target_path`: **required**. 리뷰 대상 file 또는 directory
  - 미지정: autopilot이면 current working directory, 아니면 사용자에게 요청

## Procedure

1. 코드 리뷰 스킬이 있으면 함께 적용.
2. 지정된 code, PR 또는 diff 리뷰.
3. `<PYTHON_EXEC> ./scripts/create_summary.py --title-slug "<title_slug>" --workspace-dir "<workspace_absolute_path>"` 실행. (LLM이 워크스페이스 절대경로 주입)
4. 실행 결과 로그(`INFO OK: <절대경로>`)에서 템플릿 파일의 절대 경로를 획득.
5. 주석 지침에 따라 획득한 절대 경로의 파일에 플레이스홀더 작성.
6. 남은 주석 제거.

## Validation

1. 작성된 `__summary__.md` 파일의 무결성을 검증합니다.

   ```bash
   <PYTHON_EXEC> ./scripts/validate_summary.py "<획득한_절대경로>"
   ```

2. 검증 에러(`FAIL: ...`) 발생 시, 출력되는 키워드를 확인하여 문서 수정 후 다시 검증합니다.
