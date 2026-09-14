"""Build SITC-2 commodity–partner panels from raw Comtrade records."""

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
    COMMODITY_COL,
    PARTNER_ISO_TO_KEY,
    SITC_GROUP_WIDTH,
    WORLD_PARTNER_ISO,
)


def cmd_code_to_sitc2(cmd_code) -> str:
    """Map a SITC group code (leading zeros often stripped) to a 2-digit division."""
    if pd.isna(cmd_code):
        raise ValueError("cmdCode is missing")
    text = str(cmd_code).strip()
    if text.endswith(".0"):
        text = text[:-2]
    digits = "".join(ch for ch in text if ch.isdigit())
    if not digits:
        raise ValueError(f"Cannot derive SITC-2 from cmdCode={cmd_code!r}")
    return digits.zfill(SITC_GROUP_WIDTH)[:2]


def _trade_value_series(
    df: pd.DataFrame, method: str = VALUATION_STANDARD
) -> pd.Series:
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


def build_sitc2_panel(
    comtrade_raw: pd.DataFrame,
    value_method: str = VALUATION_STANDARD,
    *,
    bilateral_partner_isos: tuple[str, ...] | None = None,
) -> pd.DataFrame:
    """
    Aggregate Comtrade rows to country × year × flow × partner × SITC-2.

    Default partners: AUS, CHN, USA, and W00 (world). AG3 codes are padded to
    3 digits (so 11 → 011) then rolled to 2-digit divisions. Values stay in USD.
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

    bilateral = (
        BILATERAL_PARTNER_ISO
        if bilateral_partner_isos is None
        else tuple(bilateral_partner_isos)
    )
    partners = set(bilateral) | {WORLD_PARTNER_ISO}
    working = comtrade_raw[comtrade_raw["partnerISO"].isin(partners)].copy()
    if working.empty:
        return pd.DataFrame(
            columns=["country", "year", "flow", "partner", COMMODITY_COL, "value_usd"]
        )

    working["value_usd"] = _trade_value_series(working, method=value_method)
    working["country"] = working["reporterDesc"].map(canonical_comtrade_country)
    working["year"] = working["refYear"].astype(int)
    working["flow"] = working["flowCode"].map({"M": "import", "X": "export"})
    working["partner"] = working["partnerISO"].map(PARTNER_ISO_TO_KEY)
    working[COMMODITY_COL] = working["cmdCode"].map(cmd_code_to_sitc2)

    working = working.dropna(subset=["flow", "partner"])
    return (
        working.groupby(
            ["country", "year", "flow", "partner", COMMODITY_COL], as_index=False
        )["value_usd"]
        .sum()
        .sort_values(["country", "year", "flow", "partner", COMMODITY_COL])
        .reset_index(drop=True)
    )


def partner_flow_totals(panel: pd.DataFrame) -> pd.DataFrame:
    """Sum SITC-2 values to country × year × flow × partner totals."""
    return (
        panel.groupby(["country", "year", "flow", "partner"], as_index=False)[
            "value_usd"
        ]
        .sum()
        .rename(columns={"value_usd": "total_usd"})
    )
