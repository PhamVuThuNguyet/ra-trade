"""Build long series panels (raw, STI, CWTI) for anomaly detection."""

from __future__ import annotations

import pandas as pd

from trade_discrepancy.constants import PARTNER_WORLD
from trade_influence.indices import compute_cwe, compute_cwi
from trade_influence.prepare import build_sitc2_panel, partner_flow_totals
from trade_anomaly.constants import (
    BILATERAL_PARTNER_ISOS,
    BILATERAL_PARTNERS,
    FLOW_TOTAL,
    METRIC_CWTI,
    METRIC_RAW,
    METRIC_STI,
)


def _series_id(country: str, partner: str, flow: str, metric: str) -> str:
    return f"{country}|{partner}|{flow}|{metric}"


def _frame_from_rows(rows: list[dict]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame(
            columns=[
                "series_id",
                "country",
                "partner",
                "flow",
                "metric",
                "year",
                "value",
            ]
        )
    return (
        pd.DataFrame(rows)
        .sort_values(["country", "partner", "flow", "metric", "year"])
        .reset_index(drop=True)
    )


def compute_flow_sti(
    totals: pd.DataFrame,
    *,
    bilateral_partners: tuple[str, ...] = BILATERAL_PARTNERS,
) -> pd.DataFrame:
    """STI^f = partner flow value / world flow value."""
    required = {"country", "year", "flow", "partner", "total_usd"}
    missing = required - set(totals.columns)
    if missing:
        raise KeyError(f"Flow totals missing columns: {sorted(missing)}")

    world = totals[totals["partner"] == PARTNER_WORLD][
        ["country", "year", "flow", "total_usd"]
    ].rename(columns={"total_usd": "world_usd"})
    bilateral = totals[totals["partner"].isin(bilateral_partners)].copy()
    merged = bilateral.merge(world, on=["country", "year", "flow"], how="inner")
    merged = merged[merged["world_usd"] > 0].copy()
    if merged.empty:
        return pd.DataFrame(columns=["country", "year", "partner", "flow", "sti"])
    merged["sti"] = merged["total_usd"] / merged["world_usd"]
    return (
        merged[["country", "year", "partner", "flow", "sti"]]
        .sort_values(["country", "year", "partner", "flow"])
        .reset_index(drop=True)
    )


def _combined_trade_share(
    totals: pd.DataFrame,
    bilateral_partners: tuple[str, ...],
) -> pd.DataFrame:
    """(imports_j + exports_j) / (TotalImport + TotalExport) for anomaly 'total' STI."""
    wide = totals.pivot_table(
        index=["country", "year", "partner"],
        columns="flow",
        values="total_usd",
        fill_value=0.0,
        aggfunc="sum",
    ).reset_index()
    wide.columns.name = None
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
    return merged[["country", "year", "partner", "sti"]]


def build_anomaly_hs2_panel(comtrade_raw: pd.DataFrame) -> pd.DataFrame:
    """SITC-2 panel including AUS, CHN, US, and World."""
    return build_sitc2_panel(
        comtrade_raw,
        bilateral_partner_isos=BILATERAL_PARTNER_ISOS,
    )


def build_series_panel(panel: pd.DataFrame) -> pd.DataFrame:
    """
    Long panel of anomaly series.

    Metrics:
      - raw_usd: bilateral import/export levels
      - sti: combined and flow-specific partner shares
      - cwti: combined and flow-specific concentration indices
    """
    totals = partner_flow_totals(panel)
    rows: list[dict] = []

    bilateral_totals = totals[totals["partner"].isin(BILATERAL_PARTNERS)]
    for row in bilateral_totals.itertuples(index=False):
        rows.append(
            {
                "series_id": _series_id(
                    row.country, row.partner, row.flow, METRIC_RAW
                ),
                "country": row.country,
                "partner": row.partner,
                "flow": row.flow,
                "metric": METRIC_RAW,
                "year": int(row.year),
                "value": float(row.total_usd),
            }
        )

    flow_sti = compute_flow_sti(totals, bilateral_partners=BILATERAL_PARTNERS)
    for row in flow_sti.itertuples(index=False):
        rows.append(
            {
                "series_id": _series_id(
                    row.country, row.partner, row.flow, METRIC_STI
                ),
                "country": row.country,
                "partner": row.partner,
                "flow": row.flow,
                "metric": METRIC_STI,
                "year": int(row.year),
                "value": float(row.sti),
            }
        )

    combined = _combined_trade_share(totals, BILATERAL_PARTNERS)
    for row in combined.itertuples(index=False):
        rows.append(
            {
                "series_id": _series_id(
                    row.country, row.partner, FLOW_TOTAL, METRIC_STI
                ),
                "country": row.country,
                "partner": row.partner,
                "flow": FLOW_TOTAL,
                "metric": METRIC_STI,
                "year": int(row.year),
                "value": float(row.sti),
            }
        )

    cwi = compute_cwi(panel, bilateral_partners=BILATERAL_PARTNERS)
    cwe = compute_cwe(panel, bilateral_partners=BILATERAL_PARTNERS)
    for row in cwi.itertuples(index=False):
        rows.append(
            {
                "series_id": _series_id(
                    row.country, row.partner, "import", METRIC_CWTI
                ),
                "country": row.country,
                "partner": row.partner,
                "flow": "import",
                "metric": METRIC_CWTI,
                "year": int(row.year),
                "value": float(row.cwi),
            }
        )
    for row in cwe.itertuples(index=False):
        rows.append(
            {
                "series_id": _series_id(
                    row.country, row.partner, "export", METRIC_CWTI
                ),
                "country": row.country,
                "partner": row.partner,
                "flow": "export",
                "metric": METRIC_CWTI,
                "year": int(row.year),
                "value": float(row.cwe),
            }
        )

    combined_cw = cwi.merge(cwe, on=["country", "year", "partner"], how="outer")
    combined_cw["cwi"] = combined_cw["cwi"].fillna(0.0)
    combined_cw["cwe"] = combined_cw["cwe"].fillna(0.0)
    combined_cw["cwti"] = combined_cw["cwi"] + combined_cw["cwe"]
    for row in combined_cw.itertuples(index=False):
        rows.append(
            {
                "series_id": _series_id(
                    row.country, row.partner, FLOW_TOTAL, METRIC_CWTI
                ),
                "country": row.country,
                "partner": row.partner,
                "flow": FLOW_TOTAL,
                "metric": METRIC_CWTI,
                "year": int(row.year),
                "value": float(row.cwti),
            }
        )

    return _frame_from_rows(rows)
