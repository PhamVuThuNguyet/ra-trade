"""Partner global market shares of HS-2 trade from full BACI year files."""

from collections.abc import Sequence

import numpy as np
import pandas as pd

from baci.constants import (
    BILATERAL_PARTNER_CODES,
    COL_EXPORT_SHARE,
    COL_IMPORT_SHARE,
    COL_EXPORTER,
    COL_IMPORTER,
    COL_PRODUCT,
    COL_VALUE,
    COL_YEAR,
    HS2_COL,
    PARTNER_CODE_TO_KEY,
)
from baci.products import product_series_to_hs2

BILATERAL_PARTNER_KEYS = tuple(PARTNER_CODE_TO_KEY[code] for code in BILATERAL_PARTNER_CODES)

SHARE_COLUMNS = (
    "year",
    HS2_COL,
    "partner",
    "world_value",
    "partner_exports",
    "partner_imports",
    COL_EXPORT_SHARE,
    COL_IMPORT_SHARE,
)


def chunk_hs2_totals(chunk: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """World, partner-export, and partner-import HS-2 value sums for one chunk."""
    if chunk.empty:
        return _empty_world(), _empty_partner("partner_exports"), _empty_partner(
            "partner_imports"
        )

    year = pd.to_numeric(chunk[COL_YEAR], errors="coerce")
    value = pd.to_numeric(chunk[COL_VALUE], errors="coerce").fillna(0.0)
    valid = year.notna()
    if not bool(valid.any()):
        return _empty_world(), _empty_partner("partner_exports"), _empty_partner(
            "partner_imports"
        )

    working = pd.DataFrame(
        {
            "year": year[valid].astype(int),
            HS2_COL: product_series_to_hs2(chunk.loc[valid, COL_PRODUCT]),
            COL_VALUE: value[valid],
            COL_EXPORTER: chunk.loc[valid, COL_EXPORTER],
            COL_IMPORTER: chunk.loc[valid, COL_IMPORTER],
        }
    )
    world = (
        working.groupby(["year", HS2_COL], as_index=False)[COL_VALUE]
        .sum()
        .rename(columns={COL_VALUE: "world_value"})
    )

    partner_codes = set(BILATERAL_PARTNER_CODES)
    exports = _partner_direction_totals(
        working, code_col=COL_EXPORTER, partner_codes=partner_codes, value_name="partner_exports"
    )
    imports = _partner_direction_totals(
        working, code_col=COL_IMPORTER, partner_codes=partner_codes, value_name="partner_imports"
    )
    return world, exports, imports


def _partner_direction_totals(
    working: pd.DataFrame,
    *,
    code_col: str,
    partner_codes: set[int],
    value_name: str,
) -> pd.DataFrame:
    subset = working[working[code_col].isin(partner_codes)]
    if subset.empty:
        return _empty_partner(value_name)
    labeled = subset.assign(partner=subset[code_col].map(PARTNER_CODE_TO_KEY))
    labeled = labeled.dropna(subset=["partner"])
    if labeled.empty:
        return _empty_partner(value_name)
    return (
        labeled.groupby(["year", HS2_COL, "partner"], as_index=False)[COL_VALUE]
        .sum()
        .rename(columns={COL_VALUE: value_name})
    )


def _empty_world() -> pd.DataFrame:
    return pd.DataFrame(columns=["year", HS2_COL, "world_value"])


def _empty_partner(value_name: str) -> pd.DataFrame:
    return pd.DataFrame(columns=["year", HS2_COL, "partner", value_name])


def concat_totals(frames: Sequence[pd.DataFrame], value_col: str) -> pd.DataFrame:
    nonempty = [frame for frame in frames if not frame.empty]
    if not nonempty:
        return pd.DataFrame(columns=["year", HS2_COL, "partner", value_col] if value_col != "world_value" else ["year", HS2_COL, value_col])
    keys = ["year", HS2_COL] if value_col == "world_value" else ["year", HS2_COL, "partner"]
    return (
        pd.concat(nonempty, ignore_index=True)
        .groupby(keys, as_index=False)[value_col]
        .sum()
    )


def compute_global_market_shares(
    world: pd.DataFrame,
    exports: pd.DataFrame,
    imports: pd.DataFrame,
    *,
    partners: tuple[str, ...] = BILATERAL_PARTNER_KEYS,
) -> pd.DataFrame:
    """
    Partner j's share of world exports (iw) and world imports (ew) by HS-2.

    In BACI, world exports of c equal world imports of c (unique FOB flows).
    Missing partner cells are 0. Zero world denominators yield share 0.
    """
    if world.empty:
        return pd.DataFrame(columns=list(SHARE_COLUMNS))

    grid = (
        world.assign(_key=1)
        .merge(pd.DataFrame({"partner": list(partners), "_key": 1}), on="_key")
        .drop(columns="_key")
    )
    merged = grid.merge(exports, on=["year", HS2_COL, "partner"], how="left")
    merged = merged.merge(imports, on=["year", HS2_COL, "partner"], how="left")
    merged["partner_exports"] = merged["partner_exports"].fillna(0.0)
    merged["partner_imports"] = merged["partner_imports"].fillna(0.0)
    safe = merged["world_value"] > 0
    merged[COL_EXPORT_SHARE] = np.where(
        safe, merged["partner_exports"] / merged["world_value"], 0.0
    )
    merged[COL_IMPORT_SHARE] = np.where(
        safe, merged["partner_imports"] / merged["world_value"], 0.0
    )
    result = merged[list(SHARE_COLUMNS)].copy()
    result[HS2_COL] = result[HS2_COL].astype(str).str.zfill(2)
    return result.sort_values(["year", HS2_COL, "partner"]).reset_index(drop=True)
