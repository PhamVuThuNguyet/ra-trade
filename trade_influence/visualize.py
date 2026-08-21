"""Generate report-ready time-series figures for I, E, CWI, and CWE."""

from pathlib import Path

import pandas as pd

from trade_influence.constants import (
    BILATERAL_PARTNERS,
    INDEX_CWE,
    INDEX_CWI,
    INDEX_EXPORT,
    INDEX_IMPORT,
    OUTPUT_PLOTS_DIR,
)
from trade_influence.plotting import (
    plot_comtrade_vs_imf_by_partner,
    plot_comtrade_vs_imf_timeseries,
    plot_index_timeseries_by_country,
    plot_index_timeseries_by_partner,
)

__all__ = (
    "generate_all_plots",
    "plot_comtrade_vs_imf_by_partner",
    "plot_comtrade_vs_imf_timeseries",
    "plot_index_timeseries_by_country",
    "plot_index_timeseries_by_partner",
)

COMTRADE_PLOT_SPECS = (
    (INDEX_IMPORT, "Import index I (Comtrade)", "timeseries_import_index_comtrade"),
    (INDEX_EXPORT, "Export index E (Comtrade)", "timeseries_export_index_comtrade"),
    (INDEX_CWI, "CWI (Comtrade)", "timeseries_cwi_comtrade"),
    (INDEX_CWE, "CWE (Comtrade)", "timeseries_cwe_comtrade"),
)
IMF_PLOT_SPECS = (
    (INDEX_IMPORT, "Import index I (IMF)", "timeseries_import_index_imf"),
    (INDEX_EXPORT, "Export index E (IMF)", "timeseries_export_index_imf"),
)
OVERLAY_SPECS = (
    (INDEX_IMPORT, "Import index I: Comtrade vs IMF", "timeseries_import_index_comtrade_vs_imf"),
    (INDEX_EXPORT, "Export index E: Comtrade vs IMF", "timeseries_export_index_comtrade_vs_imf"),
)


def _plot_index_family(
    indices: pd.DataFrame,
    specs: tuple[tuple[str, str, str], ...],
    output_dir: Path,
) -> list[Path]:
    paths: list[Path] = []
    for value_col, title, filename_stem in specs:
        if value_col not in indices.columns:
            continue
        frame = indices[["country", "year", "partner", value_col]].dropna(
            subset=[value_col]
        )
        if frame.empty:
            continue
        paths.append(
            plot_index_timeseries_by_country(
                frame,
                value_col,
                BILATERAL_PARTNERS,
                output_dir,
                title=title,
                filename=f"{filename_stem}.png",
            )
        )
        paths.extend(
            plot_index_timeseries_by_partner(
                frame,
                value_col,
                BILATERAL_PARTNERS,
                output_dir,
                title_prefix=title,
                filename_prefix=f"{filename_stem}_by_partner",
            )
        )
    return paths


def generate_all_plots(
    indices_comtrade: pd.DataFrame,
    indices_imf: pd.DataFrame,
    output_dir: Path = OUTPUT_PLOTS_DIR,
) -> list[Path]:
    """Write report-ready time-series figures; replace any stale PNGs."""
    output_dir.mkdir(parents=True, exist_ok=True)
    for stale in output_dir.glob("*.png"):
        stale.unlink()

    paths: list[Path] = []
    if not indices_comtrade.empty:
        paths.extend(_plot_index_family(indices_comtrade, COMTRADE_PLOT_SPECS, output_dir))
    if not indices_imf.empty:
        paths.extend(_plot_index_family(indices_imf, IMF_PLOT_SPECS, output_dir))
    if not indices_comtrade.empty and not indices_imf.empty:
        for value_col, title, filename_stem in OVERLAY_SPECS:
            if (
                value_col not in indices_comtrade.columns
                or value_col not in indices_imf.columns
            ):
                continue
            paths.append(
                plot_comtrade_vs_imf_timeseries(
                    indices_comtrade,
                    indices_imf,
                    value_col,
                    output_dir,
                    title=title,
                    filename=f"{filename_stem}.png",
                )
            )
            paths.extend(
                plot_comtrade_vs_imf_by_partner(
                    indices_comtrade,
                    indices_imf,
                    value_col,
                    output_dir,
                    title_prefix=title.split(":")[0],
                    filename_prefix=f"{filename_stem}_by_partner",
                )
            )
    return paths
