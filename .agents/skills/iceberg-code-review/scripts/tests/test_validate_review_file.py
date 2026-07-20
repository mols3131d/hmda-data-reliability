from pathlib import Path
import tempfile
import unittest

from validate_review_file import ReviewFileValidationError, validate_review_file


class ValidateReviewFileTest(unittest.TestCase):
    def test_validate_summary_and_reject_empty_section(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            review_file = Path(directory) / "__summary__.md"
            review_file.write_text(SUMMARY)
            validate_review_file(review_file)

            review_file.write_text(SUMMARY.replace("검토 결과", ""))
            with self.assertRaises(ReviewFileValidationError):
                validate_review_file(review_file)

    def test_validate_finding(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            review_file = Path(directory) / "auth-null-user.md"
            review_file.write_text(FINDING)
            validate_review_file(review_file)


SUMMARY = """---
title: '인증 리뷰'
date: '2026-07-20'
type: 'code-review-summary'
---
## Summary
검토 결과
## Findings
차단 finding 없음
"""

FINDING = """---
title: 'auth-null-user'
description: 'null guard 누락'
type: 'code-review-finding'
severity: 'bug'
status: 'open'
---
## Summary
요약
## Observation
관찰
## Impact
영향
## Recommendation
수정안
## Verification
검증
"""
