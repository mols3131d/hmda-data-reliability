import tempfile
import unittest
from pathlib import Path

from _checks import has_no_placeholders, validate_no_comments, validate_review_file

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
        errors = validate_no_comments(FIXTURES_DIR / "comments-html.md")
        self.assertTrue(any("REMAINING_COMMENTS" in e for e in errors), errors)

    def test_yaml_comments_are_allowed(self) -> None:
        self.assertEqual(validate_no_comments(FIXTURES_DIR / "comments-yaml.md"), [])

    def test_fixtures_placeholders(self) -> None:
        self.assertFalse(has_no_placeholders(FIXTURES_DIR / "placeholder-unfilled.md"))
        errors = validate_review_file(FIXTURES_DIR / "placeholder-unfilled.md")
        self.assertTrue(any("REMAINING_PLACEHOLDERS" in e for e in errors), errors)

    def test_invalid_yaml_returns_validation_error(self) -> None:
        errors = validate_review_file(FIXTURES_DIR / "header-invalid-yaml.md")
        self.assertIn("INVALID_FRONTMATTER_YAML", errors)

    def test_non_mapping_frontmatter_returns_validation_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "review.md"
            for root in ("- item", "value", "true"):
                with self.subTest(root=root):
                    path.write_text(f"---\n{root}\n---\n", encoding="utf-8")
                    errors = validate_review_file(path)
                    self.assertIn("INVALID_FRONTMATTER_TYPE", errors)

    def test_yaml_hashes_are_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "review.md"
            valid_values = ("C# review", "'issue #123'", '"page#section"')
            for value in valid_values:
                with self.subTest(value=value):
                    path.write_text(f"---\ntitle: {value}\n---\n", encoding="utf-8")
                    self.assertEqual(validate_no_comments(path), [])

            path.write_text("---\ntitle: review # comment\n# comment\n---\n")
            self.assertEqual(validate_no_comments(path), [])

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
