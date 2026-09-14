"""Essential-commodity panels and CWI/CWE (same formulas, restricted SITC set)."""

from functools import lru_cache
from pathlib import Path

import pandas as pd

from trade_influence.constants import (
    COMMODITY_COL,
    ESSENTIAL_SITC2,
    HS02_TO_SITC4R2_PATH,
)
from trade_influence.indices import compute_cwe, compute_cwi

ESSENTIAL_SITC2_SET = frozenset(ESSENTIAL_SITC2)


def pad_hs6(code) -> str:
    """Zero-pad an HS 2002 product code to six digits."""
    digits = "".join(ch for ch in str(code).strip() if ch.isdigit())
    return digits.zfill(6)[:6]


def pad_sitc2(code) -> str:
    digits = "".join(ch for ch in str(code).strip() if ch.isdigit())
    return digits.zfill(2)[:2]


@lru_cache(maxsize=4)
def load_concordance(path: str | None = None) -> dict[str, str]:
    """Load hs6 → sitc2 from the versioned concordance CSV."""
    csv_path = Path(path) if path else HS02_TO_SITC4R2_PATH
    table = pd.read_csv(csv_path, dtype=str)
    if "hs6" not in table.columns or "sitc2" not in table.columns:
        raise KeyError("Concordance must have hs6 and sitc2 columns")
    mapping: dict[str, str] = {}
    for _, row in table.iterrows():
        mapping[pad_hs6(row["hs6"])] = pad_sitc2(row["sitc2"])
    return mapping


def map_baci_hs6_to_sitc2(
    hs6,
    concordance: dict[str, str] | None = None,
) -> str | None:
    """Map one HS6 code; unmatched codes are not essential (None)."""
    table = concordance if concordance is not None else load_concordance()
    code = pad_hs6(hs6)
    for key in (code, code[:4] + "00", code[:2] + "0000"):
        sitc2 = table.get(key)
        if sitc2 is not None:
            return sitc2
    return None


def filter_essential_panel(
    panel: pd.DataFrame,
    *,
    commodity_col: str = COMMODITY_COL,
) -> pd.DataFrame:
    """Keep rows whose SITC-2 code is in the 21-division essential set."""
    if panel.empty or commodity_col not in panel.columns:
        return panel.iloc[0:0].copy()
    sitc2 = panel[commodity_col].map(pad_sitc2)
    return panel.loc[sitc2.isin(ESSENTIAL_SITC2_SET)].copy()


def map_hs6_panel_to_sitc2(
    panel: pd.DataFrame,
    *,
    hs6_col: str = "hs6",
    concordance: dict[str, str] | None = None,
) -> pd.DataFrame:
    """Add sitc2 from HS6; drop unmapped products."""
    if panel.empty:
        return panel.copy()
    table = concordance if concordance is not None else load_concordance()
    working = panel.copy()
    working[COMMODITY_COL] = working[hs6_col].map(
        lambda code: map_baci_hs6_to_sitc2(code, table)
    )
    mapped = working.dropna(subset=[COMMODITY_COL])
    keys = ["country", "year", "flow", "partner", COMMODITY_COL]
    return mapped.groupby(keys, as_index=False)["value_usd"].sum()


def compute_essential_cwi(
    panel: pd.DataFrame,
    *,
    commodity_col: str = COMMODITY_COL,
    global_shares: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """CWI on essential commodities only."""
    filtered = filter_essential_panel(panel, commodity_col=commodity_col)
    shares = _filter_global_shares(global_shares, commodity_col=commodity_col)
    return compute_cwi(
        filtered, commodity_col=commodity_col, global_shares=shares
    )


def compute_essential_cwe(
    panel: pd.DataFrame,
    *,
    commodity_col: str = COMMODITY_COL,
    global_shares: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """CWE on essential commodities only."""
    filtered = filter_essential_panel(panel, commodity_col=commodity_col)
    shares = _filter_global_shares(global_shares, commodity_col=commodity_col)
    return compute_cwe(
        filtered, commodity_col=commodity_col, global_shares=shares
    )


def _filter_global_shares(
    global_shares: pd.DataFrame | None,
    *,
    commodity_col: str,
) -> pd.DataFrame | None:
    if global_shares is None or global_shares.empty:
        return global_shares
    if commodity_col not in global_shares.columns:
        return None
    sitc2 = global_shares[commodity_col].map(pad_sitc2)
    return global_shares.loc[sitc2.isin(ESSENTIAL_SITC2_SET)].copy()
