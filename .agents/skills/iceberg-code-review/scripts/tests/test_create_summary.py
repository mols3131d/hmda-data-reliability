import tempfile
import unittest
from pathlib import Path

from _shared import ReviewFileCreationError
from create_summary import create_summary


class CreateSummaryTest(unittest.TestCase):
    def test_create_and_reject_invalid_or_duplicate_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            reviews_dir = Path(directory)
            destination = create_summary(reviews_dir, "auth-review")

            self.assertEqual(destination.read_text(), _template().read_text())
            with self.assertRaises(ReviewFileCreationError):
                create_summary(reviews_dir, "auth-review")
            with self.assertRaises(ReviewFileCreationError):
                create_summary(reviews_dir, "../bad")


def _template() -> Path:
    return Path(__file__).resolve().parents[2] / "templates" / "__summary__.md"


if __name__ == "__main__":
    unittest.main()
