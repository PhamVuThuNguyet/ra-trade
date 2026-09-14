"""End-to-end multi-scale Comtrade trade anomaly pipeline."""

from pathlib import Path

import pandas as pd

from trade_discrepancy.loaders import load_comtrade
from trade_anomaly.acf_diagnostics import acf_summary_for_panel
from trade_anomaly.constants import (
    BILATERAL_PARTNERS,
    OUTPUT_DIR,
    TIER_NONE,
    WINDOWS_YEARS,
)
from trade_anomaly.detect import score_all_series
from trade_anomaly.fuse import fuse_scores, summarize_alerts
from trade_anomaly.prepare import build_anomaly_hs2_panel, build_series_panel
from trade_anomaly.visualize import generate_all_plots

CORE_OUTPUT_FILES = (
    "series_panel.csv",
    "acf_summary.csv",
    "anomaly_scores.csv",
    "alerts.csv",
    "summary_by_country_partner_tier.csv",
    "summary_by_tier.csv",
)


def resolve_output_dirs(output_dir: Path = OUTPUT_DIR) -> tuple[Path, Path, Path]:
    root = Path(output_dir)
    csv_dir = root / "csv"
    plots_dir = root / "plots"
    csv_dir.mkdir(parents=True, exist_ok=True)
    plots_dir.mkdir(parents=True, exist_ok=True)
    return root, csv_dir, plots_dir


def summarize_by_tier(alerts: pd.DataFrame) -> pd.DataFrame:
    flagged = alerts[alerts["tier"] != TIER_NONE]
    if flagged.empty:
        return pd.DataFrame(columns=["tier", "n_alerts", "n_series", "n_countries"])
    return (
        flagged.groupby("tier", as_index=False)
        .agg(
            n_alerts=("year", "count"),
            n_series=("series_id", "nunique"),
            n_countries=("country", "nunique"),
        )
        .sort_values("tier")
        .reset_index(drop=True)
    )


def run_analysis(
    output_dir: Path = OUTPUT_DIR,
    *,
    windows: tuple[int, ...] = WINDOWS_YEARS,
) -> dict:
    """
    Comtrade-only multi-scale anomaly detection with operational attention tiers.

    Partners: Australia, China, United States. Metrics: raw USD, STI, CWTI.
    """
    output_dir, csv_dir, plots_dir = resolve_output_dirs(output_dir)

    comtrade_raw = load_comtrade()
    panel = build_anomaly_hs2_panel(comtrade_raw)
    series_panel = build_series_panel(panel)
    acf_summary = acf_summary_for_panel(series_panel)
    scores = score_all_series(series_panel, windows=windows)
    alerts = fuse_scores(scores)
    by_country_partner = summarize_alerts(alerts)
    by_tier = summarize_by_tier(alerts)

    series_panel.to_csv(csv_dir / "series_panel.csv", index=False)
    acf_summary.to_csv(csv_dir / "acf_summary.csv", index=False)
    scores.to_csv(csv_dir / "anomaly_scores.csv", index=False)
    alerts.to_csv(csv_dir / "alerts.csv", index=False)
    by_country_partner.to_csv(
        csv_dir / "summary_by_country_partner_tier.csv", index=False
    )
    by_tier.to_csv(csv_dir / "summary_by_tier.csv", index=False)

    plot_paths = generate_all_plots(series_panel, scores, alerts, plots_dir)

    flagged = alerts[alerts["tier"] != TIER_NONE]
    return {
        "partners": list(BILATERAL_PARTNERS),
        "windows": list(windows),
        "n_panel_rows": len(panel),
        "n_series": int(series_panel["series_id"].nunique())
        if not series_panel.empty
        else 0,
        "n_series_years": len(series_panel),
        "n_score_rows": len(scores),
        "n_alerts": len(flagged),
        "n_countries": (
            int(series_panel["country"].nunique()) if not series_panel.empty else 0
        ),
        "year_min": (
            int(series_panel["year"].min()) if not series_panel.empty else None
        ),
        "year_max": (
            int(series_panel["year"].max()) if not series_panel.empty else None
        ),
        "output_dir": str(output_dir),
        "csv_dir": str(csv_dir),
        "plots_dir": str(plots_dir),
        "plots": [str(p) for p in plot_paths],
        "comtrade_raw": comtrade_raw,
        "panel": panel,
        "series_panel": series_panel,
        "acf_summary": acf_summary,
        "scores": scores,
        "alerts": alerts,
        "by_country_partner_tier": by_country_partner,
        "by_tier": by_tier,
    }
