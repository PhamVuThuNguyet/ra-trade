"""Unit tests for essential-commodity SITC membership and CWI/CWE."""

import pandas as pd
import pytest

from trade_influence.constants import ESSENTIAL_SITC2, INDEX_CWI, INDEX_CWE
from trade_influence.essential import (
    compute_essential_cwe,
    compute_essential_cwi,
    filter_essential_panel,
    map_baci_hs6_to_sitc2,
    pad_hs6,
)
from trade_influence.indices import compute_cwe, compute_cwi


def test_essential_sitc2_has_exactly_the_closed_set():
    assert len(ESSENTIAL_SITC2) == 20
    assert len(set(ESSENTIAL_SITC2)) == 20
    assert "54" in ESSENTIAL_SITC2
    assert "67" not in ESSENTIAL_SITC2


def test_unmapped_hs6_is_not_essential():
    assert map_baci_hs6_to_sitc2("720110") is None
    assert map_baci_hs6_to_sitc2("999999") is None


def test_mapped_hs6_uses_concordance_and_chapter_fallback():
    assert map_baci_hs6_to_sitc2("010110") == "00"
    assert map_baci_hs6_to_sitc2("080232") == "05"
    assert map_baci_hs6_to_sitc2("100190") == "04"
    assert pad_hs6(10110) == "010110"


def test_filter_essential_panel_keeps_only_listed_sitc2():
    panel = pd.DataFrame(
        {
            "country": ["Fiji", "Fiji"],
            "year": [2013, 2013],
            "flow": ["import", "import"],
            "partner": ["aus", "aus"],
            "sitc2": ["04", "67"],
            "value_usd": [10.0, 90.0],
        }
    )
    filtered = filter_essential_panel(panel)
    assert list(filtered["sitc2"]) == ["04"]


def _mixed_panel() -> pd.DataFrame:
    """Essential cereal (04) plus non-essential iron (67)."""
    rows = []
    for sitc2, world, aus in (("04", 50.0, 40.0), ("67", 50.0, 10.0)):
        rows.append(
            {
                "country": "Fiji",
                "year": 2013,
                "flow": "import",
                "partner": "world",
                "sitc2": sitc2,
                "value_usd": world,
            }
        )
        rows.append(
            {
                "country": "Fiji",
                "year": 2013,
                "flow": "import",
                "partner": "aus",
                "sitc2": sitc2,
                "value_usd": aus,
            }
        )
        rows.append(
            {
                "country": "Fiji",
                "year": 2013,
                "flow": "export",
                "partner": "world",
                "sitc2": sitc2,
                "value_usd": world,
            }
        )
        rows.append(
            {
                "country": "Fiji",
                "year": 2013,
                "flow": "export",
                "partner": "aus",
                "sitc2": sitc2,
                "value_usd": aus,
            }
        )
    return pd.DataFrame(rows)


def test_essential_cwi_cwe_differ_from_all_products_on_mixed_panel():
    panel = _mixed_panel()
    all_cwi = compute_cwi(panel)
    ess_cwi = compute_essential_cwi(panel)
    all_cwe = compute_cwe(panel)
    ess_cwe = compute_essential_cwe(panel)
    aus_all = all_cwi[all_cwi["partner"] == "aus"].iloc[0][INDEX_CWI]
    aus_ess = ess_cwi[ess_cwi["partner"] == "aus"].iloc[0][INDEX_CWI]
    assert aus_ess != pytest.approx(aus_all)
    assert ess_cwe[ess_cwe["partner"] == "aus"].iloc[0][INDEX_CWE] != pytest.approx(
        all_cwe[all_cwe["partner"] == "aus"].iloc[0][INDEX_CWE]
    )
