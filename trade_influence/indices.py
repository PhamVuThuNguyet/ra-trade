"""Import/export share indices (I, E) and commodity-weighted indices (CWI, CWE)."""

import numpy as np
import pandas as pd

from trade_discrepancy.constants import PARTNER_WORLD
from trade_influence.constants import (
    BILATERAL_PARTNERS,
    COMMODITY_COL,
    FLOW_TO_CW_INDEX,
    FLOW_TO_SHARE_INDEX,
    INDEX_CWE,
    INDEX_CWI,
    INDEX_EXPORT,
    INDEX_IMPORT,
)
from trade_influence.prepare import partner_flow_totals


def compute_flow_share_from_totals(
    totals: pd.DataFrame,
    *,
    value_col: str = "total_usd",
    bilateral_partners: tuple[str, ...] = BILATERAL_PARTNERS,
) -> pd.DataFrame:
    """
    I_{i,j,t} = imports_{i,j,t} / TotalImports_{i,t}
    E_{i,j,t} = exports_{i,j,t} / TotalExports_{i,t}

    ``totals`` must contain country, year, flow, partner, and ``value_col``.
    World totals use partner ``world``. Partners with no bilateral rows are 0.
    Rows with a zero world denominator are dropped.
    """
    required = {"country", "year", "flow", "partner", value_col}
    missing = required - set(totals.columns)
    if missing:
        raise KeyError(f"Flow totals missing columns: {sorted(missing)}")

    wide = totals.pivot_table(
        index=["country", "year", "flow"],
        columns="partner",
        values=value_col,
        fill_value=0.0,
        aggfunc="sum",
    ).reset_index()
    wide.columns.name = None
    if PARTNER_WORLD not in wide.columns:
        return pd.DataFrame(columns=["country", "year", "partner", "flow", "share"])

    wide = wide[wide[PARTNER_WORLD] > 0].copy()
    if wide.empty:
        return pd.DataFrame(columns=["country", "year", "partner", "flow", "share"])

    frames: list[pd.DataFrame] = []
    for partner in bilateral_partners:
        bilateral = (
            wide[partner] if partner in wide.columns else pd.Series(0.0, index=wide.index)
        )
        frames.append(
            pd.DataFrame(
                {
                    "country": wide["country"].values,
                    "year": wide["year"].values,
                    "flow": wide["flow"].values,
                    "partner": partner,
                    "share": bilateral.to_numpy(dtype="float64")
                    / wide[PARTNER_WORLD].to_numpy(dtype="float64"),
                }
            )
        )
    return (
        pd.concat(frames, ignore_index=True)
        .sort_values(["country", "year", "partner", "flow"])
        .reset_index(drop=True)
    )


def pivot_flow_shares(shares: pd.DataFrame) -> pd.DataFrame:
    """Wide I / E columns from long flow shares."""
    if shares.empty:
        return pd.DataFrame(
            columns=["country", "year", "partner", INDEX_IMPORT, INDEX_EXPORT]
        )
    working = shares.copy()
    working["index_name"] = working["flow"].map(FLOW_TO_SHARE_INDEX)
    working = working.dropna(subset=["index_name"])
    wide = working.pivot_table(
        index=["country", "year", "partner"],
        columns="index_name",
        values="share",
        fill_value=0.0,
        aggfunc="sum",
    ).reset_index()
    wide.columns.name = None
    for col in (INDEX_IMPORT, INDEX_EXPORT):
        if col not in wide.columns:
            wide[col] = 0.0
    return (
        wide[["country", "year", "partner", INDEX_IMPORT, INDEX_EXPORT]]
        .sort_values(["country", "year", "partner"])
        .reset_index(drop=True)
    )


def compute_import_export_indices(
    panel: pd.DataFrame,
    *,
    bilateral_partners: tuple[str, ...] = BILATERAL_PARTNERS,
) -> pd.DataFrame:
    """Compute I and E from a SITC-2 commodity panel."""
    return pivot_flow_shares(
        compute_flow_share_from_totals(
            partner_flow_totals(panel),
            value_col="total_usd",
            bilateral_partners=bilateral_partners,
        )
    )


def _flow_cw_terms(
    panel: pd.DataFrame,
    flow: str,
    *,
    bilateral_partners: tuple[str, ...] = BILATERAL_PARTNERS,
) -> pd.DataFrame:
    """HHI-style commodity terms for one flow (import → CWI, export → CWE)."""
    flow_panel = panel[panel["flow"] == flow]
    if flow_panel.empty:
        return pd.DataFrame(columns=["country", "year", "partner", "term"])

    world = flow_panel[flow_panel["partner"] == PARTNER_WORLD][
        ["country", "year", COMMODITY_COL, "value_usd"]
    ].rename(columns={"value_usd": "world_c"})

    world_total = (
        world.groupby(["country", "year"], as_index=False)["world_c"]
        .sum()
        .rename(columns={"world_c": "world_total"})
    )

    bilateral = flow_panel[flow_panel["partner"].isin(bilateral_partners)][
        ["country", "year", "partner", COMMODITY_COL, "value_usd"]
    ].rename(columns={"value_usd": "bilateral"})

    base = world.merge(world_total, on=["country", "year"], how="left")
    rows: list[pd.DataFrame] = []
    for partner in bilateral_partners:
        partner_bilateral = bilateral[bilateral["partner"] == partner].drop(
            columns=["partner"]
        )
        merged = base.merge(
            partner_bilateral, on=["country", "year", COMMODITY_COL], how="left"
        )
        merged["bilateral"] = merged["bilateral"].fillna(0.0)
        merged["partner"] = partner
        rows.append(merged)

    if not rows:
        return pd.DataFrame(columns=["country", "year", "partner", "term"])

    terms = pd.concat(rows, ignore_index=True)
    safe_world_c = terms["world_c"] > 0
    partner_share = np.where(
        safe_world_c, terms["bilateral"] / terms["world_c"], 0.0
    )
    commodity_weight = np.where(
        terms["world_total"] > 0, terms["world_c"] / terms["world_total"], 0.0
    )
    terms["term"] = (partner_share**2) * commodity_weight
    return terms[["country", "year", "partner", "term"]]


def compute_commodity_weighted(
    panel: pd.DataFrame,
    flow: str,
    *,
    bilateral_partners: tuple[str, ...] = BILATERAL_PARTNERS,
) -> pd.DataFrame:
    """
    CWI/CWE for one flow:

    Σ_c [(partner share of commodity c)² × (commodity c share of total flow)]
    """
    index_name = FLOW_TO_CW_INDEX.get(flow)
    if index_name is None:
        raise ValueError(f"flow must be 'import' or 'export', got {flow!r}")
    terms = _flow_cw_terms(panel, flow, bilateral_partners=bilateral_partners)
    if terms.empty:
        return pd.DataFrame(columns=["country", "year", "partner", index_name])
    return (
        terms.groupby(["country", "year", "partner"], as_index=False)["term"]
        .sum()
        .rename(columns={"term": index_name})
        .sort_values(["country", "year", "partner"])
        .reset_index(drop=True)
    )


def compute_cwi(
    panel: pd.DataFrame,
    *,
    bilateral_partners: tuple[str, ...] = BILATERAL_PARTNERS,
) -> pd.DataFrame:
    """Commodity Weighted Import index (CWI)."""
    return compute_commodity_weighted(
        panel, "import", bilateral_partners=bilateral_partners
    )


def compute_cwe(
    panel: pd.DataFrame,
    *,
    bilateral_partners: tuple[str, ...] = BILATERAL_PARTNERS,
) -> pd.DataFrame:
    """Commodity Weighted Export index (CWE)."""
    return compute_commodity_weighted(
        panel, "export", bilateral_partners=bilateral_partners
    )


def compute_indices(
    panel: pd.DataFrame,
    *,
    bilateral_partners: tuple[str, ...] = BILATERAL_PARTNERS,
) -> pd.DataFrame:
    """Merged I, E, CWI, and CWE for each country–year–partner."""
    shares = compute_import_export_indices(
        panel, bilateral_partners=bilateral_partners
    )
    cwi = compute_cwi(panel, bilateral_partners=bilateral_partners)
    cwe = compute_cwe(panel, bilateral_partners=bilateral_partners)
    merged = shares.merge(cwi, on=["country", "year", "partner"], how="outer")
    merged = merged.merge(cwe, on=["country", "year", "partner"], how="outer")
    for col in (INDEX_IMPORT, INDEX_EXPORT, INDEX_CWI, INDEX_CWE):
        if col not in merged.columns:
            merged[col] = 0.0
        else:
            merged[col] = merged[col].fillna(0.0)
    return merged.sort_values(["country", "year", "partner"]).reset_index(drop=True)
