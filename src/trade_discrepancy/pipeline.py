"""Shared end-to-end analysis pipeline used by the CLI script and notebook."""

from pathlib import Path

import pandas as pd

from trade_discrepancy.constants import (
    COMTRADE_TO_IMF_COUNTRY,
    DISCREPANCY_TOLERANCE_PCT,
    OUTPUT_DIR,
    PARTNER_WORLD,
)
from trade_discrepancy.harmonize import aggregate_comtrade, melt_imf, merge_sources
from trade_discrepancy.loaders import comtrade_availability_by_year, load_comtrade, load_imf
from trade_discrepancy.metadata import (
    coverage_summary_from_metadata,
    run_metadata_discrepancy_analysis,
)
from trade_discrepancy.metrics import (
    add_discrepancy_metrics,
    largest_world_discrepancies,
    partner_headline_metrics,
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
    "comtrade_availability_by_year.csv",
    "metadata_attribute_comparison.csv",
    "metadata_coverage_by_country.csv",
    "metadata_discrepancy_flags.csv",
    "valuation_completeness.csv",
    "schema_comparison.csv",
    "classification_grain.csv",
    "reporter_coverage.csv",
)

ANALYSIS_DIMENSIONS = (
    "metadata_discrepancies",
    "coverage",
    "harmonization",
    "discrepancy_magnitude",
    "temporal_trends",
    "structural_partner_flow",
)

METADATA_CSV_KEYS = (
    ("metadata_attributes", "metadata_attribute_comparison.csv"),
    ("metadata_coverage", "metadata_coverage_by_country.csv"),
    ("metadata_flags", "metadata_discrepancy_flags.csv"),
    ("valuation_completeness", "valuation_completeness.csv"),
    ("schema_comparison", "schema_comparison.csv"),
    ("classification_grain", "classification_grain.csv"),
    ("reporter_coverage", "reporter_coverage.csv"),
)


def resolve_output_dirs(output_dir: Path = OUTPUT_DIR) -> tuple[Path, Path, Path]:
    """Return (root, csv_dir, plots_dir) and ensure both subfolders exist."""
    root = Path(output_dir)
    csv_dir = root / "csv"
    plots_dir = root / "plots"
    csv_dir.mkdir(parents=True, exist_ok=True)
    plots_dir.mkdir(parents=True, exist_ok=True)
    return root, csv_dir, plots_dir


def _write_csv(frame: pd.DataFrame, path: Path) -> None:
    frame.to_csv(path, index=False)


def run_analysis(output_dir: Path = OUTPUT_DIR) -> dict:
    """
    Run the Comtrade vs IMF discrepancy analysis.

    Covers metadata discrepancies, coverage, harmonization, discrepancy
    magnitude, temporal trends, and structural partner/flow decomposition.

    Writes CSVs to ``output_dir/csv/`` and plots to ``output_dir/plots/``.
    """
    output_dir, csv_dir, plots_dir = resolve_output_dirs(output_dir)

    comtrade_raw = load_comtrade()
    imf_raw = load_imf()
    comtrade_long = aggregate_comtrade(comtrade_raw)
    imf_long = melt_imf(imf_raw)
    comparison = merge_sources(comtrade_long, imf_long, COMTRADE_TO_IMF_COUNTRY)

    metrics = add_discrepancy_metrics(comparison)
    summary = summarize_discrepancies(metrics)
    by_year = summarize_by_year(metrics)
    by_partner = partner_headline_metrics(metrics)
    top_world_gaps = largest_world_discrepancies(metrics)
    availability = comtrade_availability_by_year(comtrade_raw)
    metadata = run_metadata_discrepancy_analysis(comtrade_raw, imf_raw)
    coverage = coverage_summary_from_metadata(metadata["metadata_coverage"])

    _write_csv(metrics, csv_dir / "comparison_metrics.csv")
    _write_csv(availability, csv_dir / "comtrade_availability_by_year.csv")
    _write_csv(summary, csv_dir / "summary_by_country_flow_partner.csv")
    _write_csv(by_year, csv_dir / "summary_by_year.csv")
    _write_csv(coverage, csv_dir / "coverage_summary.csv")
    _write_csv(by_partner, csv_dir / "summary_by_partner.csv")
    _write_csv(top_world_gaps, csv_dir / "largest_world_discrepancies.csv")
    for key, filename in METADATA_CSV_KEYS:
        _write_csv(metadata[key], csv_dir / filename)

    plot_paths = generate_all_plots(metrics, summary, plots_dir)
    world = metrics[metrics["partner"] == PARTNER_WORLD]
    return {
        "analysis_dimensions": list(ANALYSIS_DIMENSIONS),
        "tolerance_pct": DISCREPANCY_TOLERANCE_PCT,
        "n_comparable_observations": len(metrics),
        "n_world_observations": len(world),
        "median_world_symmetric_pct_diff": float(world["symmetric_pct_diff"].median()),
        "mean_abs_world_symmetric_pct_diff": float(
            world["symmetric_pct_diff"].abs().mean()
        ),
        "share_world_within_tolerance": float(world["within_tolerance"].mean()),
        "output_dir": str(output_dir),
        "csv_dir": str(csv_dir),
        "plots_dir": str(plots_dir),
        "plots": [str(path) for path in plot_paths],
        "comtrade_raw": comtrade_raw,
        "imf_raw": imf_raw,
        "comparison": comparison,
        "comtrade_long": comtrade_long,
        "imf_long": imf_long,
        "metrics": metrics,
        "summary": summary,
        "by_year": by_year,
        "coverage": coverage,
        "availability": availability,
        "by_partner": by_partner,
        "top_world_gaps": top_world_gaps,
        **metadata,
    }
