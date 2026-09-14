"""Build HS-2 commodity–partner panels from PIC-filtered BACI flows."""

import pandas as pd

from baci.constants import (
    HS2_COL,
    PARTNER_CODE_TO_KEY,
    VALUE_THOUSANDS_TO_USD,
)
from baci.prepare import pic_reporter_view
from trade_discrepancy.constants import PARTNER_WORLD
from trade_influence.constants import BILATERAL_PARTNERS, COMMODITY_COL_HS2
from trade_influence.prepare import partner_flow_totals

PANEL_COLUMNS = (
    "country",
    "year",
    "flow",
    "partner",
    COMMODITY_COL_HS2,
    "value_usd",
)

HS6_PANEL_COLUMNS = (
    "country",
    "year",
    "flow",
    "partner",
    "hs6",
    "value_usd",
)


def _empty_panel() -> pd.DataFrame:
    return pd.DataFrame(columns=list(PANEL_COLUMNS))


def _bilateral_and_other(view: pd.DataFrame) -> pd.DataFrame:
    """Keep AUS/CHN/US as named partners; roll remaining origins/destinations into other."""
    working = view.copy()
    working["partner"] = working["partner_code"].map(PARTNER_CODE_TO_KEY)
    working["partner"] = working["partner"].fillna("other")
    working["value_usd"] = working["value_thousands_usd"] * VALUE_THOUSANDS_TO_USD
    working[COMMODITY_COL_HS2] = working[HS2_COL]
    return working[
        ["country", "year", "flow", "partner", COMMODITY_COL_HS2, "value_usd"]
    ]


def build_hs2_panel(pic_flows: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate BACI PIC flows to country × year × flow × partner × HS-2.

    Partners: Australia, China, United States, residual ``other``, and ``world``.
    World totals are the sum of all partners (BACI has no World aggregate).
    Values are converted from thousand USD to USD.
    """
    view = pic_reporter_view(pic_flows)
    if view.empty:
        return _empty_panel()

    labeled = _bilateral_and_other(view)
    commodity = (
        labeled.groupby(
            ["country", "year", "flow", "partner", COMMODITY_COL_HS2],
            as_index=False,
        )["value_usd"]
        .sum()
    )
    world = (
        commodity.groupby(
            ["country", "year", "flow", COMMODITY_COL_HS2], as_index=False
        )["value_usd"]
        .sum()
        .assign(partner=PARTNER_WORLD)
    )
    keep_partners = set(BILATERAL_PARTNERS) | {PARTNER_WORLD}
    bilateral = commodity[commodity["partner"].isin(BILATERAL_PARTNERS)]
    panel = pd.concat([bilateral, world], ignore_index=True)
    panel = panel[panel["partner"].isin(keep_partners)]
    return (
        panel[list(PANEL_COLUMNS)]
        .sort_values(["country", "year", "flow", "partner", COMMODITY_COL_HS2])
        .reset_index(drop=True)
    )


def build_hs6_panel(pic_flows: pd.DataFrame) -> pd.DataFrame:
    """Aggregate BACI PIC flows to country × year × flow × partner × HS-6."""
    view = pic_reporter_view(pic_flows)
    if view.empty:
        return pd.DataFrame(columns=list(HS6_PANEL_COLUMNS))

    working = view.copy()
    working["partner"] = working["partner_code"].map(PARTNER_CODE_TO_KEY)
    working["partner"] = working["partner"].fillna("other")
    working["value_usd"] = working["value_thousands_usd"] * VALUE_THOUSANDS_TO_USD
    labeled = working[
        ["country", "year", "flow", "partner", "hs6", "value_usd"]
    ]
    commodity = labeled.groupby(
        ["country", "year", "flow", "partner", "hs6"],
        as_index=False,
    )["value_usd"].sum()
    world = (
        commodity.groupby(["country", "year", "flow", "hs6"], as_index=False)[
            "value_usd"
        ]
        .sum()
        .assign(partner=PARTNER_WORLD)
    )
    keep_partners = set(BILATERAL_PARTNERS) | {PARTNER_WORLD}
    bilateral = commodity[commodity["partner"].isin(BILATERAL_PARTNERS)]
    panel = pd.concat([bilateral, world], ignore_index=True)
    panel = panel[panel["partner"].isin(keep_partners)]
    return (
        panel[list(HS6_PANEL_COLUMNS)]
        .sort_values(["country", "year", "flow", "partner", "hs6"])
        .reset_index(drop=True)
    )


__all__ = ["build_hs2_panel", "build_hs6_panel", "partner_flow_totals"]
