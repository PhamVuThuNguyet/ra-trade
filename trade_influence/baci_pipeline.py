"""BACI HS-2 I / E / CWI / CWE influence-index pipeline."""

from pathlib import Path

import pandas as pd

from baci.constants import BACI_DIR, CACHE_DIR
from baci.loaders import load_baci_extract
from trade_influence.baci_prepare import build_hs2_panel
from trade_influence.constants import (
    BACI_OUTPUT_DIR,
    BILATERAL_PARTNERS,
    COMMODITY_COL_HS2,
    SOURCE_BACI,
)
from trade_influence.indices import (
    compute_cwe,
    compute_cwi,
    compute_import_export_indices,
    compute_indices,
)
from trade_influence.pipeline import (
    ALL_INDEX_COLS,
    resolve_output_dirs,
    summarize_by_country_partner,
)
from trade_influence.visualize import generate_baci_plots

CORE_OUTPUT_FILES = (
    "hs2_panel_sample.csv",
    "global_hs2_shares.csv",
    "import_export_baci.csv",
    "cwi_baci.csv",
    "cwe_baci.csv",
    "indices_baci.csv",
    "summary_by_partner.csv",
    "summary_by_country_partner.csv",
)


def summarize_by_partner(indices: pd.DataFrame) -> pd.DataFrame:
    """Headline I / E / CWI / CWE by partner for the BACI panel."""
    rows: list[dict] = []
    for partner in BILATERAL_PARTNERS:
        group = indices[indices["partner"] == partner]
        if group.empty:
            continue
        row: dict = {
            "source": SOURCE_BACI,
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


def run_baci_analysis(
    output_dir: Path = BACI_OUTPUT_DIR,
    *,
    baci_dir: Path = BACI_DIR,
    use_cache: bool = True,
    cache_dir: Path = CACHE_DIR,
) -> dict:
    """
    Compute BACI I/E/CWI/CWE from HS-2 PIC panels and write CSV + plots.

    Partners: Australia, China, United States. World denominators are the sum
    of all BACI partners (there is no World aggregate in the source files).
    CWI/CWE also weight each chapter by the partner's share of world exports
    (CWI) or world imports (CWE) of that chapter.
    """
    output_dir, csv_dir, plots_dir = resolve_output_dirs(output_dir)
    pic_flows, _year_stats, global_shares = load_baci_extract(
        baci_dir, use_cache=use_cache, cache_dir=cache_dir
    )
    panel = build_hs2_panel(pic_flows)
    indices = compute_indices(
        panel, commodity_col=COMMODITY_COL_HS2, global_shares=global_shares
    )
    import_export = compute_import_export_indices(panel)
    cwi = compute_cwi(
        panel, commodity_col=COMMODITY_COL_HS2, global_shares=global_shares
    )
    cwe = compute_cwe(
        panel, commodity_col=COMMODITY_COL_HS2, global_shares=global_shares
    )
    by_partner = summarize_by_partner(indices)
    by_country = summarize_by_country_partner(indices)

    panel.head(5000).to_csv(csv_dir / "hs2_panel_sample.csv", index=False)
    global_shares.to_csv(csv_dir / "global_hs2_shares.csv", index=False)
    import_export.to_csv(csv_dir / "import_export_baci.csv", index=False)
    cwi.to_csv(csv_dir / "cwi_baci.csv", index=False)
    cwe.to_csv(csv_dir / "cwe_baci.csv", index=False)
    indices.to_csv(csv_dir / "indices_baci.csv", index=False)
    by_partner.to_csv(csv_dir / "summary_by_partner.csv", index=False)
    by_country.to_csv(csv_dir / "summary_by_country_partner.csv", index=False)

    plot_paths = generate_baci_plots(indices, plots_dir)
    return {
        "partners": list(BILATERAL_PARTNERS),
        "n_panel_rows": len(panel),
        "n_index_observations": len(indices),
        "n_countries": int(indices["country"].nunique()) if not indices.empty else 0,
        "year_min": int(indices["year"].min()) if not indices.empty else None,
        "year_max": int(indices["year"].max()) if not indices.empty else None,
        "output_dir": str(output_dir),
        "csv_dir": str(csv_dir),
        "plots_dir": str(plots_dir),
        "plots": [str(path) for path in plot_paths],
        "pic_flows": pic_flows,
        "global_shares": global_shares,
        "panel": panel,
        "import_export": import_export,
        "cwi": cwi,
        "cwe": cwe,
        "indices": indices,
        "by_partner": by_partner,
        "by_country_partner": by_country,
    }
