## Arguments from Context

- `reviews_dir`: 리뷰 결과를 저장할 디렉터리 경로 (선택)
- `allow_extra_frontmatter`: 추가적인 프론트매터 키 허용 여부 (`true` 또는 `false`) (선택)
- `allow_extra_sections`: 추가적인 커스텀 섹션 허용 여부 (`true` 또는 `false`) (선택)

## Procedure

1. 사용자가 요구한 설정값을 인자로 전달하여 설정 변경 스크립트를 실행합니다:

   ```bash
   <PYTHON_EXEC> ./scripts/configurator.py --reviews-dir "<reviews_dir>" --allow-extra-frontmatter "<true/false>" --allow-extra-sections "<true/false>"
   ```

2. 전달할 필요가 없는 인자는 생략합니다.
