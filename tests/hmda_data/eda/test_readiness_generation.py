"""Readiness SSOT alignment and sum verification tests."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.unit

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
READINESS_YAML_PATH = PROJECT_ROOT / "docs/development/foundation/readiness.yml"
READINESS_MD_PATH = PROJECT_ROOT / "docs/development/foundation/readiness.md"


def test_readiness_yaml_totals_match_markdown_totals() -> None:
    """readiness.yml의 개별 progress 합계가 readiness.md Total 행과 100% 일치한다."""
    yaml_data = yaml.safe_load(READINESS_YAML_PATH.read_text(encoding="utf-8"))

    impl_done, impl_total = 0, 0
    verif_done, verif_total = 0, 0

    for item in yaml_data.get("items", []):
        impl_p = item["implementation"]["progress"]
        v_done, v_tot = map(int, impl_p.split("/"))
        impl_done += v_done
        impl_total += v_tot

        verif_p = item["verification"]["progress"]
        v_done, v_tot = map(int, verif_p.split("/"))
        verif_done += v_done
        verif_total += v_tot

    md_text = READINESS_MD_PATH.read_text(encoding="utf-8")

    # Extract Total row values from Markdown
    total_match = re.search(
        r"\|\s*\*\*Total\*\*\s*\|\s*.*?\s*\|\s*(?:\*\*)?`.*?(\d+)/(\d+)`(?:\*\*)?\s*\|\s*.*?\s*\|\s*(?:\*\*)?`.*?(\d+)/(\d+)`(?:\*\*)?\s*\|",
        md_text,
    )
    assert total_match is not None, "Total row not found in readiness.md"

    md_impl_done, md_impl_total = int(total_match.group(1)), int(total_match.group(2))
    md_verif_done, md_verif_total = int(total_match.group(3)), int(total_match.group(4))

    assert (impl_done, impl_total) == (md_impl_done, md_impl_total), (
        f"Implementation total mismatch: YAML has {impl_done}/{impl_total}, "
        f"Markdown has {md_impl_done}/{md_impl_total}"
    )
    assert (verif_done, verif_total) == (md_verif_done, md_verif_total), (
        f"Verification total mismatch: YAML has {verif_done}/{verif_total}, "
        f"Markdown has {md_verif_done}/{md_verif_total}"
    )
