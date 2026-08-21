"""End-to-end pipeline for I / E / CWI / CWE trade influence indices."""

from pathlib import Path

import pandas as pd

from trade_discrepancy.loaders import load_comtrade, load_imf
from trade_influence.constants import (
    BILATERAL_PARTNERS,
    INDEX_CWE,
    INDEX_CWI,
    INDEX_EXPORT,
    INDEX_IMPORT,
    OUTPUT_DIR,
)
from trade_influence.imf_indices import compute_import_export_indices_imf
from trade_influence.indices import (
    compute_cwe,
    compute_cwi,
    compute_import_export_indices,
    compute_indices,
)
from trade_influence.prepare import build_sitc2_panel
from trade_influence.visualize import generate_all_plots

CORE_OUTPUT_FILES = (
    "sitc2_panel_sample.csv",
    "import_export_comtrade.csv",
    "cwi_comtrade.csv",
    "cwe_comtrade.csv",
    "indices_comtrade.csv",
    "import_export_imf.csv",
    "summary_by_source_partner.csv",
    "summary_by_country_partner_comtrade.csv",
    "summary_by_country_partner_imf.csv",
)

ALL_INDEX_COLS = (INDEX_IMPORT, INDEX_EXPORT, INDEX_CWI, INDEX_CWE)


def resolve_output_dirs(output_dir: Path = OUTPUT_DIR) -> tuple[Path, Path, Path]:
    """Return (root, csv_dir, plots_dir) and ensure both subfolders exist."""
    root = Path(output_dir)
    csv_dir = root / "csv"
    plots_dir = root / "plots"
    csv_dir.mkdir(parents=True, exist_ok=True)
    plots_dir.mkdir(parents=True, exist_ok=True)
    return root, csv_dir, plots_dir


def summarize_by_source_partner(
    indices_comtrade: pd.DataFrame,
    indices_imf: pd.DataFrame,
) -> pd.DataFrame:
    """Headline I / E (and CWI / CWE when present) by source and partner."""
    rows: list[dict] = []
    for source, frame in (
        ("comtrade", indices_comtrade),
        ("imf", indices_imf),
    ):
        for partner in BILATERAL_PARTNERS:
            group = frame[frame["partner"] == partner]
            if group.empty:
                continue
            row: dict = {
                "source": source,
                "partner": partner,
                "n_observations": len(group),
                "n_countries": group["country"].nunique(),
                "year_min": int(group["year"].min()),
                "year_max": int(group["year"].max()),
            }
            for col in ALL_INDEX_COLS:
                if col in group.columns:
                    row[f"mean_{col}"] = group[col].mean()
                    row[f"median_{col}"] = group[col].median()
            rows.append(row)
    return pd.DataFrame(rows)


def summarize_by_country_partner(indices: pd.DataFrame) -> pd.DataFrame:
    """Mean I / E (and CWI / CWE if present) by country and partner."""
    agg: dict[str, tuple[str, str]] = {
        "n_years": ("year", "nunique"),
        "latest_year": ("year", "max"),
    }
    for col in ALL_INDEX_COLS:
        if col in indices.columns:
            agg[f"mean_{col}"] = (col, "mean")
    return (
        indices.groupby(["country", "partner"], as_index=False)
        .agg(**agg)
        .sort_values(["country", "partner"])
        .reset_index(drop=True)
    )


def run_analysis(output_dir: Path = OUTPUT_DIR) -> dict:
    """
    Compute Comtrade I/E/CWI/CWE and IMF I/E, then write CSV + time-series plots.

    Partners: Australia, China, United States.
    """
    output_dir, csv_dir, plots_dir = resolve_output_dirs(output_dir)

    comtrade_raw = load_comtrade()
    imf_raw = load_imf()

    panel = build_sitc2_panel(comtrade_raw)
    indices_comtrade = compute_indices(panel)
    import_export_comtrade = compute_import_export_indices(panel)
    cwi_comtrade = compute_cwi(panel)
    cwe_comtrade = compute_cwe(panel)
    indices_imf = compute_import_export_indices_imf(imf_raw)

    by_source_partner = summarize_by_source_partner(indices_comtrade, indices_imf)
    by_country_comtrade = summarize_by_country_partner(indices_comtrade)
    by_country_imf = summarize_by_country_partner(indices_imf)

    panel.head(5000).to_csv(csv_dir / "sitc2_panel_sample.csv", index=False)
    import_export_comtrade.to_csv(csv_dir / "import_export_comtrade.csv", index=False)
    cwi_comtrade.to_csv(csv_dir / "cwi_comtrade.csv", index=False)
    cwe_comtrade.to_csv(csv_dir / "cwe_comtrade.csv", index=False)
    indices_comtrade.to_csv(csv_dir / "indices_comtrade.csv", index=False)
    indices_imf.to_csv(csv_dir / "import_export_imf.csv", index=False)
    by_source_partner.to_csv(csv_dir / "summary_by_source_partner.csv", index=False)
    by_country_comtrade.to_csv(
        csv_dir / "summary_by_country_partner_comtrade.csv", index=False
    )
    by_country_imf.to_csv(csv_dir / "summary_by_country_partner_imf.csv", index=False)

    plot_paths = generate_all_plots(indices_comtrade, indices_imf, plots_dir)

    return {
        "partners": list(BILATERAL_PARTNERS),
        "n_panel_rows": len(panel),
        "n_index_observations": len(indices_comtrade),
        "n_imf_observations": len(indices_imf),
        "n_countries": (
            int(indices_comtrade["country"].nunique())
            if not indices_comtrade.empty
            else 0
        ),
        "n_imf_countries": (
            int(indices_imf["country"].nunique()) if not indices_imf.empty else 0
        ),
        "year_min": (
            int(indices_comtrade["year"].min()) if not indices_comtrade.empty else None
        ),
        "year_max": (
            int(indices_comtrade["year"].max()) if not indices_comtrade.empty else None
        ),
        "imf_year_min": int(indices_imf["year"].min()) if not indices_imf.empty else None,
        "imf_year_max": int(indices_imf["year"].max()) if not indices_imf.empty else None,
        "output_dir": str(output_dir),
        "csv_dir": str(csv_dir),
        "plots_dir": str(plots_dir),
        "plots": [str(p) for p in plot_paths],
        "comtrade_raw": comtrade_raw,
        "imf_raw": imf_raw,
        "panel": panel,
        "import_export_comtrade": import_export_comtrade,
        "cwi_comtrade": cwi_comtrade,
        "cwe_comtrade": cwe_comtrade,
        "indices": indices_comtrade,
        "indices_comtrade": indices_comtrade,
        "indices_imf": indices_imf,
        "by_source_partner": by_source_partner,
        "by_country_partner": by_country_comtrade,
        "by_country_partner_comtrade": by_country_comtrade,
        "by_country_partner_imf": by_country_imf,
    }
