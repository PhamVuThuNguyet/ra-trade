"""Build HS2 commodity–partner panels from raw Comtrade records."""

import numpy as np
import pandas as pd

from trade_discrepancy.constants import (
    VALUATION_CIF_FOB_ONLY,
    VALUATION_PRIMARY,
    VALUATION_STANDARD,
    canonical_comtrade_country,
)
from trade_influence.constants import (
    BILATERAL_PARTNER_ISO,
    PARTNER_ISO_TO_KEY,
    WORLD_PARTNER_ISO,
)


def cmd_code_to_hs2(cmd_code) -> str:
    """Map an HS4 (or shorter) commodity code to a zero-padded HS2 chapter."""
    if pd.isna(cmd_code):
        raise ValueError("cmdCode is missing")
    digits = "".join(ch for ch in str(cmd_code).strip() if ch.isdigit())
    if not digits:
        raise ValueError(f"Cannot derive HS2 from cmdCode={cmd_code!r}")
    return digits.zfill(4)[:2]


def _trade_value_series(df: pd.DataFrame, method: str = VALUATION_STANDARD) -> pd.Series:
    """Vectorized CIF/FOB valuation matching ``trade_value_usd`` rules."""
    if method == VALUATION_PRIMARY:
        return pd.to_numeric(df["primaryValue__US__"], errors="coerce").fillna(0.0)

    is_import = df["flowCode"].eq("M")
    cif = pd.to_numeric(df["cifvalue__US__"], errors="coerce")
    fob = pd.to_numeric(df["fobvalue__US__"], errors="coerce")
    primary = pd.to_numeric(df["primaryValue__US__"], errors="coerce")
    value = pd.Series(
        np.where(is_import, cif, fob),
        index=df.index,
        dtype="float64",
    )

    if method == VALUATION_STANDARD:
        value = value.fillna(primary)
    elif method != VALUATION_CIF_FOB_ONLY:
        raise ValueError(f"Unknown valuation method: {method}")

    return value.fillna(0.0)


def build_hs2_panel(
    comtrade_raw: pd.DataFrame,
    value_method: str = VALUATION_STANDARD,
) -> pd.DataFrame:
    """
    Aggregate Comtrade rows to country × year × flow × partner × HS2.

    Partners kept: AUS, CHN, and W00 (world). Values remain in USD.
    """
    required = {
        "reporterDesc",
        "refYear",
        "flowCode",
        "partnerISO",
        "cmdCode",
        "cifvalue__US__",
        "fobvalue__US__",
        "primaryValue__US__",
    }
    missing = required - set(comtrade_raw.columns)
    if missing:
        raise KeyError(f"Comtrade frame missing columns: {sorted(missing)}")

    partners = set(BILATERAL_PARTNER_ISO) | {WORLD_PARTNER_ISO}
    working = comtrade_raw[comtrade_raw["partnerISO"].isin(partners)].copy()
    if working.empty:
        return pd.DataFrame(
            columns=["country", "year", "flow", "partner", "hs2", "value_usd"]
        )

    working["value_usd"] = _trade_value_series(working, method=value_method)
    working["country"] = working["reporterDesc"].map(canonical_comtrade_country)
    working["year"] = working["refYear"].astype(int)
    working["flow"] = working["flowCode"].map({"M": "import", "X": "export"})
    working["partner"] = working["partnerISO"].map(PARTNER_ISO_TO_KEY)
    working["hs2"] = working["cmdCode"].map(cmd_code_to_hs2)

    working = working.dropna(subset=["flow", "partner"])
    panel = (
        working.groupby(["country", "year", "flow", "partner", "hs2"], as_index=False)[
            "value_usd"
        ]
        .sum()
        .sort_values(["country", "year", "flow", "partner", "hs2"])
        .reset_index(drop=True)
    )
    return panel


def partner_flow_totals(panel: pd.DataFrame) -> pd.DataFrame:
    """Sum HS2 values to country × year × flow × partner totals."""
    return (
        panel.groupby(["country", "year", "flow", "partner"], as_index=False)[
            "value_usd"
        ]
        .sum()
        .rename(columns={"value_usd": "total_usd"})
    )
