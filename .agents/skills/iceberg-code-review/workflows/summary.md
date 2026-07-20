## Arguments from Context

- `review_target_path`: **required**. 리뷰 대상 file 또는 directory
  - 미지정: autopilot이면 current working directory, 아니면 사용자에게 요청
- `reviews_dir`: 리뷰 결과 directory. 기본값: `/docs/reviews/`

## Procedure

1. 코드 리뷰 스킬이 있으면 함께 적용.
2. 지정된 code, PR 또는 diff 리뷰.
3. `python3 ./scripts/create_summary.py --reviews-dir "{reviews_dir}" --title-slug "{title_slug}"` 실행.
4. 주석 지침에 따라 플레이스홀더 작성.
5. 남은 주석 제거.

## Validation

`@./validation-file.md`
