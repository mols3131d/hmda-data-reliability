import tempfile
import unittest
from pathlib import Path

from _shared import ReviewFileCreationError
from create_finding import create_finding


class CreateFindingTest(unittest.TestCase):
    def test_create_and_reject_invalid_or_duplicate_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            summary_file = Path(directory) / "__summary__.md"
            summary_file.touch()
            destination = create_finding(summary_file, "auth", "null-user")

            self.assertEqual(destination.read_text(), _template().read_text())
            with self.assertRaises(ReviewFileCreationError):
                create_finding(summary_file, "auth", "null-user")
            with self.assertRaises(ReviewFileCreationError):
                create_finding(summary_file, "../auth", "null-user")


def _template() -> Path:
    return (
        Path(__file__).resolve().parents[2] / "templates" / "{{domain}}-{{finding}}.md"
    )


if __name__ == "__main__":
    unittest.main()
