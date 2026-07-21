import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from _shared import ReviewFileCreationError
from create_summary import create_summary


class CreateSummaryTest(unittest.TestCase):
    def test_create_and_reject_invalid_or_duplicate_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            reviews_dir = Path(directory)
            created_at = datetime(2026, 7, 21, 14, 35)
            with patch("create_summary.datetime") as datetime_mock:
                datetime_mock.now.return_value = created_at
                destination = create_summary(reviews_dir, "auth-review")

                self.assertEqual(
                    destination,
                    reviews_dir / "2026-0721-1435-auth-review" / "__summary__.md",
                )
                self.assertEqual(
                    destination.read_text(encoding="utf-8"),
                    _template().read_text(encoding="utf-8"),
                )
                with self.assertRaises(ReviewFileCreationError):
                    create_summary(reviews_dir, "auth-review")
            with self.assertRaises(ReviewFileCreationError):
                create_summary(reviews_dir, "../bad")


def _template() -> Path:
    return Path(__file__).resolve().parents[2] / "templates" / "__summary__.md"


if __name__ == "__main__":
    unittest.main()
