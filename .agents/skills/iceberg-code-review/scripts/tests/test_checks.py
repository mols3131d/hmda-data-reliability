import unittest
from pathlib import Path

from checks import has_no_placeholders, validate_no_comments, validate_review_file

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


class ChecksFixtureTest(unittest.TestCase):
    def test_fixtures_missing_frontmatter(self) -> None:
        errors = validate_review_file(FIXTURES_DIR / "header-no-frontmatter.md")
        self.assertTrue(any("MISSING_FRONTMATTER" in e for e in errors), errors)

        errors = validate_review_file(FIXTURES_DIR / "frontmatter-wrong-delimiter.md")
        self.assertTrue(any("MISSING_FRONTMATTER" in e for e in errors), errors)

        errors = validate_review_file(FIXTURES_DIR / "frontmatter-unclosed.md")
        self.assertTrue(any("MISSING_FRONTMATTER" in e for e in errors), errors)

    def test_fixtures_invalid_type(self) -> None:
        errors = validate_review_file(FIXTURES_DIR / "header-invalid-type.md")
        self.assertTrue(any("UNSUPPORTED_DOCUMENT_TYPE" in e for e in errors), errors)

    def test_fixtures_remaining_comments(self) -> None:
        for filename in ("comments-html.md", "comments-yaml.md"):
            errors = validate_no_comments(FIXTURES_DIR / filename)
            self.assertTrue(any("REMAINING_COMMENTS" in e for e in errors), errors)

    def test_fixtures_placeholders(self) -> None:
        self.assertFalse(has_no_placeholders(FIXTURES_DIR / "placeholder-unfilled.md"))

    def test_summary_fixtures(self) -> None:
        errors = validate_review_file(FIXTURES_DIR / "summary" / "section-empty.md")
        self.assertTrue(any("EMPTY_SECTIONS_FOUND" in e for e in errors), errors)

    def test_finding_fixtures(self) -> None:
        errors = validate_review_file(
            FIXTURES_DIR / "finding" / "header-empty-values.md"
        )
        self.assertTrue(any("MISSING_REQUIRED_METADATA" in e for e in errors), errors)

        errors = validate_review_file(
            FIXTURES_DIR / "finding" / "header-missing-fields.md"
        )
        self.assertEqual(errors, [])

        errors = validate_review_file(
            FIXTURES_DIR / "finding" / "section-invalid-order.md"
        )
        self.assertTrue(any("INVALID_SECTION_ORDER" in e for e in errors), errors)

        errors = validate_review_file(FIXTURES_DIR / "finding" / "section-missing.md")
        self.assertTrue(any("MISSING_REQUIRED_SECTION" in e for e in errors), errors)

        errors = validate_review_file(
            FIXTURES_DIR / "finding" / "section-wrong-heading.md"
        )
        self.assertTrue(any("MISSING_REQUIRED_SECTION" in e for e in errors), errors)


if __name__ == "__main__":
    unittest.main()
