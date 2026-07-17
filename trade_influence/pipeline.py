"""End-to-end pipeline for STI / CWTI trade influence indices."""

from pathlib import Path

import pandas as pd

from trade_discrepancy.loaders import load_all_comtrade, load_imf
from trade_influence.constants import (
    COMTRADE_BILATERAL_PARTNERS,
    IMF_BILATERAL_PARTNERS,
    OUTPUT_DIR,
)
from trade_influence.imf_sti import compute_sti_imf
from trade_influence.indices import compute_cwti, compute_indices, compute_sti
from trade_influence.prepare import build_hs2_panel
from trade_influence.visualize import generate_all_plots

CORE_OUTPUT_FILES = (
    "hs2_panel_sample.csv",
    "sti_comtrade.csv",
    "cwti_comtrade.csv",
    "indices_comtrade.csv",
    "sti_imf.csv",
    "summary_sti_by_source_partner.csv",
    "summary_by_country_partner_comtrade.csv",
    "summary_by_country_partner_imf.csv",
)


def resolve_output_dirs(output_dir: Path = OUTPUT_DIR) -> tuple[Path, Path, Path]:
    """Return (root, csv_dir, plots_dir) and ensure both subfolders exist."""
    root = Path(output_dir)
    csv_dir = root / "csv"
    plots_dir = root / "plots"
    csv_dir.mkdir(parents=True, exist_ok=True)
    plots_dir.mkdir(parents=True, exist_ok=True)
    return root, csv_dir, plots_dir


def summarize_sti_by_source_partner(
    sti_comtrade: pd.DataFrame,
    sti_imf: pd.DataFrame,
) -> pd.DataFrame:
    """Headline STI stats by data source and partner."""
    rows: list[dict] = []
    for source, frame, partners in (
        ("comtrade", sti_comtrade, COMTRADE_BILATERAL_PARTNERS),
        ("imf", sti_imf, IMF_BILATERAL_PARTNERS),
    ):
        for partner in partners:
            group = frame[frame["partner"] == partner]
            if group.empty:
                continue
            rows.append(
                {
                    "source": source,
                    "partner": partner,
                    "n_observations": len(group),
                    "n_countries": group["country"].nunique(),
                    "year_min": int(group["year"].min()),
                    "year_max": int(group["year"].max()),
                    "mean_sti": group["sti"].mean(),
                    "median_sti": group["sti"].median(),
                }
            )
    return pd.DataFrame(rows)


def summarize_by_country_partner(indices: pd.DataFrame) -> pd.DataFrame:
    """Mean STI (and CWTI if present) by country and partner."""
    agg: dict[str, tuple[str, str]] = {
        "n_years": ("year", "nunique"),
        "mean_sti": ("sti", "mean"),
        "latest_year": ("year", "max"),
    }
    if "cwti" in indices.columns:
        agg["mean_cwti"] = ("cwti", "mean")
    return (
        indices.groupby(["country", "partner"], as_index=False)
        .agg(**agg)
        .sort_values(["country", "partner"])
        .reset_index(drop=True)
    )


def run_analysis(output_dir: Path = OUTPUT_DIR) -> dict:
    """
    Compute Comtrade STI/CWTI and IMF STI, then write CSV + time-series plots.

    Comtrade partners: Australia, China.
    IMF partners: Australia, China, United States.
    """
    output_dir, csv_dir, plots_dir = resolve_output_dirs(output_dir)

    comtrade_raw = load_all_comtrade()
    imf_raw = load_imf()

    panel = build_hs2_panel(comtrade_raw)
    sti_comtrade = compute_sti(panel)
    cwti_comtrade = compute_cwti(panel)
    indices_comtrade = compute_indices(panel)
    sti_imf = compute_sti_imf(imf_raw)

    by_source_partner = summarize_sti_by_source_partner(sti_comtrade, sti_imf)
    by_country_comtrade = summarize_by_country_partner(indices_comtrade)
    by_country_imf = summarize_by_country_partner(sti_imf)

    panel.head(5000).to_csv(csv_dir / "hs2_panel_sample.csv", index=False)
    sti_comtrade.to_csv(csv_dir / "sti_comtrade.csv", index=False)
    cwti_comtrade.to_csv(csv_dir / "cwti_comtrade.csv", index=False)
    indices_comtrade.to_csv(csv_dir / "indices_comtrade.csv", index=False)
    sti_imf.to_csv(csv_dir / "sti_imf.csv", index=False)
    by_source_partner.to_csv(csv_dir / "summary_sti_by_source_partner.csv", index=False)
    by_country_comtrade.to_csv(
        csv_dir / "summary_by_country_partner_comtrade.csv", index=False
    )
    by_country_imf.to_csv(csv_dir / "summary_by_country_partner_imf.csv", index=False)

    plot_paths = generate_all_plots(indices_comtrade, sti_imf, plots_dir)

    return {
        "comtrade_partners": list(COMTRADE_BILATERAL_PARTNERS),
        "imf_partners": list(IMF_BILATERAL_PARTNERS),
        "partners": list(COMTRADE_BILATERAL_PARTNERS),
        "n_panel_rows": len(panel),
        "n_index_observations": len(indices_comtrade),
        "n_imf_sti_observations": len(sti_imf),
        "n_countries": (
            int(indices_comtrade["country"].nunique())
            if not indices_comtrade.empty
            else 0
        ),
        "n_imf_countries": (
            int(sti_imf["country"].nunique()) if not sti_imf.empty else 0
        ),
        "year_min": (
            int(indices_comtrade["year"].min()) if not indices_comtrade.empty else None
        ),
        "year_max": (
            int(indices_comtrade["year"].max()) if not indices_comtrade.empty else None
        ),
        "imf_year_min": int(sti_imf["year"].min()) if not sti_imf.empty else None,
        "imf_year_max": int(sti_imf["year"].max()) if not sti_imf.empty else None,
        "output_dir": str(output_dir),
        "csv_dir": str(csv_dir),
        "plots_dir": str(plots_dir),
        "plots": [str(p) for p in plot_paths],
        "comtrade_raw": comtrade_raw,
        "imf_raw": imf_raw,
        "panel": panel,
        "sti": sti_comtrade,
        "sti_comtrade": sti_comtrade,
        "cwti": cwti_comtrade,
        "cwti_comtrade": cwti_comtrade,
        "indices": indices_comtrade,
        "indices_comtrade": indices_comtrade,
        "sti_imf": sti_imf,
        "by_partner": by_source_partner,
        "by_source_partner": by_source_partner,
        "by_country_partner": by_country_comtrade,
        "by_country_partner_comtrade": by_country_comtrade,
        "by_country_partner_imf": by_country_imf,
    }
