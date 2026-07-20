import re
import tempfile
import unittest
from pathlib import Path

from checks import PLACEHOLDER_PATTERN, count_placeholders, has_no_placeholders

BRACED_TOKEN_PATTERN = re.compile(r"{{[^{}\n]*}}")


class PlaceholderTest(unittest.TestCase):
    def test_count_and_completion(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            markdown_file = Path(directory) / "review.md"
            markdown_file.write_text(
                "# {{title}} {{리뷰_결과}}\n"
                "{{}} {{ title }} {{title-slug}} {{123}} `{{` ... `}}`\n"
            )

            self.assertEqual(count_placeholders(markdown_file), 2)
            self.assertFalse(has_no_placeholders(markdown_file))

            markdown_file.write_text("# 작성 완료\n")
            self.assertEqual(count_placeholders(markdown_file), 0)
            self.assertTrue(has_no_placeholders(markdown_file))

    def test_all_template_placeholders_follow_the_rule(self) -> None:
        templates_dir = Path(__file__).resolve().parents[2] / "templates"

        for template in templates_dir.glob("*.md"):
            source = template.read_text()
            self.assertEqual(
                BRACED_TOKEN_PATTERN.findall(source),
                PLACEHOLDER_PATTERN.findall(source),
                template,
            )
