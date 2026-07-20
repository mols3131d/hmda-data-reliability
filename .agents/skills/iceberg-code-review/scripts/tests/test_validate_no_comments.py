import tempfile
import unittest
from pathlib import Path

from validate_no_comments import count_comments, has_no_comments


class ValidateNoCommentsTest(unittest.TestCase):
    def test_count_comments_without_code_false_positives(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            markdown_file = Path(directory) / "review.md"
            markdown_file.write_text(WITH_COMMENTS)

            self.assertEqual(count_comments(markdown_file), 4)
            self.assertFalse(has_no_comments(markdown_file))

    def test_no_comments(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            markdown_file = Path(directory) / "review.md"
            markdown_file.write_text(WITHOUT_COMMENTS)

            self.assertEqual(count_comments(markdown_file), 0)
            self.assertTrue(has_no_comments(markdown_file))


WITH_COMMENTS = '''---
# YAML comment
title: "# value"
description: |
  # block scalar content
status: open # inline comment
---
<!-- Markdown comment -->
*<!-- Emphasized comment -->*
`<!-- inline code -->`

```html
```not-a-closing-fence
<!-- fenced code -->
```

    <!-- indented code -->
'''

WITHOUT_COMMENTS = '''---
title: "# value"
description: |
  # block scalar content
---
`<!-- inline code -->`

```html
<!-- fenced code -->
```
'''
