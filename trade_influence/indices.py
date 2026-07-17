"""Simple Trade Index (STI) and Commodity Weighted Trade Index (CWTI)."""

import numpy as np
import pandas as pd

from trade_discrepancy.constants import PARTNER_WORLD
from trade_influence.constants import BILATERAL_PARTNERS, COMTRADE_BILATERAL_PARTNERS
from trade_influence.prepare import partner_flow_totals


def compute_sti_from_totals(
    totals: pd.DataFrame,
    *,
    value_col: str = "total_usd",
    bilateral_partners: tuple[str, ...] = BILATERAL_PARTNERS,
) -> pd.DataFrame:
    """
    STI_{i,j,t} = (imports_{i,j,t} + exports_{i,j,t})
                  / (TotalImport_{i,t} + TotalExport_{i,t})

    ``totals`` must contain country, year, flow, partner, and ``value_col``.
    World totals use partner ``world``. Rows with a zero denominator are dropped.
    """
    required = {"country", "year", "flow", "partner", value_col}
    missing = required - set(totals.columns)
    if missing:
        raise KeyError(f"Flow totals missing columns: {sorted(missing)}")

    wide = totals.pivot_table(
        index=["country", "year", "partner"],
        columns="flow",
        values=value_col,
        fill_value=0.0,
        aggfunc="sum",
    ).reset_index()
    for flow in ("import", "export"):
        if flow not in wide.columns:
            wide[flow] = 0.0

    world = wide[wide["partner"] == PARTNER_WORLD][
        ["country", "year", "import", "export"]
    ].rename(columns={"import": "total_import", "export": "total_export"})

    bilateral = wide[wide["partner"].isin(bilateral_partners)].copy()
    merged = bilateral.merge(world, on=["country", "year"], how="inner")
    merged["denominator"] = merged["total_import"] + merged["total_export"]
    merged = merged[merged["denominator"] > 0].copy()
    if merged.empty:
        return pd.DataFrame(columns=["country", "year", "partner", "sti"])
    merged["sti"] = (merged["import"] + merged["export"]) / merged["denominator"]
    return (
        merged[["country", "year", "partner", "sti"]]
        .sort_values(["country", "year", "partner"])
        .reset_index(drop=True)
    )


def compute_sti(panel: pd.DataFrame) -> pd.DataFrame:
    """Compute STI from a Comtrade HS2 commodity panel."""
    return compute_sti_from_totals(
        partner_flow_totals(panel),
        value_col="total_usd",
        bilateral_partners=COMTRADE_BILATERAL_PARTNERS,
    )


def _flow_cwti_terms(panel: pd.DataFrame, flow: str) -> pd.DataFrame:
    """Commodity-level CWTI terms for one flow (import or export)."""
    flow_panel = panel[panel["flow"] == flow]
    if flow_panel.empty:
        return pd.DataFrame(columns=["country", "year", "partner", "term"])

    world = flow_panel[flow_panel["partner"] == PARTNER_WORLD][
        ["country", "year", "hs2", "value_usd"]
    ].rename(columns={"value_usd": "world_c"})

    world_total = (
        world.groupby(["country", "year"], as_index=False)["world_c"]
        .sum()
        .rename(columns={"world_c": "world_total"})
    )

    bilateral = flow_panel[flow_panel["partner"].isin(COMTRADE_BILATERAL_PARTNERS)][
        ["country", "year", "partner", "hs2", "value_usd"]
    ].rename(columns={"value_usd": "bilateral"})

    # Universe of commodities is world totals; missing bilateral → 0.
    base = world.merge(world_total, on=["country", "year"], how="left")
    rows: list[pd.DataFrame] = []
    for partner in COMTRADE_BILATERAL_PARTNERS:
        partner_bilateral = bilateral[bilateral["partner"] == partner].drop(
            columns=["partner"]
        )
        merged = base.merge(
            partner_bilateral, on=["country", "year", "hs2"], how="left"
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


def compute_cwti(panel: pd.DataFrame) -> pd.DataFrame:
    """
    CWTI_{i,j,t} = Σ_c [(imp share_{c,j})^2 × (imp commodity weight_c)]
                 + Σ_c [(exp share_{c,j})^2 × (exp commodity weight_c)]
    """
    import_terms = _flow_cwti_terms(panel, "import")
    export_terms = _flow_cwti_terms(panel, "export")
    terms = pd.concat([import_terms, export_terms], ignore_index=True)
    if terms.empty:
        return pd.DataFrame(columns=["country", "year", "partner", "cwti"])

    cwti = (
        terms.groupby(["country", "year", "partner"], as_index=False)["term"]
        .sum()
        .rename(columns={"term": "cwti"})
        .sort_values(["country", "year", "partner"])
        .reset_index(drop=True)
    )
    return cwti


def compute_indices(panel: pd.DataFrame) -> pd.DataFrame:
    """Return merged Comtrade STI and CWTI for each country–year–partner."""
    sti = compute_sti(panel)
    cwti = compute_cwti(panel)
    return sti.merge(cwti, on=["country", "year", "partner"], how="outer").sort_values(
        ["country", "year", "partner"]
    ).reset_index(drop=True)
