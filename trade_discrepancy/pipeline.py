"""Shared end-to-end analysis pipeline used by the CLI script and notebook."""

from pathlib import Path

import pandas as pd

from trade_discrepancy.constants import DISCREPANCY_TOLERANCE_PCT, OUTPUT_DIR
from trade_discrepancy.loaders import (
    build_comparison_table,
    comtrade_year_ranges,
    load_all_comtrade,
    load_imf,
)
from trade_discrepancy.metrics import (
    add_discrepancy_metrics,
    coverage_summary,
    summarize_by_year,
    summarize_discrepancies,
)
from trade_discrepancy.visualize import generate_all_plots

CORE_OUTPUT_FILES = (
    "comparison_metrics.csv",
    "summary_by_country_flow_partner.csv",
    "summary_by_year.csv",
    "coverage_summary.csv",
    "summary_by_partner.csv",
    "largest_world_discrepancies.csv",
)

ANALYSIS_DIMENSIONS = (
    "coverage",
    "harmonization",
    "discrepancy_magnitude",
    "temporal_trends",
    "structural_partner_flow",
)


def resolve_output_dirs(output_dir: Path = OUTPUT_DIR) -> tuple[Path, Path, Path]:
    """Return (root, csv_dir, plots_dir) and ensure both subfolders exist."""
    root = Path(output_dir)
    csv_dir = root / "csv"
    plots_dir = root / "plots"
    csv_dir.mkdir(parents=True, exist_ok=True)
    plots_dir.mkdir(parents=True, exist_ok=True)
    return root, csv_dir, plots_dir


def partner_headline_metrics(metrics: pd.DataFrame) -> pd.DataFrame:
    """Aggregate headline SymDiff% stats by partner (world / aus / china)."""
    rows: list[dict] = []
    for partner, group in metrics.groupby("partner", sort=False):
        rows.append(
            {
                "partner": partner,
                "n_observations": len(group),
                "median_symmetric_pct_diff": group["symmetric_pct_diff"].median(),
                "mean_abs_symmetric_pct_diff": group["symmetric_pct_diff"].abs().mean(),
                "share_within_tolerance": group["within_tolerance"].mean(),
            }
        )
    order = {"world": 0, "aus": 1, "china": 2}
    frame = pd.DataFrame(rows)
    return frame.sort_values(
        "partner", key=lambda s: s.map(lambda p: order.get(p, 99))
    ).reset_index(drop=True)


def largest_world_discrepancies(metrics: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Return the n largest absolute SymDiff% observations for world totals."""
    cols = [
        "country_comtrade",
        "year",
        "flow",
        "comtrade_value_musd",
        "imf_value_musd",
        "abs_diff_musd",
        "symmetric_pct_diff",
        "within_tolerance",
    ]
    world = metrics[metrics["partner"] == "world"].copy()
    world["abs_symmetric_pct"] = world["symmetric_pct_diff"].abs()
    available = [c for c in cols if c in world.columns]
    return (
        world.sort_values("abs_symmetric_pct", ascending=False)[available]
        .head(n)
        .reset_index(drop=True)
    )


def run_analysis(output_dir: Path = OUTPUT_DIR) -> dict:
    """
    Run the Comtrade vs IMF discrepancy analysis.

    Covers coverage, harmonization, discrepancy magnitude, temporal trends,
    and structural partner/flow decomposition.

    Writes CSVs to ``output_dir/csv/`` and plots to ``output_dir/plots/``.
    """
    output_dir, csv_dir, plots_dir = resolve_output_dirs(output_dir)

    comtrade_raw = load_all_comtrade()
    imf_raw = load_imf()
    comparison, comtrade_long, imf_long = build_comparison_table()
    metrics = add_discrepancy_metrics(comparison)
    summary = summarize_discrepancies(metrics)
    by_year = summarize_by_year(metrics)
    coverage = coverage_summary(comtrade_long, imf_long)
    year_ranges = comtrade_year_ranges()
    by_partner = partner_headline_metrics(metrics)
    top_world_gaps = largest_world_discrepancies(metrics)

    metrics.to_csv(csv_dir / "comparison_metrics.csv", index=False)
    summary.to_csv(csv_dir / "summary_by_country_flow_partner.csv", index=False)
    by_year.to_csv(csv_dir / "summary_by_year.csv", index=False)
    coverage.to_csv(csv_dir / "coverage_summary.csv", index=False)
    by_partner.to_csv(csv_dir / "summary_by_partner.csv", index=False)
    top_world_gaps.to_csv(csv_dir / "largest_world_discrepancies.csv", index=False)

    plot_paths = generate_all_plots(metrics, summary, coverage, plots_dir)

    world = metrics[metrics["partner"] == "world"]
    return {
        "analysis_dimensions": list(ANALYSIS_DIMENSIONS),
        "tolerance_pct": DISCREPANCY_TOLERANCE_PCT,
        "n_comparable_observations": len(metrics),
        "n_world_observations": len(world),
        "median_world_symmetric_pct_diff": float(world["symmetric_pct_diff"].median()),
        "mean_abs_world_symmetric_pct_diff": float(
            world["symmetric_pct_diff"].abs().mean()
        ),
        "share_world_within_5pct": float(world["within_tolerance"].mean()),
        "output_dir": str(output_dir),
        "csv_dir": str(csv_dir),
        "plots_dir": str(plots_dir),
        "plots": [str(p) for p in plot_paths],
        "comtrade_raw": comtrade_raw,
        "imf_raw": imf_raw,
        "comparison": comparison,
        "comtrade_long": comtrade_long,
        "imf_long": imf_long,
        "metrics": metrics,
        "summary": summary,
        "by_year": by_year,
        "coverage": coverage,
        "year_ranges": year_ranges,
        "by_partner": by_partner,
        "top_world_gaps": top_world_gaps,
    }
