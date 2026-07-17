"""Prepare IMF flow totals for STI calculation."""

import pandas as pd

from trade_discrepancy.harmonize import melt_imf
from trade_influence.constants import (
    IMF_BILATERAL_PARTNERS,
    IMF_TO_COMTRADE_COUNTRY,
)
from trade_influence.indices import compute_sti_from_totals


def build_imf_flow_totals(imf_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Convert wide IMF DOTS to long flow totals.

    Output columns: country (short label when mappable), year, flow, partner,
    total_usd (millions USD as reported by IMF).
    """
    long = melt_imf(imf_raw)
    if long.empty:
        return pd.DataFrame(
            columns=["country", "year", "flow", "partner", "total_usd"]
        )

    totals = long.rename(columns={"imf_value_musd": "total_usd"}).copy()
    totals["country"] = totals["country"].map(
        lambda name: IMF_TO_COMTRADE_COUNTRY.get(name, name)
    )
    return totals[["country", "year", "flow", "partner", "total_usd"]]


def compute_sti_imf(imf_raw: pd.DataFrame) -> pd.DataFrame:
    """Compute STI from IMF Pacific DOTS (Australia, China, US)."""
    totals = build_imf_flow_totals(imf_raw)
    return compute_sti_from_totals(
        totals,
        value_col="total_usd",
        bilateral_partners=IMF_BILATERAL_PARTNERS,
    )
