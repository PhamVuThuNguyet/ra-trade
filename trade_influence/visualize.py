"""Time-series plots for STI and CWTI trade influence indices."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from trade_influence.constants import (
    COMTRADE_BILATERAL_PARTNERS,
    IMF_BILATERAL_PARTNERS,
    OUTPUT_PLOTS_DIR,
    PARTNER_DISPLAY,
    PARTNER_PLOT_COLORS,
    SOURCE_COMTRADE,
    SOURCE_DISPLAY,
    SOURCE_IMF,
    SOURCE_LINESTYLES,
)


def _save_figure(fig: plt.Figure, output_dir: Path, filename: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / filename
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def _plot_partner_lines(
    ax: plt.Axes,
    frame: pd.DataFrame,
    value_col: str,
    partners: tuple[str, ...],
    *,
    linestyle: str = "-",
    label_suffix: str = "",
) -> None:
    for partner in partners:
        series = frame[frame["partner"] == partner].sort_values("year")
        if series.empty or series[value_col].isna().all():
            continue
        label = PARTNER_DISPLAY.get(partner, partner) + label_suffix
        ax.plot(
            series["year"],
            series[value_col],
            marker="o",
            markersize=3.5,
            linewidth=2,
            linestyle=linestyle,
            color=PARTNER_PLOT_COLORS.get(partner, None),
            label=label,
        )


def plot_index_timeseries_by_country(
    indices: pd.DataFrame,
    value_col: str,
    partners: tuple[str, ...],
    output_dir: Path = OUTPUT_PLOTS_DIR,
    *,
    title: str,
    filename: str,
) -> Path:
    """One subplot per country; partner lines over years."""
    countries = sorted(indices["country"].unique())
    n_rows = max(len(countries), 1)
    fig, axes = plt.subplots(
        n_rows,
        1,
        figsize=(10, max(2.2 * n_rows, 4)),
        sharex=True,
        squeeze=False,
    )
    label = value_col.upper()
    for ax, country in zip(axes[:, 0], countries):
        country_data = indices[indices["country"] == country]
        _plot_partner_lines(ax, country_data, value_col, partners)
        ax.set_ylabel(label)
        ax.set_title(country)
        ax.grid(True, alpha=0.3)
        ax.legend(loc="best", fontsize=8)

    axes[-1, 0].set_xlabel("Year")
    fig.suptitle(title, y=1.01, fontsize=12)
    fig.tight_layout()
    return _save_figure(fig, output_dir, filename)


def plot_index_timeseries_by_partner(
    indices: pd.DataFrame,
    value_col: str,
    partners: tuple[str, ...],
    output_dir: Path = OUTPUT_PLOTS_DIR,
    *,
    title_prefix: str,
    filename_prefix: str,
) -> list[Path]:
    """One figure per partner; country lines over years."""
    paths: list[Path] = []
    label = value_col.upper()
    for partner in partners:
        subset = indices[indices["partner"] == partner]
        if subset.empty or subset[value_col].isna().all():
            continue
        countries = sorted(subset["country"].unique())
        fig, ax = plt.subplots(figsize=(10, 5))
        for country in countries:
            series = subset[subset["country"] == country].sort_values("year")
            ax.plot(
                series["year"],
                series[value_col],
                marker="o",
                markersize=3.5,
                linewidth=1.8,
                label=country,
            )
        ax.set_xlabel("Year")
        ax.set_ylabel(label)
        ax.set_title(f"{title_prefix} — {PARTNER_DISPLAY.get(partner, partner)}")
        ax.grid(True, alpha=0.3)
        ax.legend(loc="best", fontsize=8, ncol=2)
        fig.tight_layout()
        paths.append(
            _save_figure(fig, output_dir, f"{filename_prefix}_{partner}.png")
        )
    return paths


def plot_sti_comtrade_vs_imf_timeseries(
    sti_comtrade: pd.DataFrame,
    sti_imf: pd.DataFrame,
    output_dir: Path = OUTPUT_PLOTS_DIR,
) -> Path:
    """Overlay Comtrade and IMF STI over time for shared partners."""
    partners = COMTRADE_BILATERAL_PARTNERS
    shared_countries = sorted(
        set(sti_comtrade["country"].unique()) & set(sti_imf["country"].unique())
    )
    if not shared_countries:
        fig, ax = plt.subplots(figsize=(8, 3))
        ax.text(0.5, 0.5, "No overlapping countries", ha="center", va="center")
        ax.axis("off")
        return _save_figure(fig, output_dir, "timeseries_sti_comtrade_vs_imf.png")

    n_rows = len(shared_countries)
    fig, axes = plt.subplots(
        n_rows,
        1,
        figsize=(11, max(2.4 * n_rows, 4)),
        sharex=True,
        squeeze=False,
    )
    for ax, country in zip(axes[:, 0], shared_countries):
        ct = sti_comtrade[sti_comtrade["country"] == country]
        imf = sti_imf[sti_imf["country"] == country]
        _plot_partner_lines(
            ax,
            ct,
            "sti",
            partners,
            linestyle=SOURCE_LINESTYLES[SOURCE_COMTRADE],
            label_suffix=f" ({SOURCE_DISPLAY[SOURCE_COMTRADE]})",
        )
        _plot_partner_lines(
            ax,
            imf,
            "sti",
            partners,
            linestyle=SOURCE_LINESTYLES[SOURCE_IMF],
            label_suffix=f" ({SOURCE_DISPLAY[SOURCE_IMF]})",
        )
        ax.set_ylabel("STI")
        ax.set_title(country)
        ax.grid(True, alpha=0.3)
        ax.legend(loc="best", fontsize=7, ncol=2)

    axes[-1, 0].set_xlabel("Year")
    fig.suptitle("STI over time: Comtrade vs IMF", y=1.01, fontsize=12)
    fig.tight_layout()
    return _save_figure(fig, output_dir, "timeseries_sti_comtrade_vs_imf.png")


def generate_all_plots(
    indices_comtrade: pd.DataFrame,
    sti_imf: pd.DataFrame,
    output_dir: Path = OUTPUT_PLOTS_DIR,
) -> list[Path]:
    """Write time-series figures for Comtrade indices and IMF STI."""
    paths: list[Path] = []

    if not indices_comtrade.empty:
        sti_ct = indices_comtrade[["country", "year", "partner", "sti"]].dropna(
            subset=["sti"]
        )
        paths.append(
            plot_index_timeseries_by_country(
                sti_ct,
                "sti",
                COMTRADE_BILATERAL_PARTNERS,
                output_dir,
                title="STI over time (Comtrade)",
                filename="timeseries_sti_comtrade.png",
            )
        )
        paths.extend(
            plot_index_timeseries_by_partner(
                sti_ct,
                "sti",
                COMTRADE_BILATERAL_PARTNERS,
                output_dir,
                title_prefix="STI over time (Comtrade)",
                filename_prefix="timeseries_sti_comtrade_by_partner",
            )
        )

        if "cwti" in indices_comtrade.columns:
            cwti = indices_comtrade[["country", "year", "partner", "cwti"]].dropna(
                subset=["cwti"]
            )
            if not cwti.empty:
                paths.append(
                    plot_index_timeseries_by_country(
                        cwti,
                        "cwti",
                        COMTRADE_BILATERAL_PARTNERS,
                        output_dir,
                        title="CWTI over time (Comtrade)",
                        filename="timeseries_cwti_comtrade.png",
                    )
                )
                paths.extend(
                    plot_index_timeseries_by_partner(
                        cwti,
                        "cwti",
                        COMTRADE_BILATERAL_PARTNERS,
                        output_dir,
                        title_prefix="CWTI over time (Comtrade)",
                        filename_prefix="timeseries_cwti_comtrade_by_partner",
                    )
                )

    if not sti_imf.empty:
        paths.append(
            plot_index_timeseries_by_country(
                sti_imf,
                "sti",
                IMF_BILATERAL_PARTNERS,
                output_dir,
                title="STI over time (IMF)",
                filename="timeseries_sti_imf.png",
            )
        )
        paths.extend(
            plot_index_timeseries_by_partner(
                sti_imf,
                "sti",
                IMF_BILATERAL_PARTNERS,
                output_dir,
                title_prefix="STI over time (IMF)",
                filename_prefix="timeseries_sti_imf_by_partner",
            )
        )

    if not indices_comtrade.empty and not sti_imf.empty:
        sti_ct = indices_comtrade[["country", "year", "partner", "sti"]].dropna(
            subset=["sti"]
        )
        paths.append(
            plot_sti_comtrade_vs_imf_timeseries(sti_ct, sti_imf, output_dir)
        )

    return paths
